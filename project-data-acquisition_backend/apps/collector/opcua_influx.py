#!/usr/bin/env python
# -*- encoding: utf-8 -*-

import time
import threading
import queue
from datetime import datetime
import ctypes
import inspect
import copy
from apps.connect.connect_influx import InfluxClient, w_influx
from apps.connect.connect_opc import OpcClient
from apps.utils.baseLogger import Log


class OpcuaInflux:
    def __init__(self, device_data_addresses):
        """
        初始化OPC UA到InfluxDB服务
        :param device_data_addresses: 设备数据地址配置
        """
        # 构建OPC UA服务器URL
        self.register_config = {}
        self.data_queue = queue.Queue(maxsize=1000)
        if 'source_url' in device_data_addresses:
            self.server_url = device_data_addresses['source_url']
        elif 'source_ip' in device_data_addresses and 'source_port' in device_data_addresses:
            source_ip = device_data_addresses['source_ip']
            source_port = device_data_addresses['source_port']
            self.server_url = f'opc.tcp://{source_ip}:{source_port}'
        else:
            raise ValueError("配置中必须包含 'source_url' 或者 'source_ip' 和 'source_port'")
        try:
            for en_name, register_conf in device_data_addresses.items():
                if isinstance(register_conf, dict):
                    self.register_config[register_conf['source_addr']] = register_conf
        except Exception as e:
            print(f"{source_ip}初始化配置失败：{e}")

    def start_collector(self):
        """
        主函数
        """
        opc_client = OpcClient().connect(self.server_url, self.server_url)
        influxdb_client = InfluxClient().connect()
        threads = []
        threads.append(threading.Thread(target=self.calc_and_save, args=(influxdb_client,)))
        data_thread = threading.Thread(target=self.get_data, args=(opc_client,))
        threads.append(data_thread)
        for thread in threads:
            thread.start()

    def get_data(self, opc_client):
        package = {
            "measurement": "",
            "tags": {"cn_name": ""},
            "fields": {}
        }
        while True:
            try:
                for key, value in self.register_config.items():
                    try:
                        if key is not None:
                            data_package = copy.deepcopy(package)
                            injection_node = opc_client.get_node(key)
                            var_name = value['cn_name']
                            var_value = injection_node.get_value()
                            if isinstance(var_value, float):
                                var_value = round(var_value, 2)
                            data_package['fields'][var_name] = var_value
                            data_package['tags']['cn_name'] = var_name
                            data_package['measurement'] = value['device_a_tag']
                            try:
                                self.data_queue.put(data_package, timeout=1)
                            except queue.Full:
                                print("队列已满，丢弃数据包")
                                continue
                    except Exception as e:
                        # 判断是否为节点不存在的报错
                        if "The node id refers to a node that does not exist" in str(e) or "BadNodeIdUnknown" in str(e):
                            # 直接跳过，不重连，也不打印
                            continue
                        else:
                            print(f"获取数据时出错: {e}")
                            # 这里才做重连
                            try:
                                opc_client.disconnect()
                            except Exception:
                                pass
                            time.sleep(3)
                            try:
                                opc_client = OpcClient().connect(self.server_url, self.server_url)
                                print("OPC UA重连成功")
                            except Exception as e2:
                                print(f"OPC UA重连失败: {e2}")
                                time.sleep(5)
                            break  # 跳出for循环，重新开始while True
            except Exception as e:
                print(f"线程级别异常: {e}")
                time.sleep(5)

    def calc_and_save(self, influxdb_client):
        batch_data = []
        batch_size = 50
        while True:
            try:
                tag_data = self.data_queue.get(timeout=60)
                batch_data.append(tag_data)
                if len(batch_data) >= batch_size:
                    try:
                        w_influx(influxdb_client, "", batch_data)
                        batch_data = []
                    except Exception as e:
                        print(f"上传数据到InfluxDB失败: {e}")
                        # 上传失败，重连InfluxDB
                        try:
                            influxdb_client.close()
                        except Exception:
                            pass
                        time.sleep(3)
                        try:
                            influxdb_client = InfluxClient().connect()
                            print("InfluxDB重连成功")
                        except Exception as e2:
                            print(f"InfluxDB重连失败: {e2}")
                            time.sleep(5)
            except queue.Empty:
                if batch_data:
                    try:
                        w_influx(influxdb_client, "", batch_data)
                        batch_data = []
                    except Exception as e:
                        print(f"上传数据到InfluxDB失败: {e}")
                        try:
                            influxdb_client.close()
                        except Exception:
                            pass
                        time.sleep(3)
                        try:
                            influxdb_client = InfluxClient().connect()
                            print("InfluxDB重连成功")
                        except Exception as e2:
                            print(f"InfluxDB重连失败: {e2}")
                            time.sleep(5)
            except Exception as e:
                print(f"calc_and_save线程级别异常: {e}")
                time.sleep(5)





