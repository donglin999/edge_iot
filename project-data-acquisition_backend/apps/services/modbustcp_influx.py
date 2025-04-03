#!/usr/bin/env python
# -*- encoding: utf-8 -*-

# here put the import lib
import time
import threading
import queue

from apps.connect.connect_influx import InfluxClient, w_influx
from apps.connect.connect_modbustcp import ModbustcpClient
from utils.baseLogger import Log

class ModbustcpInflux:
    def __init__(self, data_addresses):
        self.device_ip = data_addresses['source_ip']
        self.device_port = data_addresses['source_port']
        self.slave_addr = data_addresses['source_slave_addr']
        self.device_conf = data_addresses
        
    def modbustcp_influx(self):

        modbustcp_client = ModbustcpClient(self.device_ip, self.device_port)
        # mqtt_client = MqttClient().connect(self.device_name)
        influxdb_client = InfluxClient().connect()
        
        threads = []
        
        data_buff = queue.Queue(maxsize=1000)
        threads.append(threading.Thread(target=self.get_data, args=(data_buff, modbustcp_client, self.device_conf,
                                                                    self.slave_addr,influxdb_client)))
        # 数据计算和存储
        threads.append(threading.Thread(target=self.calc_and_save, args=(data_buff, influxdb_client)))
        
        for thread in threads:
            thread.start()
    
    def get_data(self, data_buff, modbustcp_client, device_conf, slave_addr, influxdb_client):

        while True:
            try:
                tag_data = modbustcp_client.read_modbustcp(device_conf, slave_addr)
                if "无法连接" in tag_data:
                    Log().printError(f"{self.device_ip}:{self.device_port}无法连接")
                    print(f"{self.device_ip}:{self.device_port}无法连接")
                    for K, V in device_conf.items():
                        if isinstance(V, dict):
                            device_a_tag = device_conf['device_a_tag']
                            device_name = device_conf['device_name']

                    # print(V['source_addr'])
                    package = \
                        {
                            "measurement": "ART",
                            "tags":
                                {
                                    "device_a_tag": device_a_tag,
                                    "device_name": device_name,
                                    "cn_name": "runningstatus",
                                    "data_source": "ART",
                                    "kafka_position": "measures"
                                },
                            "fields": {"runningstatus": 4}
                        }
                    json_body = [package]
                    w_influx(influxdb_client, device_name, json_body)
                    time.sleep(10)
                else:
                    for i in tag_data:
                        i['time'] = int(time.time_ns())
                        data_buff.put(i)
                    time.sleep(0.1)

            except Exception as e:
                Log().printError(f"{self.device_ip}{self.device_port}get_data函数报错: {e}")
                print(f"{self.device_ip}{self.device_port}get_data函数报错: {e}")
                
    def calc_and_save(self, data_buff, influxdb_client):
        while True:
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
                                "kafka_position": kafka_position
                            },
                        "time": influx_data['time'],
                        "fields": influx_data
                    }
                json_body = [package]
                w_influx(influxdb_client, device_name, json_body)
                # print(f"{self.device_ip}{self.device_port}数据写入influxdb成功，json_body: {json_body}")
            try:
                pass

            except Exception as e:
                Log().printError(f"{self.device_ip}{self.device_port}calc_and_save函数报错: {e}")
                print(f"{self.device_ip}{self.device_port}calc_and_save函数报错: {e}")
                influxdb_client = InfluxClient().connect()

        
    