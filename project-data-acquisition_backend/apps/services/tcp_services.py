import socket
import pandas as pd
import os
import time
import datetime
import struct
from utils.baseLogger import Log

class TCPServer:
    def __init__(self, data_addresses):
        self.client_socket = None
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.host = data_addresses['source_ip']
        self.port = data_addresses['source_port']
        self.device_a_tag = data_addresses["device_a_tag"]
        self.data_file = None  # 初始化时不指定文件，将在需要时创建
        # self.df = pd.DataFrame(columns=['测试结果'])  # 简化列名
        self.message_count = 0  # 接收到的消息计数

    def modbus_crc(self, data):
        """
        计算Modbus CRC校验值。

        :param data: 待计算CRC的字节序列
        :return: CRC校验值（16位整数）
        """
        crc = 0xFFFF
        for byte in data:
            crc ^= byte
            for _ in range(8):
                if crc & 0x0001:
                    crc >>= 1
                    crc ^= 0xA001
                else:
                    crc >>= 1
        return crc
    def create_modbus_read_request(self, slave_id, function_code, start_address, quantity):
        """
        创建一个Modbus RTU读取数据请求的字节序列。

        :param slave_id: 从站地址（0-247）
        :param function_code: 功能码（3或4，分别代表读保持寄存器和读输入寄存器）
        :param start_address: 起始地址（16位整数）
        :param quantity: 寄存器个数（16位整数）
        :return: Modbus RTU读取数据请求的字节序列
        """
        # 构建请求报文：从站地址 + 功能码 + 起始地址（两个字节）+ 寄存器个数（两个字节）
        request = struct.pack('>BBHH', slave_id, function_code, start_address, quantity)

        # 计算CRC校验值
        crc = self.modbus_crc(request)

        # 将CRC添加到请求报文中
        request += struct.pack('>H', crc)

        return request

    def parse_modbus_rtu_response(self, response):
        """
        解析Modbus RTU响应报文，提取数据。

        :param response: Modbus RTU响应报文（字节序列）
        :return: 一个字典，包含从站地址、功能码和读取到的数据
        """
        # 检查响应长度是否至少为7字节（最小有效长度）
        if len(response) < 7:
            raise ValueError("响应太短，无法解析")

        # 解析从站地址和功能码
        slave_id = response[0]
        function_code = response[1]

        # 根据功能码判断数据格式
        if function_code == 3 or function_code == 4:  # 读保持寄存器或读输入寄存器
            # 跳过前两个字节（从站地址和功能码），然后是字节数字节
            data_length = response[2]
            # 紧接着是实际数据，根据字节数字节确定数据长度
            data_start = 3
            data_end = data_start + data_length
            data = response[data_start:data_end]

            # 如果数据长度是偶数，表示每个寄存器占用两个字节，需要转换为整数
            if data_length % 2 == 0:
                # 将字节序列转换为整数列表
                values = []
                for i in range(0, data_length, 2):
                    value = struct.unpack('>H', data[i:i + 2])[0]
                    values.append(value)
                return {'slave_id': slave_id, 'function_code': function_code, 'data': values}
            else:
                # 如果数据长度不是偶数，可能有错误或非标准实现
                raise ValueError("数据长度不是偶数，无法正确解析")
        else:
            # 其他功能码可能有不同的解析方式
            raise ValueError("不支持的功能码")

    def hex_to_bytes(self, hex_string):
        """将十六进制字符串转换为字节"""
        bytes_object = bytes.fromhex(hex_string.replace(" ", ""))
        return bytes_object

    def bytes_to_hex(self, byte_data):
        """将字节转换为十六进制字符串"""
        hex_string = " ".join(f"{byte:02X}" for byte in byte_data)
        return hex_string

    def save_file_and_reset(self, addr,order_number,column_name,data_excel,groupName):

        file_name = f"{order_number}.xlsx"

        if self.device_a_tag == "A0502050004140088":
            file_path = f'/code/EQ00003366/{file_name}'
            # self.df = pd.DataFrame(columns=['检测结果'])  # 清空DataFrame以便下次接收消息
            self.message_count = 0  # 重置消息计数
        else:
            # file_name = f"继电器综合测试仪检测报告_{formatted_time}.xlsx"
            file_path = f'/code/EQ00003365/{file_name}'
        # 确保目录存在
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        # print(f"data_excel:{data_excel}")
        # print(f"column_name:{column_name}")
        new_df = pd.DataFrame(data_excel, columns=column_name)
        try:
            # 尝试打开文件
            existing_df = pd.read_excel(file_path)
            print("文件已存在并成功读取。")
            # 在这里继续处理 existing_df
        except FileNotFoundError:
            print(f"文件 {file_path} 不存在，将创建一个新的 Excel 文件。")
            # 创建一个空的 DataFrame
            existing_df = pd.DataFrame()
        except Exception as e:
            print(f"读取或创建文件时发生错误: {e}")
        # 合并数据框（纵向追加）
        combined_df = pd.concat([existing_df, new_df], ignore_index=True)
        combined_df.to_excel(file_path, index=False)
        # self.df.to_excel(file_path, index=False)
        print(f"文件已保存为：{file_path}")
        # self.df = pd.DataFrame(columns=['检测结果'])  # 清空DataFrame以便下次接收消息

    def start(self, test_item,order_number):
        try:
            # 尝试绑定到指定的主机和端口
            self.server_socket.bind((self.host, self.port))
            print(f"Server is listening on {self.host}:{self.port}")
            # 继续服务器的启动流程...
            self.server_socket.listen(5)
            print(f"{self.host}{self.port}TCP服务器正在运行，等待客户端连接...")
            self.client_socket, addr = self.server_socket.accept()
            print(f"已连接到客户端：{addr}")

        except OSError as e:
            if e.errno == 98:  # 检查错误号是否为98（地址已在使用）
                print(f"{self.host}{self.port}客户端已连接.")
                self.client_socket, addr = self.server_socket.accept()
                print(f"已连接到客户端：{addr}")
            else:
                raise e  # 如果是其他类型的OSError，重新抛出异常

        groupName = test_item[0]["testFieldDictionaryGroups"][0]["groupName"]
        if self.port == 8899:
            data = self.client_socket.recv(1024).decode().strip()

            for a in test_item:
                for b in a["testFieldDictionaryGroups"]:
                    for c in b["testFieldDictionarys"]:
                        if c["attributeDisplayName"] == "电感量":
                            attributeDisplayName = c["attributeDisplayName"]
                            paraUnit = c["paraUnit"]
                            if paraUnit == "uH" or paraUnit == "µH":
                                data2 = float(data[0:12])
                            elif paraUnit == "mH":
                                data2 = float(data[0:12]) / 100
                            else:
                                data2 = float(data[0:12]) / 1000
                            column_name = ["测试时间", "实验阶段", f"{attributeDisplayName}（{paraUnit}）", "Q值"]
                            # 获取当前时间
                            now = datetime.datetime.now()
                            # 给当前时间加上8小时
                            future_time = now
                            # 将时间格式化为字符串
                            formatted_time = future_time.strftime("%Y/%m/%d %H:%M:%S")

                            data_excel = [[formatted_time, groupName, data2, float(data[13:25])]]

                            print(f"从客户端 {addr} 接收的数据: {data}")
                            Log().printInfo(f"从客户端 {addr} 接收的数据: {data}")

                            self.save_file_and_reset(addr, order_number, column_name, data_excel, groupName)
                            self.client_socket.close()
                            self.server_socket.close()  # 确保服务器套接字被关闭
                            print(f"接收到1条消息，关闭{self.host}{self.port}服务器...")

                        if c["attributeDisplayName"] == "电容量":
                            attributeDisplayName = c["attributeDisplayName"]
                            paraUnit = c["paraUnit"]
                            if paraUnit == "µF" or paraUnit == "uF":
                                print(f"data[0:12]:{data[0:12]}")
                                print(f"float(data[0:12]):{float(data[0:12])}")
                                print(f"data[13:25]:{data[13:25]}")
                                print(f"float(data[13:25]):{float(data[13:25])}")
                                data2 = float(data[0:12]) * 1000000
                                data3 = float(data[13:25])

                            elif paraUnit == "mF":
                                data2 = float(data[0:12]) * 1000
                                data3 = float(data[13:25])

                            else:
                                data2 = float(data[0:12])
                                data3 = float(data[13:25])

                            column_name = ["测试时间", "实验阶段", f"{attributeDisplayName}（{paraUnit}）",
                                           f"损耗角"]
                            # 获取当前时间
                            now = datetime.datetime.now()
                            # 给当前时间加上8小时
                            future_time = now
                            # 将时间格式化为字符串
                            formatted_time = future_time.strftime("%Y/%m/%d %H:%M:%S")

                            data_excel = [[formatted_time, groupName, data2, data3]]

                            print(f"从客户端 {addr} 接收的数据: {data}")
                            Log().printInfo(f"从客户端 {addr} 接收的数据: {data}")

                            self.save_file_and_reset(addr, order_number, column_name, data_excel, groupName)
                            self.client_socket.close()
                            self.server_socket.close()  # 确保服务器套接字被关闭
                            print(f"接收到1条消息，关闭{self.host}{self.port}服务器...")
        else:
            # 要发送的数据
            slave_address = 12
            function_code = 3  # 读取保持寄存器
            start_address = 500
            quantity_of_registers = 19
            request = self.create_modbus_read_request(slave_address, function_code, start_address, quantity_of_registers)
            print("自动生成的读modbusRTU报文请求:", request)
            # 获取CRC高位和低位字节
            crc_high = request[-2]
            crc_low = request[-1]
            # 创建一个新的字节序列，其中CRC位置被交换
            new_request = request[:-2] + bytes([crc_low, crc_high])
            print("修改后的读modbusRTU报文请求:", new_request)
            send_data = new_request
            # 发送数据到客户端
            self.client_socket.sendall(send_data)

            # 接收来自客户端的数据
            buffer_size = 1024  # 缓冲区大小
            data_bytes = self.client_socket.recv(buffer_size)
            print(f"从客户端 {addr} 接收的数据: {self.bytes_to_hex(data_bytes)}")
            parsed_response = self.parse_modbus_rtu_response(data_bytes)
            print(f"解析后的数据{parsed_response}")

            column_name = ["测试时间","实验阶段","线圈电阻Ω","动作电压V","释放电压V","吸合时间ms","释放时间ms"]

            # 获取当前时间
            now = datetime.datetime.now()
            # 给当前时间加上8小时
            future_time = now
            # 将时间格式化为字符串
            formatted_time = future_time.strftime("%Y/%m/%d %H:%M:%S")

            data1 = parsed_response['data'][0] * 0.1
            if parsed_response['data'][6] * 0.01 == 655.32:
                data2 = "PASS"
            else:
                data2 = parsed_response['data'][6] * 0.01
            if parsed_response['data'][9] * 0.01 == 655.32:
                data3 = "PASS"
            else:
                data3 = parsed_response['data'][9] * 0.01
            data4 = parsed_response['data'][7] * 0.01
            data5 = parsed_response['data'][10] * 0.01
            data_excel = [[formatted_time,groupName,data1,data2,data3,data4,data5]]

            '''
            new_row = pd.DataFrame([f"线圈电阻测量值（欧）：{parsed_response['data'][0] * 0.1}"])
            self.df = pd.concat([self.df, new_row], ignore_index=True)
            print(f"线圈电阻测量值（欧）：{parsed_response['data'][0] * 0.1}")
            new_row = pd.DataFrame([f"吸合电压测量值（V）：{parsed_response['data'][6] * 0.01}"])
            if parsed_response['data'][6] * 0.01 == 655.32:
                new_row = pd.DataFrame([f"吸合电压测量值（V）：PASS"])
            self.df = pd.concat([self.df, new_row], ignore_index=True)
            print(f"吸合电压测量值（V）：{parsed_response['data'][6] * 0.01}")
            new_row = pd.DataFrame([f"吸合时间测量值（ms）：{parsed_response['data'][7] * 0.01}"])
            self.df = pd.concat([self.df, new_row], ignore_index=True)
            print(f"吸合时间测量值（ms）：{parsed_response['data'][7] * 0.01}")
            new_row = pd.DataFrame([f"释放电压测量值（V）：{parsed_response['data'][9] * 0.01}"])
            self.df = pd.concat([self.df, new_row], ignore_index=True)
            print(f"释放电压测量值（V）：{parsed_response['data'][9] * 0.01}")
            new_row = pd.DataFrame([f"释放时间测量值（ms）：{parsed_response['data'][10] * 0.01}"])
            if parsed_response['data'][10] * 0.01 == 655.32:
                new_row = pd.DataFrame([f"吸合电压测量值（V）：PASS"])
            self.df = pd.concat([self.df, new_row], ignore_index=True)
            print(f"释放时间测量值（ms）：{parsed_response['data'][10] * 0.01}")
            '''

            self.save_file_and_reset(addr, order_number, column_name, data_excel, groupName)
            self.client_socket.close()
            self.server_socket.close()  # 确保服务器套接字被关闭


if __name__ == "__main__":
    # 示例数据地址配置
    data_addresses = {
        'source_ip': '127.0.0.1',
        'source_port': 8888,
        'device_a_tag': 'device_a'
    }
    server = TCPServer(data_addresses)
    server.start()