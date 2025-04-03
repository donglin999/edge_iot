import struct

from lib.HslCommunication import MelsecMcNet

def int_to_float32(value):
    # 将整数转换为4字节的二进制数据
    packed = struct.pack('i', value)
    # 将4字节的整数数据转换为4字节的浮点数数据
    float32 = struct.unpack('f', packed)[0]
    return float32

def circular_shift_left(value, shift):
    bit_size = 32  # 32位整数
    # 计算实际需要移动的位数，因为移动32位相当于没有移动
    shift = shift % bit_size
    # 进行循环左移
    return ((value << shift) | (value >> (bit_size - shift))) & ((1 << bit_size) - 1)

class M20:
    def __init__(self, ip, port):
        self.plc = MelsecMcNet(ip, port)
        print(f"开始连接{ip}：{port} plc，请等待...")
        if not self.plc.ConnectServer().IsSuccess:
            print("PLC connect falied !")
        else:
            print(f"plc：{ip}：{port} plc连接成功")

    def read_float(self, address, length, rotate=False):
        value = self.plc.ReadUInt32(address, length).Content[0]
        if rotate:
            value = circular_shift_left(value, 16)
        f_value = struct.unpack('<f', struct.pack('<I', value))[0]
        return hex(value), f_value

    def __call__(self, addr):
        print(f"ReadInt16,{addr}：{self.plc.ReadInt16(addr, 2).Content[0]}")
        #print(f"ReadInt32,{addr}：{self.plc.ReadInt32(addr, 2).Content[0]}")
        #print(f"ReadUInt32,{addr}：{hex(self.plc.ReadUInt32(addr, 40).Content[0])}")
        #print(f"ReadUInt16,{addr}：{hex(self.plc.ReadUInt16(addr, 1).Content[0])}")
        #print(f"ReadBool,{addr}：{hex(self.plc.ReadBool(addr, 1).Content[0])}")
        #print(f"ReadString,{addr}：{self.plc.ReadString(addr, 30).Content}")
        #hex_v, f_v = self.read_float(addr, 1, rotate=True)
        #print(f"ReadString,{addr}：{addr} {hex_v}---{f_v}")

        self.plc.ConnectClose()

if __name__ == '__main__':

    for addr in ['D100']:
        M20("192.168.3.251", 4999)(addr)



