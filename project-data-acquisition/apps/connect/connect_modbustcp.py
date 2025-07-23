#!/usr/bin/env python
# -*- encoding: utf-8 -*-

from modbus_tk import modbus_tcp
import modbus_tk.defines as cst
from apps.utils.baseLogger import Log
import time
import struct


class ModbustcpClient:
    def __init__(self, ip, port, register_dict) -> None:
        self.ip = ip
        self.port = port
        self.master = None
        try:
            self.connect()
            self.register_configs = self._group_continuous_registers(register_dict)
        except Exception as e:
            Log().printError(f"Modbus TCP连接失败 {self.ip}:{self.port}, 错误: {e}")
            raise e

    def connect(self):
        """连接到Modbus TCP设备"""
        try:
            self.master = modbus_tcp.TcpMaster(self.ip, port=self.port, timeout_in_sec=10)
            Log().printInfo(f"成功连接到Modbus TCP设备 {self.ip}:{self.port}")
            return True
        except Exception as e:
            Log().printError(f"连接Modbus TCP设备失败 {self.ip}:{self.port}, 错误: {e}")
            return False

    def _get_function_code_and_address(self, address):
        """根据地址判断功能码和实际地址"""
        if 1 <= address <= 9999:  # Coil
            return cst.READ_COILS, address - 1
        elif 10001 <= address <= 19999:  # Discrete Input
            return cst.READ_DISCRETE_INPUTS, address - 10001
        elif 30001 <= address <= 39999:  # Input Register
            return cst.READ_INPUT_REGISTERS, address - 30001
        elif 40001 <= address <= 49999:  # Holding Register
            return cst.READ_HOLDING_REGISTERS, address - 40001
        else:
            raise ValueError(f"无效的寄存器地址: {address}")

    def _convert_data_type(self, data, data_type):
        """根据数据类型转换数据"""
        try:
            if data_type == 'BOOL':
                return bool(data)
            elif data_type == 'UINT16':
                return data
            elif data_type == 'INT16':
                # 如果值大于32767，说明是负数
                return data if data <= 32767 else data - 65536
            elif data_type == 'INT32':
                if isinstance(data, list) and len(data) >= 2:
                    # 合并两个寄存器的值
                    combined = (data[0] << 16) | data[1]
                    # 处理负数
                    if combined > 2147483647:
                        combined -= 4294967296
                    return combined
                else:
                    raise ValueError("INT32类型需要两个连续的寄存器")
            elif data_type == 'UINT32':
                if isinstance(data, list) and len(data) >= 2:
                    return (data[0] << 16) | data[1]
                else:
                    raise ValueError("UINT32类型需要两个连续的寄存器")
            elif data_type == 'FLOAT32':
                if isinstance(data, list) and len(data) >= 2:
                    # 将两个16位整数转换为浮点数
                    combined = (data[0] << 16) | data[1]
                    return struct.unpack('!f', struct.pack('!I', combined))[0]
                else:
                    raise ValueError("FLOAT32类型需要两个连续的寄存器")
            else:
                return data
        except Exception as e:
            Log().printError(f"数据类型转换失败: {e}")
            return data

    def _group_continuous_registers(self, registers):
        """将连续的寄存器地址分组"""
        try:
            # 首先按功能码分组
            function_groups = {}
            for en_name, register_conf in registers.items():
                if isinstance(register_conf, dict):
                    # 根据地址判断功能码和实际地址
                    func_code, actual_addr = self._get_function_code_and_address(register_conf['source_addr'])
                    if func_code not in function_groups:
                        function_groups[func_code] = []
                    # 更新配置中的实际地址
                    register_conf['actual_addr'] = actual_addr
                    function_groups[func_code].append(register_conf)

            # 对每个功能码组内的寄存器按实际地址排序
            for func_code in function_groups:
                function_groups[func_code].sort(key=lambda x: x['actual_addr'])

            # 对每个功能码组内的寄存器进行连续分组
            continuous_groups = {}
            for func_code, regs in function_groups.items():
                continuous_groups[func_code] = []
                current_group = []

                for i, reg in enumerate(regs):
                    if not current_group:
                        current_group.append(reg)
                    else:
                        # 检查是否连续
                        last_reg = current_group[-1]
                        expected_addr = last_reg['actual_addr'] + last_reg['num']

                        if reg['actual_addr'] == expected_addr:
                            current_group.append(reg)
                        else:
                            if current_group:
                                continuous_groups[func_code].append(current_group)
                            current_group = [reg]

                if current_group:
                    continuous_groups[func_code].append(current_group)

            return continuous_groups
        except Exception as e:
            Log().printError(f"将连续的寄存器地址分组失败 {self.ip}:{self.port}, 错误: {e}")
            print(f"将连续的寄存器地址分组失败 {self.ip}:{self.port}, 错误: {e}")
            time.sleep(10)
            return None

    def read_modbustcp(self, slave_addr=1):
        """读取Modbus TCP数据，支持连续地址批量读取"""
        if not self.master:
            if not self.connect():
                return None

        tag_data = []

        try:
            for func_code, groups in self.register_configs.items():
                for group in groups:
                    # print(group)
                    start_addr = group[0]['actual_addr']  # 使用实际地址
                    total_length = (group[-1]['actual_addr'] + group[-1]['num']) - start_addr

                    try:
                       # 批量读取数据
                        data = self.master.execute(
                            slave=slave_addr,
                            function_code=func_code,
                            starting_address=start_addr,
                            quantity_of_x=total_length
                        )
                        # 分配数据到各个寄存器
                        offset = 0
                        for reg in group:
                            reg_length = reg['num']
                            reg_data = data[offset:offset + reg_length]
                            offset += reg_length

                            # 转换数据类型
                            converted_data = self._convert_data_type(
                                reg_data[0] if len(reg_data) == 1 else list(reg_data),
                                reg['type']
                            )

                            # 构建数据字典
                            modbustcp_data = {
                                reg['en_name']: converted_data,
                                'cn_name': reg['cn_name'],
                                'device_a_tag': reg['device_a_tag'],
                                'device_name': reg['device_name'],
                            }

                            # 添加可选字段
                            if 'kafka_position' in reg:
                                modbustcp_data['kafka_position'] = reg['kafka_position']

                            tag_data.append(modbustcp_data)
                    except Exception as e:
                        Log().printError(
                            f"读取寄存器失败 - 起始地址: {start_addr}, 长度: {total_length}, 功能码: {func_code}, 错误: {e}")
                        continue

        except Exception as e:
            Log().printError(f"读取Modbus TCP数据总体错误: {e}")
            return None

        return tag_data

    def close(self):
        """关闭连接"""
        if self.master:
            try:
                self.master.close()
                self.master = None
                Log().printInfo(f"已关闭与Modbus TCP设备的连接 {self.ip}:{self.port}")
            except Exception as e:
                Log().printError(f"关闭Modbus TCP连接失败: {e}")
