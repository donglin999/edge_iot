import socket
import time


def tcp_client(server_host='127.0.0.1', server_port=8899, message='Hello, TCP Server!'):
    # 创建一个新的socket对象（每次迭代都创建）
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # 连接到服务器
    client_socket.connect((server_host, server_port))
    print(f"已连接到服务器：{server_host}:{server_port}")
    while True:  # 无限循环，直到手动停止
        try:

            # 发送数据到服务器
            client_socket.sendall(message.encode())
            print(f"已发送数据：{message}")

            # 可选择性地接收服务器的响应（如果服务器有发送响应的话）
            # response = client_socket.recv(1024)
            # print(f"从服务器接收到的响应：{response.decode()}")
            # 等待一秒再发送下一次
            time.sleep(1)

        except (ConnectionRefusedError, OSError) as e:
            # 处理连接错误
            print(f"无法连接到服务器或发送数据时出错：{e}")
            # 可以选择添加重试逻辑，比如等待几秒钟再尝试连接
            # time.sleep(5)  # 例如，等待5秒再重试
            # 或者直接继续下一次循环（注意：这可能会导致无限循环，如果没有适当的退出条件）
            continue  # 如果你想要继续尝试连接，使用 continue
            # 如果你想要退出循环，使用 break

        except Exception as e:
            # 处理其他可能的异常
            print(f"发生了一个未处理的异常：{e}")
            break  # 或者根据你的需求选择其他处理方式

        # 注意：这里没有finally块来关闭socket，因为我们在每次迭代结束时都关闭了它
    # 关闭连接（如果需要每秒发送一次且不需要保持连接）
    client_socket.close()
    print("已关闭与服务器的连接（为了每秒发送一次而关闭）")


# 调用函数启动客户端并发送数据
tcp_client()