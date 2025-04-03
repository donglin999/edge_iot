#!/usr/bin/env python
# -*- encoding: utf-8 -*-

from baseFunc.util import getconfig
import json
from flask import Flask, request, jsonify
from baseFunc.baseLogger import Log
import requests
from kafka import KafkaProducer
from flask_apscheduler import APScheduler
from datetime import datetime, timedelta, timezone, date, time
from connect.connect_influx import w_influx, InfluxClient
from influxdb_client import InfluxDBClient

app = Flask(__name__)

if __name__ == "__main__":

    device_a_tags = getconfig('device_a_tags')
    industrial_computer_name_cn = getconfig('industrial_computer_name_cn')
    device_name = getconfig('device_name')
    influx_org = getconfig('influx_org')
    influx_bucket = getconfig('influx_bucket')
    influx_ip = getconfig('influx_ip')
    influx_port = getconfig('influx_port')
    influx_token = getconfig('influx_token')
    API_URL = getconfig('API_URL')
    TOKEN = getconfig('TOKEN')
    IMAGE_time = getconfig('IMAGE_time')
    port = getconfig('port')
    KAFKA_BROKER = getconfig('KAFKA_BROKER')
    influxdb_client = InfluxClient().connect()
    query_api = influxdb_client.query_api()
    # influxdb_client2 = InfluxClient().connect2()
    # query_api2 = influxdb_client2.query_api()
    kafka_producer = KafkaProducer(bootstrap_servers=KAFKA_BROKER,
                                   value_serializer=lambda x: json.dumps(x).encode('utf-8'))
    # 初始化并启动APScheduler
    scheduler = APScheduler()
    scheduler.init_app(app)
    scheduler.start()

    # 跟踪最后请求的时间戳
    last_request_time = None

    # 定时任务：检查是否在5秒内没有接收到请求
    @scheduler.task('interval', id='check_request_frequency', seconds=5)
    def check_request_frequency():
        # 假设local_time是一个UTC时间对象
        # 例如，我们可以手动创建一个UTC时间
        utc_time = datetime.now(timezone.utc)
        # 将UTC时间转换为北京时间（UTC+8）
        # 注意：timedelta(hours=8)用于将UTC时间转换为北京时间
        beijing_time = utc_time + timedelta(hours=8)
        # 使用strftime来格式化时间
        formatted_time = beijing_time.strftime("%Y-%m-%d %H:%M:%S")

        global last_request_time
        if last_request_time is None or (datetime.utcnow() - last_request_time).total_seconds() > 5:
            try:
                ac_status_data = {"code": "200", "deviceIP": "10.173.192.70", "message": "5秒内无调用记录",
                                  "serviceCode": "image_kafka", "timestamp": formatted_time}

                kafka_producer.send("ac_status_data", ac_status_data)
                # Log().printInfo(f"kafka消息推送成功，主题：ac_status_data，内容：{ac_status_data}")
                # print(f"5秒内没调用记录，kafka消息推送成功，主题：ac_status_data，内容：{ac_status_data}")

            except Exception as e:
                Log().printError(e)
                print(f"发程序心跳报错{e}")


    @app.route('/upload', methods=['POST'])
    def upload_image():
        # 假设local_time是一个UTC时间对象
        # 例如，我们可以手动创建一个UTC时间
        utc_time = datetime.now(timezone.utc)
        # 将UTC时间转换为北京时间（UTC+8）
        # 注意：timedelta(hours=8)用于将UTC时间转换为北京时间
        beijing_time = utc_time + timedelta(hours=8)
        # 使用strftime来格式化时间
        formatted_time = beijing_time.strftime("%Y-%m-%d %H:%M:%S")

        try:
            ac_status_data = {"code": "200", "deviceIP": "10.173.192.70", "message": "upload ok",
                              "serviceCode": "image_kafka", "timestamp": formatted_time}

            kafka_producer.send("ac_status_data", ac_status_data)

        except Exception as e:
            Log().printError(f"发程序心跳报错{e}")
            print(f"发程序心跳报错{e}")
            return jsonify({'error': f"kafka send:{e}"}), 400

        tag1 = request.form['description_json']
        # Log().printInfo(f"收到请求的内容：{tag1}")
        # print(f"收到请求的内容：{tag1}")
        global last_request_time
        last_request_time = datetime.utcnow()  # 更新最后请求时间

        if 'image' not in request.files:
            Log().printInfo("请求里没有image字段")
            return jsonify({'error': 'image not in request.files.请求里没有image字段'}), 400

        image_file = request.files['image']
        ip = request.remote_addr
        # Log().printInfo(f"收到文件的内容：{request.files}，类型：{type(request.files)}")
        # print(f"收到文件的内容：{request.files}，类型：{type(request.files)}")
        # 确保图片文件有效
        if not image_file:
            Log().printInfo("图片文件无效")
            return jsonify({'error': 'not image_file'}), 400

        # 尝试从表单数据中获取描述JSON字符串
        if 'description_json' not in request.form:
            # Log().printInfo(f"表单数据中无描述JSON字符串{description_json}")
            # print(f"表单数据中无描述JSON字符串description_json")
            return jsonify(
                {'error': 'description_json not in request.form'}), 400

        description_json = request.form['description_json']

        try:
            # 使用json.loads解析描述JSON字符串，更安全且避免eval的潜在风险
            description = json.loads(description_json)
            # print(f"表单数据中描述JSON字符串{description}")
        except json.JSONDecodeError as e:
            Log().printError(f"解析表单数据中描述JSON字符串报错{e}")
            return jsonify(
                {
                    'error': f"json.loads(description_json) is JSONDecodeError:{e}"}), 400

        # 上传图片服务器
        files = {'file': (f"{description['codeResult']}.jpg", image_file, 'image/jpg')}
        # Log().printInfo(f"打开文件的内容：{files}，类型：{type(files)}")
        # 设置请求头，包含token
        headers = {
            'Authorization': f'Bearer {TOKEN}'
        }
        # 发送请求
        response = requests.post(API_URL, files=files, headers=headers)
        response_json = response.json()
        # Log().printInfo(f"{tag1}，图片上传图片服务器返回内容response_json：{response_json}")
        # print(f"{tag1}，图片上传图片服务器返回内容response_json：{response_json}")

        n = 0
        for d in description["detectItems"]:
            filePath = {}
            # print(f"批量上传收到的返回{response_json}")
            filePath["objectKey"] = response_json["data"]["objectKey"]
            filePath["bucketName"] = response_json["data"]["bucketName"]
            description["deviceAddr"] = ip
            description["detectItems"][n]["filePath"] = json.dumps(filePath)
            n = n + 1

        for mea in description["measures"]:
            if mea["measureCode"] == "cl":
                cl = mea["value"]

        device_a_tag = description["deviceAddr"]
        device_name_cn = device_a_tags[device_a_tag]
        # 将influx存储数据组织成对应的package存储格式
        package = \
            {
                "measurement": industrial_computer_name_cn,
                "tags":
                    {
                        "device_a_tag": device_a_tag,
                        "device_name_cn": device_name_cn,
                        "data_type": "measures",
                        "cn_name": "产量"
                    },
                "fields": {"cl": int(cl)}
            }
        json_body = [package]
        w_influx(influxdb_client, device_name_cn, json_body)
        # w_influx(influxdb_client2, device_name_cn, json_body)

        package = \
            {
                "measurement": industrial_computer_name_cn,
                "tags":
                    {
                        "device_a_tag": device_a_tag,
                        "device_name_cn": device_name_cn,
                        "data_type": "codeResult",
                        "cn_name": "条码"
                    },
                "fields": {"codeResult": description["codeResult"]}
            }
        json_body = [package]
        w_influx(influxdb_client, device_name_cn, json_body)
        # w_influx(influxdb_client2, device_name_cn, json_body)

        # 获取今天的日期
        today = date.today()
        # 计算昨天的日期
        yesterday = today - timedelta(days=1)
        # 格式化昨天的日期为字符串（例如：YYYY-MM-DD）
        yesterday_str = yesterday.strftime('%Y-%m-%d')
        today_str = today.strftime('%Y-%m-%d')

        def is_within_time_range(start_time, end_time):
            # 获取当前时间
            now = datetime.now().time()
            # 判断当前时间是否在指定范围内
            return start_time <= now <= end_time

        # 定义时间范围
        start_time = time(0, 0)
        end_time = time(7, 30)
        # 判断当前时间是否在范围内
        if is_within_time_range(start_time, end_time):
            # print("当前时间在0:0到7:30之间")
            # Log().printInfo(f"当前时间在0:0到7:30之间")
            stop_time = yesterday_str + "T11:30:00Z"
        # 定义时间范围
        start_time = time(7, 30)
        end_time = time(19, 30)
        # 判断当前时间是否在范围内
        if is_within_time_range(start_time, end_time):
            # print("当前时间在7:30到19:30之间")
            # Log().printInfo(f"当前时间在7:30到19:30之间")
            stop_time = yesterday_str + "T23:30:00Z"
        # 定义时间范围
        start_time = time(19, 30)
        end_time = time(23, 59, 59)
        # 判断当前时间是否在范围内
        if is_within_time_range(start_time, end_time):
            # print("当前时间在19:30到23:50:59之间")
            Log().printInfo(f"当前时间在19:30到23:50:59之间")
            stop_time = today_str + "T11:30:00Z"

        # 算产量
        try:

            query = f'from(bucket: "{influx_bucket}") ' \
                    f'|> range(start: {stop_time}, stop: -1s) ' \
                    f'|> filter(fn: (r) => r["device_a_tag"] == "{device_a_tag}") ' \
                    f'|> filter(fn: (r) => r["_field"] == "cl") ' \
                    f'|> limit(n: 1)'

            tables = query_api.query(query)
            for table in tables:
                for record in table.records:
                    cl_start = record.get_value()

            query = f'from(bucket: "{influx_bucket}") ' \
                    f'|> range(start: {stop_time}, stop: -1s) ' \
                    f'|> filter(fn: (r) => r["device_a_tag"] == "{device_a_tag}") ' \
                    f'|> filter(fn: (r) => r["_field"] == "cl") ' \
                    f'|> last()'

            tables = query_api.query(query)
            for table in tables:
                for record in table.records:
                    cl_now = record.get_value()
            cl = cl_now - cl_start

            record_dic = {"measureCode": "cl",
                          "status": 1,
                          "value": str(cl)
                          }
            description["measures"].append(record_dic)
        except Exception as e:
            Log().printError(f"{device_a_tag}，{query}查时序数据库产量标记算当日产量数据报错：{e}")
            print(f"{device_a_tag}，{query}查时序数据库累计产量算当日产量数据报错：{e}")

        # 计算扫描识别率
        try:
            query = f'from(bucket: "{influx_bucket}") ' \
                    f'|> range(start: {stop_time}, stop: -1s) ' \
                    f'|> filter(fn: (r) => r["device_a_tag"] == "{device_a_tag}") ' \
                    f'|> filter(fn: (r) => r["_field"] == "codeResult") '
            codeResult = []
            tables = query_api.query(query)
            for table in tables:
                for record in table.records:
                    if "E" in record.get_value():
                        codeResult.append(record.get_value())
            codeResult_set = set(codeResult)
            codeResult_set_len = len(codeResult_set)
            recognition_rate = codeResult_set_len / cl
            record_dic = {"measureCode": "codeResult_set_len",
                          "status": 1,
                          "value": str(codeResult_set_len)
                          }
            description["measures"].append(record_dic)
            record_dic = {"measureCode": "ScanSuccessRate",
                          "status": 1,
                          "value": str(recognition_rate)
                          }
            description["measures"].append(record_dic)

        except Exception as e:
            Log().printError(f"{device_a_tag}，{query}查时序数据库条码算识别率报错：{e}")
            print(f"{device_a_tag}，{query}查时序数据库条码算识别率数据报错：{e}")

        try:
            kafka_producer.send("qm_data", description)
            # Log().printInfo(f"kafka发送完成,description:{description}")
            success = True
            msg = f"{device_a_tag} send kafka OK"
        except Exception as e:
            Log().printError(f"{device_a_tag}发送数据到kafka报错：{e}")
            print(f"{device_a_tag}发送数据到kafka报错：{e}")
            success = False
            msg = f"{device_a_tag} send kafka error：{e}"

        return jsonify({'success': success, 'image_path': response_json["data"]["fileUrl"], 'msg': msg}), 201

    app.run(host='0.0.0.0', port=port)
