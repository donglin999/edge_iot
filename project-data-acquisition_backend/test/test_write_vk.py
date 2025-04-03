import socket
import struct
import time
import random


# 模拟数据包的函数
def create_mock_data_packet():
    # 创建一个1032字节的数据包，其中前4个字节是包头（0x55, 0xEE, 0x02, 0x04）
    packet = bytearray([0x55, 0xEE, 0x02, 0x04])

    # 填充数据包的内容，这里我们随机生成一些模拟数据
    for i in range(64):  # 64个数据点
        for j in range(4):  # 每个数据点有4个通道
            # 随机生成一个16位有符号整数，表示ADC值
            adc_value = random.randint(-0x8000, 0x7FFF)
            # 将ADC值转换为字节并添加到数据包中
            packet.extend(struct.pack('h', adc_value))

    # 确保数据包长度为1032字节（如果需要，可以添加额外的填充字节）
    while len(packet) < 2048:
        packet.append(0x00)

    # 截断数据包到1032字节（以防万一超过了这个长度）
    packet = packet[:2048]

    return packet


def start_client():
    # 创建一个TCP客户端
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    param_set_response = 0

    try:
        # 连接到服务器
        client_socket.connect(('127.0.0.1', 8234))  # 假设服务器运行在本地机器上
        print("已连接到服务器")

        while True:
            if param_set_response == 0:
                # 创建并发送模拟数据包
                mock_data_packet = create_mock_data_packet()
                client_socket.send(mock_data_packet)
                print(f"向服务器发送数据完成：{mock_data_packet}")

                # 接收来自服务器的参数设置命令
                param_set_response = client_socket.recv(2048)
                # 可以选择打印或处理这个响应
                print(param_set_response)



            # 等待10秒（模拟服务器设置参数后的等待时间）
            time.sleep(10)

            # 接收来自服务器的采样开始命令
            sampling_start_response = client_socket.recv(2048)
            # 可以选择打印或处理这个响应
            print(sampling_start_response)

            # 等待3秒，然后重复发送模拟数据包
            time.sleep(3)

    except KeyboardInterrupt:
        # 捕获Ctrl+C以优雅地关闭客户端
        print("客户端已关闭")

    finally:
        # 关闭客户端套接字
        client_socket.close()


if __name__ == "__main__":
    start_client()