import time

from influxdb_client import InfluxDBClient
from influxdb_client.client.write_api import SYNCHRONOUS,Point
from flask import Flask, request, jsonify
from baseFunc.baseLogger import Log
from baseFunc.util import getconfig

app = Flask(__name__)

@app.route('/Data', methods=['POST'])
def nt_measure_data():
    try:
        # 读取POST请求中的数据
        data = request.get_json()
        print(f"收到NTMeasureData请求中的data类型：{type(data)},data内容: {data}")
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

if __name__ == '__main__':

    ip = getconfig('ip')
    port = getconfig('port')
    token = getconfig('token')
    org = getconfig('org')
    bucket = getconfig('bucket')
    app.run(host='0.0.0.0', port=5000,debug=True)
