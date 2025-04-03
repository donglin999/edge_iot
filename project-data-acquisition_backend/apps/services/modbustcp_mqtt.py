#!/usr/bin/env python
# -*- encoding: utf-8 -*-

# here put the import lib
import time
import threading
import queue
from apps.connect.connect_influx import InfluxClient, w_influx
from apps.connect.connect_modbustcp import ModbustcpClient
from apps.connect.connect_mqtt import MqttClient
from settings import DevelopmentConfig
from utils.baseLogger import Log
import datetime

class ModbustcpMQTT:
    def __init__(self, data_addresses):
        self.device_ip = data_addresses['source_ip']
        self.device_port = data_addresses['source_port']
        self.slave_addr = data_addresses['source_slave_addr']
        self.device_conf = data_addresses
        self.old_data = {}
        
    def modbustcp_mqtt(self):

        modbustcp_client = ModbustcpClient(self.device_ip, self.device_port)
        mqtt_client = MqttClient(self.device_conf).connect2()
        # influxdb_client = InfluxClient().connect()
        
        threads = []
        
        data_buff = queue.Queue(maxsize=1000)
        threads.append(threading.Thread(target=self.get_data, args=(data_buff, modbustcp_client, self.device_conf,
                                                                    self.slave_addr)))
        # 数据计算和存储
        # threads.append(threading.Thread(target=self.calc_and_save, args=(data_buff, influxdb_client)))
        threads.append(threading.Thread(target=self.calc_and_save, args=(data_buff, mqtt_client)))
        
        for thread in threads:
            thread.start()
    
    def get_data(self, data_buff, modbustcp_client, device_conf, slave_addr):

        while True:
            tag_data = modbustcp_client.read_modbustcp(device_conf, slave_addr)
            if "无法连接" in tag_data:
                Log().printError(f"{self.device_ip}:{self.device_port}无法连接")
                print(f"{self.device_ip}:{self.device_port}无法连接")
                time.sleep(10)
            else:
                for i in tag_data:
                    i['time'] = int(time.time_ns())
                    data_buff.put(i)

                time.sleep(2)
            try:
                pass

            except Exception as e:
                Log().printError(f"{self.device_ip}{self.device_port}get_data函数报错: {e}")
                print(f"{self.device_ip}{self.device_port}get_data函数报错: {e}")
                
    def calc_and_save(self, data_buff, mqtt_client):
        while True:
            try:
                tag_data = data_buff.get()
                addr = tag_data['addr']
                cn_name = tag_data['cn_name']
                part_name = tag_data['part_name']
                tag_data.pop('addr', None)
                tag_data.pop('cn_name', None)
                tag_data.pop('part_name', None)
                unit = tag_data['unit']
                tag_data.pop('unit', None)
                data_source = tag_data['data_source']
                tag_data.pop('data_source', None)
                device_a_tag = tag_data['device_a_tag']
                tag_data.pop('device_a_tag', None)
                device_name = tag_data['device_name']
                tag_data.pop('device_name', None)
                kafka_position = tag_data['kafka_position']
                tag_data.pop('kafka_position', None)

                influx_data = tag_data

                if influx_data == {}:
                    Log().printError("plc data " + device_name + " is null")
                else:
                    for k, v in influx_data.items():
                        if k != "time":
                            if k in self.old_data:
                                pass
                            else:
                                self.old_data[k] = 0
                            # print(f"{k}的当前值为{v}")
                            # print(f"{k}的旧值为{self.old_data[k]}")
                            if v == self.old_data[k]:
                                # print(f"{k}的值没变化不操作")
                                pass
                            else:
                                print(f"{k}的当前值为{v}")
                                print(f"{k}的旧值为{self.old_data[k]}")
                                print(f"{k}的值变化")
                                self.old_data[k] = v
                                # print(self.old_data)
                                # 获取当前的日期和时间
                                now = datetime.datetime.now()

                                # 打印原始的日期时间对象
                                # print("原始日期时间对象:", now)

                                # 格式化日期时间为字符串
                                formatted_now = now.strftime("%Y-%m-%d %H:%M:%S")

                                # 打印格式化的日期时间字符串
                                # print("格式化的日期时间字符串:", formatted_now)

                                # 将influx存储数据组织成对应的package存储格式
                                package = \
                                    {
                                        "measurement": device_a_tag,
                                        "tags":
                                            {
                                                "device_a_tag": device_a_tag,
                                                "device_name": device_name,
                                                "cn_name": cn_name,
                                                "addr": addr,
                                                "part_name": part_name,
                                                "unit": unit,
                                                "data_source": data_source,
                                                "time": formatted_now,
                                                "kafka_position": kafka_position
                                            },
                                        "fields": influx_data
                                    }
                                # json_body = [package]
                                # w_influx(influxdb_client, device_name, json_body)

                                mqtt_client.publish(DevelopmentConfig().MQTT_TOPIC, str(package))
                                print(f"数据{package}发送到{DevelopmentConfig().MQTT_TOPIC}主题成功")

            except Exception as e:
                Log().printError(f"{self.device_ip}{self.device_port}calc_and_save函数报错: {e}")
                print(f"{self.device_ip}{self.device_port}calc_and_save函数报错: {e}")
                influxdb_client = InfluxClient().connect()

        
    