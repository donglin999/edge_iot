import modbus_tk.modbus_tcp as mt
import modbus_tk.defines as cst

modbustcp_ip = '192.168.1.50'
modbustcp_port = 502
master = mt.TcpMaster(modbustcp_ip, modbustcp_port)  # 目标机（PLC或触摸屏）地址
master.set_timeout(5)
slave = 1
addr = 0
num = 2
data_type = 3
# data_type = 4
# 读浮点数
# data_format='>f'
# 读16位有符号整数
# data_format=''
# 读32位有符号长整数
data_format='>i'
r = master.execute(slave=slave, function_code=data_type,
                   starting_address=addr, quantity_of_x=num, data_format=data_format)
print(f"从modbustcp：{modbustcp_ip}中，从站地址：{slave}，起始数据地址：{addr}，寄存器类型：{data_type}，数据类型：{data_format}，读取{num}个数据为{r}")