from baseFunc.baseLogger import Log
from connect.connect_plc import PLCClient
from datetime import datetime
import time


def write_to_plc(data):
    client = PLCClient('192.168.3.38', 3001, '127.0.0.1:19092')
    try:
        write_result = client.write_plc(data)
        print(f"{data_put}写入结果write_result:{write_result}")
        Log().printInfo(f"write to plc success,write_result:{write_result}")
        return write_result
    except Exception as e:
        print(f"写入报错：{e}")
        Log().printError("write to plc failed!")
        Log().printError(e)
        return f"写入报错：{e}"


data_put = {
            "润滑电机启动": {
                "addr": "M900",
                "value": 1,
                "type": "bool",
                'num': 1
            }
        }
write_result = write_to_plc(data_put)
print(f"时间到")
time.sleep(20)
data_put = {
    "润滑电机启动": {
        "addr": "M900",
        "value": 0,
        "type": "bool",
        'num': 1
    }
}
write_result = write_to_plc(data_put)
