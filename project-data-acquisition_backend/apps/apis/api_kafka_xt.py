
import json
from flask import Flask, request, jsonify
from kafka import KafkaProducer
from settings import DevelopmentConfig
from utils.baseLogger import Log

class Api_Kafka:
    def __init__(self, host='0.0.0.0', port=5000, debug=True):
        self.app = Flask(__name__)
        self.host = host
        self.port = port
        self.debug = debug
        self.KAFKA_BROKER = DevelopmentConfig.kafka_bootstrap_servers
        self.TOPIC = DevelopmentConfig.kafka_topic
        self.kafka_producer = KafkaProducer(bootstrap_servers=self.KAFKA_BROKER,
                                       value_serializer=lambda x: json.dumps(x).encode('utf-8'))
        Log().printInfo(f"kafka生产者创建成功，服务器：{self.KAFKA_BROKER}")

        # 注册路由
        self.app.add_url_rule('/Data', 'nt_measure_data', self.nt_measure_data, methods=['POST'])
        # self.app.add_url_rule('/SaveFile', 'save_files_api', self.save_files_api, methods=['POST'])  # 新增的路由

    def run(self):
        self.app.run(host=self.host, port=self.port, debug=self.debug)

    def nt_measure_data(self):
        try:
            # 读取POST请求中的数据
            data = request.get_json()
            # print(f"收到NTMeasureData请求中的data类型：{type(data)},data内容: {data}")
            Log().printInfo(f"收到NTMeasureData请求中的data类型：{type(data)},data内容: {data}")
            # 检查输入数据是否有效（这里只是简单示例，实际中需要更复杂的验证）
            if not data or not isinstance(data, dict):
                success = False
                message = "请求输入数据不是json字典结构"
                Log().printError(f"请求输入数据不是json字典结构：{data}")

            else:
                # 假设处理总是成功的
                success = True
                message = "操作成功"

                future = self.kafka_producer.send(self.TOPIC, data)
                Log().printInfo(f"{data}，kafka消息发送成功，TOPIC：{self.TOPIC}，description：{data}")
                # 如果需要，你可以等待消息发送完成并处理结果
                result = future.get(timeout=60)
                Log().printInfo(f"Message sent to {self.TOPIC} at offset {result.offset}")

                # 准备返回结果
            response = {
                "code": 200,
                "success": success,
                "data": True,  # 这里假设data始终为True，根据实际需求可能需要修改
                "msg": message
            }

            # 返回JSON响应
            return jsonify(response)
        except Exception as e:
            Log().printError(e)
            print(f"数据整理报错{e}")
            return jsonify(e)
            raise

if __name__ == "__main__":
    debug = False
    app = Api_Kafka(debug=debug)
    app.run()