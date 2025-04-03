#!/usr/bin/env python
# -*- encoding: utf-8 -*-

import json
import re
import time
from kafka import KafkaProducer
from datetime import datetime, timedelta, timezone
import struct
from apps.connect.connect_influx import w_influx, InfluxClient
from lib.HslCommunication import MelsecMcNet
from settings import DevelopmentConfig
from utils.baseLogger import Log

def circular_shift_left(value, shift):
    bit_size = 32  # 32位整数
    # 计算实际需要移动的位数，因为移动32位相当于没有移动
    shift = shift % bit_size
    # 进行循环左移
    return ((value << shift) | (value >> (bit_size - shift))) & ((1 << bit_size) - 1)

class PLCClient:
    def __init__(self, ip, port, device_a_tag, device_name) -> None:
        self.ip = ip
        self.port = port
        self.device_a_tag = device_a_tag
        self.device_name = device_name
        if DevelopmentConfig().KAFKA_ENABLED:
            self.kafka_producer = KafkaProducer(bootstrap_servers=DevelopmentConfig().kafka_bootstrap_servers,value_serializer=lambda x: json.dumps(x).encode('utf-8'))
            print(f"kafka连接成功，{DevelopmentConfig().kafka_bootstrap_servers}")
            Log().printInfo(f"kafka连接成功，{DevelopmentConfig().kafka_bootstrap_servers}")
        self.influxdb_client = InfluxClient().connect()
        print(f"influxdb对象创建成功")
        self.plc = MelsecMcNet(self.ip, self.port)

    def contains_alpha_or_digit(self, s):
        # 检查是否包含字母
        contains_alpha = any(char.isalpha() for char in s)
        # 检查是否包含数字
        contains_digit = any(char.isdigit() for char in s)

        # 如果包含字母或数字，就打印消息
        if contains_alpha or contains_digit:
            print(f"{s}变量包含字母或数字")
        else:
            # 可选：如果不包含，也可以打印一条消息（这里省略）
            pass

    def read_plc(self, register_dict):

        while True:
            try:
                if not self.plc.ConnectServer().IsSuccess:
                    self.plc = MelsecMcNet(self.ip, self.port)
                    Log().printError(f"PLC {self.ip}：{self.port} connect error")
                    print(f"PLC {self.ip}：{self.port} connect error")
                    if DevelopmentConfig().KAFKA_ENABLED:
                        # 假设local_time是一个UTC时间对象
                        # 例如，我们可以手动创建一个UTC时间
                        utc_time = datetime.now(timezone.utc)

                        # 将UTC时间转换为北京时间（UTC+8）
                        # 注意：timedelta(hours=8)用于将UTC时间转换为北京时间
                        beijing_time = utc_time + timedelta(hours=8)

                        # 使用strftime来格式化时间
                        formatted_time = beijing_time.strftime("%Y-%m-%d %H:%M:%S")
                        ac_status_data = {"code": "200", "deviceIP": DevelopmentConfig().INFLUXDB_HOST,
                                          "message": f"{self.ip}：{self.port} PLC连接失败",
                                          "serviceCode": "plc_kafka", "timestamp": formatted_time}

                        self.kafka_producer.send("ac_status_data", ac_status_data)
                        # Log().printInfo(f"kafka消息推送成功，主题：ac_status_data，内容：{ac_status_data}")


                    package = \
                        {
                            "measurement": self.device_a_tag,
                            "tags":
                                {
                                    "device_a_tag": self.device_a_tag,
                                    "device_name": self.device_name,
                                    "kafka_position": "runningstatus",
                                    "cn_name": "设备状态4"
                                },
                            "fields": {"runningstatus": 2}
                        }
                    json_body = [package]

                    w_influx(self.influxdb_client, self.device_name, json_body)

                    time.sleep(3)

                else:
                    break

            except Exception as e:
                Log().printError(f"{self.ip}连接报错：{e}")
                print(f"{self.ip}连接报错：{e}")
                continue

        try:
            tag_data = []
            if self.ip == "10.79.226.7":
                Log().printInfo(f"{self.ip}：{self.port}plc开始读取register_dict:{register_dict}")
                print(f"{self.ip}：{self.port}plc开始读取register_dict:{register_dict}")

            for en_name, register_conf in register_dict.items():
                if isinstance(register_conf, dict):

                    try:
                        num = int(register_conf['num'])
                        addr = register_conf['source_addr']
                        coefficient = register_conf['coefficient']
                        kafka_position = register_conf['kafka_position']
                        precision = int(register_conf['precision'])
                        cn_name = register_conf['cn_name']
                        plc_data = {}
                        if register_conf['type'] == 'str':
                            if en_name == "codeResult":
                                read_data = str(self.plc.ReadString(addr, num).Content)[4:64]
                                # 检查是否包含字母
                                contains_alpha = any(char.isalpha() for char in read_data)
                                # 检查是否包含数字
                                contains_digit = any(char.isdigit() for char in read_data)

                                # 如果包含字母或数字，就打印消息
                                if contains_alpha or contains_digit:
                                    print(f"{read_data}变量包含字母或数字")
                                    pass
                                else:
                                    read_data = "None"
                                plc_data[en_name] = re.sub(r'\s+', '', read_data)
                                plc_data['kafka_position'] = kafka_position
                                plc_data['cn_name'] = cn_name
                            else:
                                plc_data[en_name] = str(self.plc.ReadString(addr, num).Content)
                                plc_data['kafka_position'] = kafka_position
                                plc_data['cn_name'] = cn_name
                        elif register_conf['type'] == 'int16':
                            plc_data[en_name] = round(self.plc.ReadInt16(addr, num).Content[0] * coefficient, precision)
                            plc_data['kafka_position'] = kafka_position
                            plc_data['cn_name'] = cn_name
                        elif register_conf['type'] == 'int32':
                            plc_data[en_name] = round(self.plc.ReadInt32(addr, num).Content[0] * coefficient, precision)
                            plc_data['kafka_position'] = kafka_position
                            plc_data['cn_name'] = cn_name
                        elif register_conf['type'] == 'float':
                            plc_data[en_name] = round(self.plc.ReadFloat(addr, num).Content[0] * coefficient, precision)
                            plc_data['kafka_position'] = kafka_position
                            plc_data['cn_name'] = cn_name
                            # print(f"{self.ip}：{self.port}plc数据读取成功，数据为{plc_data}")
                        elif register_conf['type'] == 'float2':
                            value = self.plc.ReadUInt32(addr, num).Content[0]
                            # print(f"value:{value}")
                            value2 = circular_shift_left(value, 16)
                            # print(f"value2:{value2}")
                            value3 = struct.unpack('<f', struct.pack('<I', value2))[0]
                            # print(f"{self.ip}：{self.port}plc数据读取成功，数据value3:{value3},数据value3类型{type(value3)}:")
                            plc_data[en_name] = round(value3, precision)
                            plc_data['kafka_position'] = kafka_position
                            plc_data['cn_name'] = cn_name
                            # print(f"{self.ip}：{self.port}plc数据读取成功，数据:{plc_data[en_name]},plc_data[en_name]数据类型{type(plc_data[en_name])}:")
                        elif register_conf['type'] == 'bool':
                            plc_data[en_name] = int(self.plc.ReadBool(addr, num).Content[0])
                            plc_data['kafka_position'] = kafka_position
                            plc_data['cn_name'] = cn_name
                        elif register_conf['type'] == 'hex':
                            plc_data[en_name] = hex(self.plc.ReadUInt32(addr, num).Content[0])
                            plc_data['kafka_position'] = kafka_position
                            plc_data['cn_name'] = cn_name
                        tag_data.append(plc_data)
                    except Exception as e:
                        Log().printError(f"read plc addr: {addr} Exception: {e}")
                        print(f"read plc addr: {addr} Exception: {e}")
                        continue
            self.plc.ConnectClose()
            if self.ip == "10.79.226.7":
                Log().printInfo(f"{self.ip}：{self.port}plc数据读取成功，数据为{tag_data}")
                print(f"{self.ip}：{self.port}plc数据读取成功，数据为{tag_data}")
            return tag_data
        except Exception as e:
            Log().printError(f"{self.ip}，{register_conf}读地址数据报错：{e}")
            print(f"{self.ip}，{register_conf}地址数据报错：{e}")

    def write_plc(self, register_dict):
        while True:
            if not self.plc.ConnectServer().IsSuccess:
                Log().printError("PLC connect !")
                time.sleep(1)
                continue
            else:
                break
        
        for register_name, register_conf in register_dict.items():
            try:
                num = register_conf['num']
                addr = register_conf['addr']
                value = register_conf['value']
                
                if register_conf['type'] == 'str':
                    self.plc.WriteUnicodeString(addr, value, num)
                elif register_conf['type'] == 'int16':
                    self.plc.WriteInt16(addr, value)
                elif register_conf['type'] == 'float':
                    self.plc.WriteFloat(addr, value)
            except Exception as e:
                Log().printError('write plc '+register_name+' failed')
                Log().printError(e)
        self.plc.ConnectClose()

if __name__ == "__main__":
    ip = "192.168.3.251"
    port = 4998
    device_a_tag = "A_test"
    device_name = "test_device"
    PLC_client = PLCClient(ip, port, device_a_tag, device_name)
    register_dict = {
        "en_name": {
            'num': 1,
            'source_addr':"D100",
            'coefficient':1,
            'kafka_position':"meatear",
            'precision':2,
            'type':"int16",
            'cn_name': "test1"
        }
    }
    while True:
        tag_data = PLC_client.read_plc(register_dict)
        print(tag_data)
        time.sleep(1)

        