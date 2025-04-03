#!/usr/bin/env python
# -*- encoding: utf-8 -*-
'''
@File    :   collector_e_motor.py
@Time    :   2023/05/05 14:08:22
@Author  :   Jason Jiangfeng 
@Version :   1.0
@Contact :   jiangfeng24@midea.com
@Desc    :   collector_e_motor data
'''

# here put the import lib
import time
import json
from baseFunc.baseLogger import Log
from baseFunc.util import pub_mqtt, getconfig, w_influx, getcrc, get_timestamp
from connect.connect_mqtt import MqttClient
from connect.connect_influx import InfluxClient

class CollectorEMotor:
    def __init__(self, device_id, device_name_en, device_name_cn, vib_id, current_id, client_socket, server_socket, server_addr) -> None:
        self.device_id = device_id
        self.device_name_en = device_name_en
        self.device_name_cn = device_name_cn
        self.vib_id = vib_id
        self.current_id = current_id
        self.client_socket = client_socket
        self.server_socket = server_socket
        self.server_addr = server_addr
        
    def start_collect(self):
        """
        主函数
        """
        # mqtt_client = MqttClient().connect(self.device_id)
        influxdb_client = InfluxClient().connect()
        while True:
            try:
                #循环读取modbus数据，并发送mqtt和存储influxdb
                rc = self.get_data(self.client_socket, self.server_socket, self.server_addr, influxdb_client)
            except Exception as e:
                # 采集中异常情况间隔3s进行报警并进行重连和重试
                Log().printError(self.device_id + ':=================>')
                Log().printError(e)
                # mqtt_client = MqttClient().connect(self.device_id)
                influxdb_client = InfluxClient().connect()
                time.sleep(3)
                continue
    
    
    def get_data(self, client_socket, server_socket, server_addr, influxdb_client):
        """获取zigbee连接的温振和电流模块的数据

        Args:
            client_socket (socket): PC
            server_socket (socket): zigbee
            server_addr (tuple): zigbee ip 端口
            mqtt_client (socket): mqtt
            influxdb_client (socket): influx

        Returns:
            int: 0:正常返回代码
                 1:异常结束，无数据
        """
        cmd_v = getconfig('cmd_v')
        cmd_c = getconfig('cmd_c')
        
        if self.vib_id != 0:
            for item in cmd_v:
                cmd = item['cmd']
                id_cmd = str(self.vib_id) + cmd
                msg = bytes.fromhex(getcrc(id_cmd))
                server = client_socket.sendto(msg, server_addr)
                receive_data, client = server_socket.recvfrom(1024)
                data1 = receive_data.hex()
                rc = self.parse(data1, influxdb_client)
                
        if self.current_id != "0":
            for item in cmd_c:
                cmd = item['cmd']
                id_cmd = self.current_id + cmd
                msg = bytes.fromhex(getcrc(id_cmd))
                server = client_socket.sendto(msg, server_addr)
                receive_data, client = server_socket.recvfrom(1024)
                data2 = receive_data.hex()
                rc = self.parse(data2, influxdb_client)
        
        return rc
    
    def parse(self, data, influxdb_client):
        # 振动数据
        if len(data) == 22 and data[4:6] == '06' :
            influx_data = {}
            mqtt_data = {}
            name = 'vib_speed'
            v = ['vx', 'vy', 'vz']
            data_start = 6
            data_range = 4
            for i in range(len(v)):
                d = int(data[data_start:data_start + data_range],16)/10
                influx_data, mqtt_data = data_append(influx_data, mqtt_data, name, v[i], d)
                data_start += data_range
            
            devicemap = getjson('modbus_input.json')["device_map"]
            for item in devicemap:
                if str(item['vib_id']) == data[:2]:
                    influx_id = item['device_id']
                    break
            
            package = \
                {
                    "measurement": getconfig('measurement'),
                    "tags":
                        {
                            "location": getconfig('location'),
                            "factory": getconfig('factory'),
                            "device": getconfig('device'),
                            "machine_id":'em-' + influx_id
                        },
                    "fields": influx_data
                }
            json_body = [package]
            w_influx(influxdb_client, influx_id, json_body)
        #温度数据和电流数据
        elif len(data) == 14 and data[4:6] == '02':
            influx_data = {}
            mqtt_data = {}
            id = int(data[:2],16)
            if id < 83:
                name = 'current'
                point_id = 'current_id'
            else:
                name = 'temp'
                point_id = 'vib_id'
            data_start = 6
            data_range = 4
            d = int(data[data_start:data_start + data_range],16)/100
            influx_data, mqtt_data = data_append(influx_data, mqtt_data, name, 'real', d)
            
            devicemap = getjson('modbus_input.json')["device_map"]
            for item in devicemap:
                if str(item[point_id]) == data[:2]:
                    influx_id = item['device_id']
                    break
                
            package = \
                {
                    "measurement": getconfig('measurement'),
                    "tags":
                        {
                            "location": getconfig('location'),
                            "factory": getconfig('factory'),
                            "device": getconfig('device'),
                            "machine_id":'em-' + influx_id
                        },
                    "fields": influx_data
                }
            json_body = [package]
            w_influx(influxdb_client, influx_id, json_body)
            
        return 0
    
def data_append(influx_data, mqtt_data, name, value_name, value):
    """组织成存储influx的data格式和发送mqtt的data格式

    Args:
        influx_data (dict): 将要存储到influxdb的数据
        mqtt_data (dict): 将要发送到mqtt的数据
        name (_type_): 数据名
        value_name (_type_): 分量名
        value (_type_): 数据

    Returns:
        dict, dict: 已经整理好的influxdb和mqtt数据
    """
    influx_data[name + '_' + value_name] = value
    mqtt_data[name + '_' + value_name] = {"value": value, "timestamp": get_timestamp(), "quality": 192}
    return influx_data, mqtt_data