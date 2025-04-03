import socket
import pandas as pd
import os
import time
import datetime
import struct

class TCPClientTest:
    def __init__(self, data_addresses):
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_ip = data_addresses['source_ip']
        self.server_port = data_addresses['source_port']
        self.device_a_tag = data_addresses["device_a_tag"]
        self.data_file = None  # 初始化时不指定文件，将在需要时创建
        # self.df = pd.DataFrame(columns=['测试结果'])  # 简化列名
        self.message_count = 0  # 接收到的消息计数

    def connect(self):
        try:
            self.client_socket.connect((self.server_ip, self.server_port))
            print(f"已连接到服务器 {self.server_ip}:{self.server_port}")
            return True
        except Exception as e:
            print(f"连接服务器失败: {e}")
            return False

    def send_data(self, data):
        try:
            self.client_socket.send(data)
            return True
        except Exception as e:
            print(f"发送数据失败: {e}")
            return False

    def receive_data(self, buffer_size=1024):
        try:
            data = self.client_socket.recv(buffer_size)
            return data
        except Exception as e:
            print(f"接收数据失败: {e}")
            return None

    def close(self):
        if self.client_socket:
            self.client_socket.close()
            print("连接已关闭")
    def start(self):
        if self.connect():
            while True:
                self.send_data(b"Hello, Server!")
                response = self.receive_data()
                print(f"收到服务器响应: {response}")
                time.sleep(1)

if __name__ == "__main__":
    config = {
        "server_ip": "127.0.0.1",
        "server_port": 8889,
        "device_a_tag": "test"
    }
    client = TCPClientTest(config)
    client.connect()
    while True:
        client.send_data(b"Hello, Server!")
        response = client.receive_data()
        print(f"收到服务器响应: {response}")
        time.sleep(1)

