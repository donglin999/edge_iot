import socket


def read_data_from_server():
    # 创建一个socket对象
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        # 连接到本机的TCP服务器，端口号为8899
        client_socket.connect(('172.20.10.29', 8899))

        # 接收数据，这里设置接收缓冲区大小为1024字节
        data = client_socket.recv(1024)

        # 打印接收到的数据
        print("从服务器接收的数据:", data.decode())

    except ConnectionRefusedError:
        print("无法连接到服务器，请检查服务器是否正在运行以及端口是否正确。")

    finally:
        # 关闭socket连接
        client_socket.close()


# 调用函数
read_data_from_server()