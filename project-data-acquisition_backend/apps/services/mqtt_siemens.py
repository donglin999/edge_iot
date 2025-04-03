#!/usr/bin/env python
# -*- encoding: utf-8 -*-

import json
import queue
import threading
from apps.connect.connect_mqtt import MqttClient
from apps.connect.connect_siemens import ConnectSiemens

class MqttSiemens:
    def __init__(self, data_addresses):
        self.data_addresses = data_addresses
        self.device_a_tag_dic = {}
        self.en_name_dic = {}
        self.cn_name_dic = {}
        self.plc_addr = {}
        self.addr_type = {}
        if data_addresses['protocol_type'] == 'MQTT_SIEMENS':
            self.device_a_tag_dic[data_addresses['device_a_tag']] = data_addresses['device_name']
            self.plc_addr[data_addresses['device_a_tag']] = {}
            self.addr_type[data_addresses['device_a_tag']] = {}
            for k1, v1 in data_addresses.items():
                if isinstance(v1, dict):
                    self.en_name_dic[v1['en_name']] = v1['cn_name']
                    self.cn_name_dic[v1['en_name']] = v1['cn_name']
                    self.plc_addr[data_addresses['device_a_tag']][v1['en_name']] = v1['source_addr']
                    self.addr_type[data_addresses['device_a_tag']][v1['en_name']] = v1['type']
        else:
            for k, v in self.data_addresses.items():
                if isinstance(v, dict):
                    self.device_a_tag_dic[v['device_a_tag']] = v['device_name']
                    self.plc_addr[v['device_a_tag']] = {}
                    self.addr_type[v['device_a_tag']] = {}
                    for k1, v1 in v.items():
                        if isinstance(v1, dict):
                            self.en_name_dic[v1['en_name']] = v1['cn_name']
                            self.cn_name_dic[v1['en_name']] = v1['cn_name']
                            self.plc_addr[v['device_a_tag']][v1['en_name']] = v1['source_addr']
                            self.addr_type[v['device_a_tag']][v1['en_name']] = v1['type']

        print(f"self.plc_addr:{self.plc_addr}")
        print(f"self.addr_type:{self.addr_type}")
        print(f"self.device_a_tag_dic:{self.device_a_tag_dic}")
        print(f"self.en_name_dic:{self.en_name_dic}")
        self.old_data = {}
        self.points = []
        self.plc = ConnectSiemens()
        self.data_buff = queue.Queue(maxsize=1000)

    def mqtt_siemens(self):
        threads = [threading.Thread(target=self.mqtt_cpu, args=(self.data_addresses,)),
                   threading.Thread(target=self.cpu_siemens, args=(self.data_buff,))]

        # 数据计算和存储
        for thread in threads:
            thread.start()

    def mqtt_cpu(self, data_addresses):
        mqtt_client = MqttClient(data_addresses).connect()
        # print(f"连接mqtt服务器完成")
        mqtt_client.on_message = self.get_data
        mqtt_client.loop_forever()

    def get_data(self, client, userdata, msg):
        msg_payload_dic = json.loads(str(msg.payload.decode("utf-8")))
        device_a_tag = msg_payload_dic['data']['deviceCode']
        en_name = msg_payload_dic['data']['propertyCode']
        print(f"msg_payload_dic:{msg_payload_dic}")
        if device_a_tag in self.device_a_tag_dic:
            if en_name in self.en_name_dic:
                # print(f"msg_payload_dic:{msg_payload_dic}")
                try:
                    value = float(msg_payload_dic['data']['propertyValue'])
                except Exception as e:
                    if msg_payload_dic['data']['propertyValue'] == True:
                        value = 1
                    elif msg_payload_dic['data']['propertyValue'] == False:
                        value = 0
                    else:
                        value = str(msg_payload_dic['data']['propertyValue'])
                date = {"addr": self.plc_addr[device_a_tag][en_name],
                        "type": self.addr_type[device_a_tag][en_name],
                        "value": value}
                self.data_buff.put(date)

    def cpu_siemens(self, data_buff):
        while True:
            data = data_buff.get()
            print(f"从队列拿到的数据{data}")
            self.plc.write(data['addr'], data['type'], data['value'])
            print(f"将数据写入PLC完成，{data}")

