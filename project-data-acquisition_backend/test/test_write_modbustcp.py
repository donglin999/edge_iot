import time

import modbus_tk.modbus_tcp as mt
import modbus_tk.defines as cst

if __name__ == '__main__':

    a = "气缸 MC39061410"
    print(f"收到的a:{a}")
    a_no_spaces = a.replace(" ", "")
    print(f"去掉a的空格a_no_spaces:{a_no_spaces}")
    encoded_bytes = a_no_spaces.encode('gb2312')
    print(f"将a转为gb2312，encoded_bytes:{encoded_bytes}")
    byte_count = len(encoded_bytes)
    print(f"计算encoded_bytes的长度byte_count:{byte_count}")
    if byte_count % 2 != 0:
        b = "0" + a_no_spaces
        print(f"a长度为奇数，加0为b:{b}")
    else:
        b = a_no_spaces
        print(f"a长度为偶数，直接用b:{b}")
    encoded_bytes = b.encode('gb2312')
    print(f"更新encoded_bytes为b转的gb2312码:{encoded_bytes}")
    byte_count = len(encoded_bytes)
    print(f"更新byte_count为b的长度:{byte_count}")
    data_format = "s"
    for i in range(byte_count - 1):
        data_format += 's'
    print(f"根据b的长度创建data_format:{data_format}")
    # 将每两个字节倒换
    swapped_bytes = []
    for i in range(0, len(encoded_bytes) - 1, 2):
        swapped_bytes.extend([encoded_bytes[i + 1], encoded_bytes[i]])
    # 将每个字节转换为字节串
    result = [bytes([byte]) for byte in swapped_bytes]

    master = mt.TcpMaster('192.168.8.65', 502)  # 目标机（PLC或触摸屏）地址
    # v1 = master.execute(slave=1,function_code=cst.WRITE_SINGLE_REGISTER,starting_address=0,
    #                   quantity_of_x=0,output_value=0,data_format=">",expected_length=-1,
    #                  write_starting_address_fc23=0,number_file=None,pdu="",returns_raw=None)#06功能码
    while True:
        write_result = master.execute(slave=1, function_code=cst.WRITE_MULTIPLE_REGISTERS, starting_address=399,
                                      quantity_of_x=2, output_value=result, data_format=data_format)
        print(f"写入成功标记write_result:{write_result}")
        if write_result:
            break
        else:
            time.sleep(1)


