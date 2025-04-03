import socket
import struct
import time

# 参数设置缓冲区
paramSetBuf = [0x55, 0xEE, 0x80, 0x0E, 0x10, 0x01, 0x81, 0x00, 0x00, 0x00, 0x00, 0x01, 0x01, 0x00, 0x03, 0xE8, 0x00, 0x50]

# 开始采样命令缓冲区
samplingStartBuf = [0x55, 0xEE, 0x00, 0x05, 0x10, 0x01, 0x24, 0x10, 0x8D]

# 将数据转换为十六进制字符串格式
def print_hex(var):
    hex_str = ' '.join([format(byte, '02X') for byte in var])
    print(hex_str)

def start_server():
    # 创建一个TCP监听器
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(('0.0.0.0', 8234))  # 服务器端口
    server_socket.listen(1)
    print("TCP服务器已启动，等待连接...")

    while True:
        client_socket, addr = server_socket.accept()
        print(f"收到客户端连接，地址: {addr}")
        start_communication(client_socket)
        client_socket.close()

def start_communication(client_socket):
    # 处理脉冲信号
    # 注意：这里处理DAQ缓冲区中的脉冲信号。
    #       如果不处理，脉冲信号可能会与有效数据混合。
    client_socket.recv(2048)  # 接收来自客户端的响应

    # 设置ADC参数
    client_socket.send(bytearray(paramSetBuf))  # 向客户端发送数据
    response = client_socket.recv(2048)  # 接收来自客户端的响应
    print_hex(response)
    time.sleep(10)

    # ADC开始采样
    client_socket.send(bytearray(samplingStartBuf))  # 向客户端发送数据
    response = client_socket.recv(2048)  # 接收来自客户端的响应
    print_hex(response)

    while True:
        # 用于存储接收到的数据包
        recvBuf = client_socket.recv(1032)  # 每个数据包长度为1032字节（固定长度）
        if recvBuf[0] == 0x55 and recvBuf[1] == 0xEE and recvBuf[2] == 0x02 and recvBuf[3] == 0x04:
            for i in range(64):
                print(f"数据点{i + 1}: ", end="")
                for j in range(4):
                    # 将接收到的数据转换为电压值
                    voltage = struct.unpack('h', recvBuf[(7 + j * 2 + i * 8): (9 + j * 2 + i * 8)])[0] * -4.000 / 0x8000 / 0.344
                    print(f"通道{j + 1} = {voltage:.8f}V,\t", end="")
                print()

if __name__ == "__main__":
    start_server()