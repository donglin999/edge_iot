#!/usr/bin/env python
# -*- encoding: utf-8 -*-

from modbus_tk import modbus_tcp
import modbus_tk.defines as cst
from utils.baseLogger import Log

class ModbustcpClient:
    def __init__(self, ip, port) -> None:
        self.ip = ip
        self.port = port
        self.master = modbus_tcp.TcpMaster(self.ip, port=self.port, timeout_in_sec=10)
    
    def read_modbustcp(self, register_dict, slave_addr):
        tag_data = []
        # print(f"register_dict:{register_dict},slave_addr:{slave_addr}")
        for K, V in register_dict.items():
            if isinstance(V, dict):
                # print(V['source_addr'])
                if isinstance(V['source_addr'], int):
                    addr = V['source_addr'] - 40001
                else:
                    addr = int(float(V['source_addr'])) - 40001
                # print(V['type'])
                if isinstance(V['type'], int):
                    data_type = V['type']
                else:
                    data_type = 3
                # print(V['num'])
                if isinstance(V['num'], int):
                    num = V['num']
                else:
                    num = int(V['num'])
                if V['type'] == "32位浮点数":
                    data_format = '>f'
                elif V['type'] == "16位有符号整数":
                    data_format = ''
                elif V['type'] == "布尔型":
                    data_format = ''
                else:
                    data_format = ''

                if V['data_source'] == "ART":
                    data_format = ''
                    addr = addr + 257
                try:
                    if slave_addr:
                        slave = int(slave_addr)
                    else:
                        slave = V[slave_addr]

                    data = self.master.execute(slave=slave, function_code=data_type,
                                               starting_address=addr,
                                               quantity_of_x=num, data_format=data_format)
                except Exception as e:
                    print(f"读modbustcp报错{e}")
                    return "无法连接"

                modbustcp_data = {}
                cn_name = V['cn_name']
                en_name = V['en_name']
                part_name = V['part_name']
                input_data_minimum = V['input_data_minimum']
                input_data_maximum = V['input_data_maximum']
                output_data_minimum = V['output_data_minimum']
                output_data_maximum = V['output_data_maximum']
                unit = V['unit']
                data_source = V['data_source']
                coefficient = V['coefficient']
                precision = V['precision']
                device_a_tag = register_dict['device_a_tag']
                device_name = register_dict['device_name']
                # print(f"1")
                if input_data_minimum == 4 and input_data_maximum == 20:
                    i = (data[0] / 65535) * (input_data_maximum - input_data_minimum) + input_data_minimum
                    modbustcp_data[en_name] = float((i - input_data_minimum) * (output_data_maximum -
                            output_data_minimum) / (input_data_maximum - input_data_minimum) + output_data_minimum)
                    modbustcp_data['cn_name'] = cn_name
                    modbustcp_data['addr'] = V['source_addr']
                    modbustcp_data['part_name'] = part_name
                    modbustcp_data['unit'] = unit
                    modbustcp_data['data_source'] = data_source
                    modbustcp_data['device_a_tag'] = device_a_tag
                    modbustcp_data['device_name'] = device_name
                    modbustcp_data['kafka_position'] = V['kafka_position']
                    tag_data.append(modbustcp_data)
                elif input_data_minimum == 0 and input_data_maximum == 65535:
                    modbustcp_data[en_name] = (data[0] / 65535) * (output_data_maximum - output_data_minimum) + output_data_minimum
                    modbustcp_data['cn_name'] = cn_name
                    modbustcp_data['addr'] = V['source_addr']
                    modbustcp_data['part_name'] = part_name
                    modbustcp_data['unit'] = unit
                    modbustcp_data['data_source'] = data_source
                    modbustcp_data['device_a_tag'] = device_a_tag
                    modbustcp_data['device_name'] = device_name
                    modbustcp_data['kafka_position'] = V['kafka_position']
                    tag_data.append(modbustcp_data)
                else:
                    # print(f"2")
                    if '.' in str(V['source_addr']):
                        # print(f"地址{V['source_addr']}是浮点数")
                        # 将浮点数转换为字符串
                        num_str = str(V['source_addr'])

                        # 找到小数点的位置
                        decimal_point_index = num_str.find('.')

                        # 如果找到了小数点，则截取小数点之后的部分
                        decimal_part_str = int(num_str[decimal_point_index + 1:])

                        # 使用 bin() 函数获取二进制字符串，并去掉 '0b' 前缀
                        binary_str = bin(data[0])[2:]

                        # 使用 zfill() 函数填充前导零，直到长度为16
                        binary_str_16bit = binary_str.zfill(16)

                        modbustcp_data[en_name] = binary_str_16bit[decimal_part_str]
                    else:
                        modbustcp_data[en_name] = round(float(data[0] * coefficient), int(precision))

                    modbustcp_data['cn_name'] = cn_name
                    modbustcp_data['addr'] = V['source_addr']
                    modbustcp_data['part_name'] = part_name
                    modbustcp_data['unit'] = unit
                    modbustcp_data['data_source'] = data_source
                    modbustcp_data['device_a_tag'] = device_a_tag
                    modbustcp_data['device_name'] = device_name
                    modbustcp_data['kafka_position'] = V['kafka_position']
                    # print(f"3")
                    tag_data.append(modbustcp_data)
        # 断开连接
        self.master.close()
        return tag_data

