import serial
import time


class SerialClient:
    def __init__(self, port='/dev/ttyUSB0', baudrate=9600):
        """
        初始化串口客户端
        :param port: 串口设备路径
        :param baudrate: 波特率
        """
        self.port = port
        self.baudrate = baudrate
        self.serial = None
        self.connected = False

    def connect(self):
        """建立串口连接"""
        try:
            self.serial = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=10
            )
            self.connected = True
            print(f"成功连接到串口 {self.port}，波特率 {self.baudrate}")
            return True
        except Exception as e:
            print(f"串口连接失败: {e}")
            return False

    def send_binary_data(self, data_bytes):
        """
        直接发送二进制数据
        :param data_bytes: 字节数组或字节对象
        """
        if not self.connected or self.serial is None:
            print("未连接，请先建立连接")
            return False

        try:
            self.serial.write(data_bytes)
            # 显示发送的数据
            hex_display = ' '.join([f'{b:02X}' for b in data_bytes])
            print(f"发送二进制数据: {hex_display}")
            print(f"字节长度: {len(data_bytes)}")
            return True
        except Exception as e:
            print(f"发送失败: {e}")
            return False

    def send_hex_data(self, hex_string):
        """
        发送十六进制数据（转换为二进制）
        :param hex_string: 十六进制字符串，例如 "EF 0C AE 9D 81 11 22 33 44 55 66 2C"
        """
        try:
            # 将十六进制字符串转换为字节数组
            hex_bytes = bytes.fromhex(hex_string.replace(' ', ''))
            return self.send_binary_data(hex_bytes)
        except Exception as e:
            print(f"十六进制转换失败: {e}")
            return False

    def send_keep_warm_command(self):
        """
        发送保温命令（直接使用二进制数据）
        """
        # 直接构造二进制数据包
        keep_warm_binary = bytes([0xEF, 0x09, 0xAE, 0x8F, 0xFF, 0x00, 0x00, 0x34])
        return self.send_binary_data(keep_warm_binary)

    def create_custom_packet(self, *values):
        """
        创建自定义数据包
        :param values: 十进制或十六进制值的列表
        """
        try:
            data_bytes = bytes(values)
            return self.send_binary_data(data_bytes)
        except Exception as e:
            print(f"创建数据包失败: {e}")
            return False

    def set_receive_timeout(self, timeout_seconds):
        """设置接收超时时间"""
        if self.serial:
            self.serial.timeout = timeout_seconds
            print(f"接收超时设置为 {timeout_seconds} 秒")

    def receive_data(self, buffer_size=1024, timeout_seconds=5):
        """接收数据"""
        if not self.connected or self.serial is None:
            print("未连接，请先建立连接")
            return None

        try:
            # 设置接收超时
            original_timeout = self.serial.timeout
            self.serial.timeout = timeout_seconds

            data = self.serial.read(buffer_size)

            # 恢复原始超时设置
            self.serial.timeout = original_timeout

            if data:
                hex_data = data.hex().upper()
                # 格式化十六进制显示
                formatted_hex = ' '.join([hex_data[i:i + 2] for i in range(0, len(hex_data), 2)])

                print(f"接收数据: {formatted_hex}")
                print(f"字节长度: {len(data)}")
                return data
            else:
                print("串口连接已断开")
                self.connected = False
                return None
        except Exception as e:
            print(f"接收失败: {e}")
            return None

    def clear_receive_buffer(self, wait_time=0.5, max_attempts=3):
        """清空接收缓冲区"""
        if not self.connected or self.serial is None:
            return

        print(f"开始清空接收缓冲区，等待时间: {wait_time}秒，最大尝试次数: {max_attempts}")

        for attempt in range(max_attempts):
            try:
                # 先等待一段时间，让设备有时间发送自动响应
                time.sleep(wait_time)

                # 清空串口缓冲区
                cleared_count = 0
                while self.serial.in_waiting > 0:
                    data = self.serial.read(self.serial.in_waiting)
                    if not data:
                        break
                    cleared_count += 1
                    hex_display = ' '.join([f'{b:02X}' for b in data])
                    print(f"第{attempt + 1}次清空 - 数据{cleared_count}: {hex_display}")

                if cleared_count == 0:
                    print(f"第{attempt + 1}次清空完成，无数据")
                    break
                else:
                    print(f"第{attempt + 1}次清空完成，清除了{cleared_count}条数据")

            except Exception as e:
                print(f"第{attempt + 1}次清空缓冲区失败: {e}")

        print("接收缓冲区清空完成")

    def close(self):
        """关闭连接"""
        if self.serial:
            self.serial.close()
            self.connected = False
            print("串口连接已关闭")


def main():
    # 创建串口客户端实例
    client = SerialClient()

    while True:
        time.sleep(3)
        # 建立连接
        if client.connect():
            try:
                # 连接后立即清空接收缓冲区
                print("开始清空接收缓冲区...")
                client.clear_receive_buffer(wait_time=1.0, max_attempts=5)

                # 直接创建二进制数据包发送
                print("发送二进制数据包...")

                # binary_data = bytes([0xEF, 0x08, 0xAE, 0x83, 0x81, 0x00, 0x00, 0xA9])
                binary_data = bytes([0xEF, 0x08, 0xAF, 0x8F, 0xFF, 0x00, 0x00, 0x34])

                # EF 09 AE 8F FF 00 00
                # binary_data = bytes([0xEF, 0x0C, 0xAE, 0x9D, 0x81, 0x11, 0x22, 0x33, 0x44, 0x55, 0x66, 0x2C])
                if client.send_binary_data(binary_data):
                    # 等待响应，设置5秒超时
                    print("等待响应...")
                    response = client.receive_data(timeout_seconds=5)
                    if response is None:
                        print("未收到响应，继续下一次循环")
                else:
                    print("发送失败，继续下一次循环")

            except KeyboardInterrupt:
                print("\n用户中断操作")
                break


if __name__ == "__main__":
    main()