import socket
import time
from baseFunc.baseLogger import Log
from connect.connect_influx import w_influx, InfluxClient

class TCPInflux:
    def __init__(self, codeResult, data_address):
        try:
            self.break_ok = 0
            self.codeResult = codeResult
            self.data_address = data_address
            self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            # 连接到服务器
            self.s.connect((self.data_address['ip'], self.data_address['port']))
            print(
                f"链接TCP服务器成功,self.data_address['ip']:{self.data_address['ip']},self.data_address['port']:{self.data_address['port']}")
            Log().printInfo(
                f"链接TCP服务器成功,self.data_address['ip']:{self.data_address['ip']},self.data_address['port']:{self.data_address['port']}")
            self.influxdb_client = InfluxClient().connect()
            self.break_ok = 1
        except Exception as e:
            print(f"TCPInflux初始化报错: {e}")
            Log().printError(f"TCPInflux初始化报错: {e}")
            self.break_ok = 0

    def tcp_influx(self):

        while True:

            try:
                if self.break_ok == 0:
                    self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    self.s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                    # 连接到服务器
                    self.s.connect((self.data_address['ip'], self.data_address['port']))
                    print(
                        f"链接TCP服务器成功,self.data_address['ip']:{self.data_address['ip']},self.data_address['port']:{self.data_address['port']}")
                    Log().printInfo(
                        f"链接TCP服务器成功,self.data_address['ip']:{self.data_address['ip']},self.data_address['port']:{self.data_address['port']}")
                    self.influxdb_client = InfluxClient().connect()
                    self.break_ok = 1

                # 接收数据（这里假设服务器会立即发送数据，或者我们发送一些请求后服务器响应）
                # 注意：recv()方法需要指定要接收的字节数，这里使用1024作为示例
                data = self.s.recv(1024)

                if data:
                    # 打印接收到的数据
                    # print("Received:", data.decode())
                    # print("self.data_address:", self.data_address)
                    Log().print(f"{self.data_address}收到条码: {data.decode()}")
                    for k, v in self.data_address['device_a_tags'].items():
                        if data.decode() == "NG" or data.decode() == "testdata":
                            influx_data = {self.data_address["en_name"]: "NG" + str(time.time())}
                        else:
                            influx_data = {self.data_address["en_name"]: data.decode()}
                        # 将influx存储数据组织成对应的package存储格式
                        package = \
                            {
                                "measurement": v,
                                "tags":
                                    {
                                        "device_a_tag": v,
                                        "device_name": k,
                                        "kafka_position": 'codeResult',
                                        "cn_name": '条码'
                                    },
                                "fields": influx_data
                            }
                        json_body = [package]
                        w_influx(self.influxdb_client, k, json_body)

                else:
                    print("No data received from the server.")

            except Exception as e:
                print(f"读取整理数据保持: {e}")
                Log().printError(f"读取整理数据保持: {e}")
                time.sleep(5)
                self.break_ok = 0
