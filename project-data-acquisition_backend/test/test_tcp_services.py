import socket


def tcp_server():
    # 创建一个socket对象
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # 绑定到本地主机的8899端口
    server_socket.bind(('10.16.37.200', 8899))

    # 开始监听连接请求，参数5表示最多可以有5个排队等待的连接
    server_socket.listen(5)

    print("TCP服务器正在运行，等待客户端连接...")

    while True:
        # 接受一个新连接，返回一个新的socket和客户端地址
        client_socket, addr = server_socket.accept()

        print(f"已连接到客户端：{addr}")

        # 接收数据，这里设置接收缓冲区大小为1024字节
        data = client_socket.recv(1024)

        # 打印接收到的数据
        print("从客户端接收的数据:", data.decode())

        # 关闭与客户端的连接
        client_socket.close()


# 调用函数启动服务器
tcp_server()