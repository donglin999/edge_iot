import glob
import json
import os
import requests
from flask import Flask, request, jsonify, send_from_directory
from modbus_tk import modbus_tcp

from apps.services.tcp_services import TCPServer
from utils.baseLogger import Log

class Api:
    def __init__(self, host='0.0.0.0', port=5000, debug=True):
        self.server8899 = None
        self.app = Flask(__name__)
        self.host = host
        self.port = port
        self.debug = debug
        self.data_addresses8898 = {'source_ip': '0.0.0.0', 'source_port': 8898, 'device_a_tag': 'A2202020122210041'}
        self.server8898 = None
        self.data_addresses8899 = {'source_ip': '0.0.0.0', 'source_port': 8899, 'device_a_tag': 'A0502050004140088'}

        # 注册路由
        self.app.add_url_rule('/OrderLabel', 'order_label_api', self.order_label_api, methods=['POST'])
        self.app.add_url_rule('/SaveFile', 'save_files_api', self.save_files_api, methods=['POST'])  # 新增的路由

    def run(self):
        self.app.run(host=self.host, port=self.port, debug=self.debug)

    # 获取最新文件的函数
    def file_to_byte_array(self, file_path):
        """
        将文件内容读取为字节数组。

        :param file_path: 文件路径
        :return: 字节数组
        """
        with open(file_path, 'rb') as file:
            byte_array = bytearray(file.read())
        return byte_array

    def byte_array_to_json_array(self, byte_array):
        """
        将字节数组转换为 JSON 数组。

        :param byte_array: 字节数组
        :return: JSON 数组字符串
        """
        json_array = json.dumps(list(byte_array))
        return json_array

    # 获取最新文件的函数
    def get_latest_file(self, folder):
        # 获取文件夹中的所有Excel文件（假设文件扩展名为.xlsx）
        files = glob.glob(os.path.join(folder, '*'))
        if not files:
            return None
        # 获取文件的修改时间并排序
        latest_file = max(files, key=os.path.getmtime)
        return latest_file

    def order_label_api(self):  # 假设这是您原本想要定义的 tcp_api 方法
        # 读取POST请求中的数据
        data = request.get_json()
        print(f"收到请求中的data类型：{type(data)},data内容: {data}")
        Log().printInfo(f"收到请求中的data类型：{type(data)},data内容: {data}")

        # 检查输入数据是否有效（这里只是简单示例，实际中需要更复杂的验证）
        if not data or not isinstance(data, dict):
            success = False
            message = "请求输入数据不是json字典结构"
            Log().printError(f"请求输入数据不是json字典结构：{data}")
            response = self._prepare_response(200, success, data, message)
            return jsonify(response)

        # 假设处理总是成功的
        success = True
        message = "reading the serial port data ok"

        # 定义第一个URL
        url = 'https://lims.midea.com/LIMS-Server/MPLM_Service_Gateway/TokenGenerator/getToken'
        # 定义要发送的数据
        headers = {
            "__TokenAuthorization_UserName_": data["test_item"][0]["testerName"],
            "__TokenAuthorization_Function_": "upLoadFileAndData"
        }  # 设置请求头
        response = requests.post(url, headers=headers)

        # 打印响应状态码和响应内容
        print("Response Status Code:", response.status_code)
        print("Response Content:", response.text)

        # 解析JSON响应并提取token
        try:
            json_response = json.loads(response.text)  # 将响应文本转换为JSON对象
            token = json_response["token"]  # 从JSON对象中提取token
        except json.JSONDecodeError:
            print("Error decoding JSON response")
            token = None  # 如果JSON解析失败，设置token为None

        if data['test_item'][0]["equipment"] == "EQ00003366":
            self.server8899 = TCPServer(self.data_addresses8899)
            self.server8899.start(data['test_item'],data["order_number"])

        if data['test_item'][0]["equipment"] == "EQ00003365":
            self.server8898 = TCPServer(self.data_addresses8898)
            self.server8898.start(data['test_item'],data["order_number"])

        # 定义第二个URL
        url = 'https://lims.midea.com/LIMS-Server/MPLM_Service_Gateway/raclimsRestfulController/upLoadFileAndData'
        # 定义要发送的数据
        headers = {
            "__TokenAuthorization_UserName_": data["test_item"][0]["testerName"],
            "__TokenAuthorization_Function_": "upLoadFileAndData",
            "__TokenAuthorization_UID_": token  # 使用提取的token
        }  # 设置请求头
        # 定义文件夹路径
        folder_path = data["test_item"][0]["equipment"]
        latest_file = self.get_latest_file(folder_path)
        if latest_file:
            file_name = os.path.basename(latest_file)
            byte_array = self.file_to_byte_array(latest_file)
            json_array = self.byte_array_to_json_array(byte_array)
            # print(json_array)
            print(f"找到最新报告：{file_name}")
            Log().printInfo(f"找到最新报告：{file_name}")
        else:
            success = False
            message = "No test results"
            Log().printError(f"No test results")
            response = self._prepare_response(200, success, data, message)
            return jsonify(response)

        body = {"testFormItemNumber": data["test_item"][0]["testFormItemNumber"],
                "ReportName": file_name,
                "ReportInfo": json_array,
                "ReportParam": []}
        # print(f"body:{body}")
        response = requests.post(url, headers=headers, json=body)  # 注意使用json参数发送JSON数据

        # 打印响应状态码和响应内容
        print("Response Status Code:", response.status_code)
        print("Response Content:", response.text)
        Log().printInfo(f"报告：{file_name}发送成功")
        print(f"报告：{file_name}发送成功")

        # 准备返回结果
        response = self._prepare_response(200, success, data, message)
        return jsonify(response)

    def save_files_api(self):  # 新增的接口处理函数
        file = request.files['file']
        print(f"{request.form['equipment']}")
        filename = file.filename
        filepath = request.form['equipment']
        if not os.path.exists(filepath):
            os.makedirs(filepath)
        file.save(os.path.join(filepath, filename))
        return jsonify({'message': 'File successfully uploaded', 'filename': filename}), 201

    def _prepare_response(self, code, success, data, msg):
        return {
            "code": code,
            "success": success,
            "data": data,
            "msg": msg
        }

