from flask import Flask, request, jsonify
from utils.baseLogger import Log
import glob
import os
import requests
import json  # 导入json模块以解析JSON数据

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
        files = glob.glob(os.path.join(folder, '*.xlsx'))
        if not files:
            return None
        # 获取文件的修改时间并排序
        latest_file = max(files, key=os.path.getmtime)
        return latest_file

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

        # 定义第一个URL
        url = 'https://limsuat.midea.com/LIMS-Server/MPLM_Service_Gateway/TokenGenerator/getToken'
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

        # 定义第二个URL
        url = 'https://limsuat.midea.com/LIMS-Server/MPLM_Service_Gateway/raclimsRestfulController/upLoadFileAndData'
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
            print(json_array)
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
        print(f"body:{body}")
        response = requests.post(url, headers=headers, json=body)  # 注意使用json参数发送JSON数据

        # 打印响应状态码和响应内容
        print("Response Status Code:", response.status_code)
        print("Response Content:", response.text)

        # 准备返回结果
        response = self._prepare_response(200, success, data, message)
        return jsonify(response)

    def _prepare_response(self, code, success, data, msg):
        return {
            "code": code,
            "success": success,
            "data": data,
            "msg": msg
        }
