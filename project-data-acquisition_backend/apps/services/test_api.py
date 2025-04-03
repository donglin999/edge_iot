import socket

from flask import Flask, request, jsonify

import time

from utils.baseLogger import Log


class TcpApi:
    def __init__(self, host='0.0.0.0', port=5000, debug=True, data_addresses=""):
        self.app = Flask(__name__)
        self.host = host
        self.port = port
        self.debug = debug
        self.data_addresses = data_addresses

        # 注册路由
        self.app.add_url_rule('/OrderLabel', 'tcp_api', self.tcp_api, methods=['POST'])

    def run(self):
        self.app.run(host=self.host, port=self.port, debug=self.debug)

    def tcp_api(self):
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

        # 准备返回结果
        response = self._prepare_response(200, success, data, message)
        return jsonify(response)
        try:
            pass

        except Exception as e:
            Log().printError(e)
            print(f"数据整理报错{e}")
            return jsonify({"error": str(e)})

    def _prepare_response(self, code, success, data, msg):
        return {
            "code": code,
            "success": success,
            "data": data,
            "msg": msg
        }

if __name__ == '__main__':
    app = TcpApi(debug=True)
    app.run()