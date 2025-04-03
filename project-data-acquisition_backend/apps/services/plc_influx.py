#!/usr/bin/env python
# -*- encoding: utf-8 -*-
'''
@File    :   collector_kafka.py
@Time    :   2023/05/11 15:11:40
@Author  :   Jason Jiangfeng 
@Version :   1.0
@Contact :   jiangfeng24@midea.com
@Desc    :   获取kafka数据
'''

# here put the import lib
import time
import threading
import queue

from apps.connect.connect_influx import InfluxClient, w_influx
from apps.connect.connect_plc import PLCClient
from utils.baseLogger import Log


class PlcInflux:
    def __init__(self, device_data_addresses):
        self.device_ip = device_data_addresses['source_ip']
        self.device_port = device_data_addresses['source_port']
        self.device_data_addresses = device_data_addresses
        self.device_fs = device_data_addresses['fs']
        self.device_a_tag = device_data_addresses['device_a_tag']
        self.device_name = device_data_addresses['device_name']

    def plc_influx(self):
        """
        主函数
        """
        plc_client = PLCClient(self.device_ip, self.device_port, self.device_a_tag, self.device_name)
        # mqtt_client = MqttClient().connect(self.device_name)
        influxdb_client = InfluxClient().connect()

        threads = []

        data_buff = queue.Queue(maxsize=100)
        threads.append(threading.Thread(target=self.get_data, args=(data_buff, plc_client, self.device_data_addresses)))
        # 数据计算和存储
        threads.append(threading.Thread(target=self.calc_and_save, args=(data_buff, influxdb_client)))

        for thread in threads:
            thread.start()

    def get_data(self, data_buff, plc_client, device_conf):
        while True:

            try:
                tag_data = plc_client.read_plc(device_conf)
                # print(f"从{self.device_ip}plc读到的数据tag_data：{tag_data}")
                if tag_data:
                    for i in tag_data:
                        i['time'] = int(time.time_ns())

                        data_buff.put(i)

                time.sleep(self.device_fs)

            except Exception as e:
                # Log().printError(f"从{self.device_ip}拿数据报错：{e}")
                # print(f"从{self.device_ip}拿数据报错：{e}")
                continue

    def calc_and_save(self, data_buff, influxdb_client):
        while True:
            try:
                tag_data = data_buff.get()

                kafka_position = tag_data['kafka_position']
                cn_name = tag_data['cn_name']
                tag_data.pop('kafka_position', None)
                tag_data.pop('cn_name', None)

                influx_data = tag_data

                if influx_data == {}:
                    Log().printError("plc data " + self.device_name + " is null")
                else:
                    # 将influx存储数据组织成对应的package存储格式
                    package = \
                        {
                            "measurement": self.device_a_tag,
                            "tags":
                                {
                                    "device_a_tag": self.device_a_tag,
                                    "device_name": self.device_name,
                                    "kafka_position": kafka_position,
                                    "cn_name": cn_name
                                },
                            "time": influx_data['time'],
                            "fields": influx_data
                        }
                    json_body = [package]

                    w_influx(influxdb_client, self.device_name, json_body)

            except Exception as e:
                Log().printError(f"{self.device_name}, calc_and_save error e: {e}")
                print(f"{self.device_name}, calc_and_save error e: {e}")
                influxdb_client = InfluxClient().connect()

            # mqtt数据发送的topic组织成："工厂/设备类型/A码/设备名/opc"的格式
            # json_data = json.dumps(mqtt_data)
            # pub_mqtt(mqtt_client,
            #         getconfig('factory') + '/' +
            #         getconfig('device') + '/' +
            #         self.device_a_tag + '/' +
            #         self.device_name + '/kafka', json_data)

