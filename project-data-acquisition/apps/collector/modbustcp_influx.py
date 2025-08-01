#!/usr/bin/env python
# -*- encoding: utf-8 -*-

# here put the import lib
import time
import threading
import queue
from datetime import datetime
import ctypes
import inspect
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from logs.log_config import get_logger

from apps.connect.connect_influx import InfluxClient, w_influx
from apps.connect.connect_modbustcp import ModbustcpClient
from apps.utils.baseLogger import Log

# 获取专用日志器
logger = get_logger("data-acquisition", "collector", "modbustcp_influx")


def _async_raise(tid, exctype):
    """强制终止线程"""
    if not inspect.isclass(exctype):
        exctype = type(exctype)
    res = ctypes.pythonapi.PyThreadState_SetAsyncExc(ctypes.c_long(tid), ctypes.py_object(exctype))
    if res == 0:
        raise ValueError("无效的线程ID")
    elif res != 1:
        ctypes.pythonapi.PyThreadState_SetAsyncExc(ctypes.c_long(tid), None)
        raise SystemError("PyThreadState_SetAsyncExc 失败")


class ModbustcpInflux:
    def __init__(self, device_data_addresses):
        self.device_ip = device_data_addresses['source_ip']
        self.device_port = device_data_addresses['source_port']
        self.slave_addr = device_data_addresses.get('source_slave_addr', 1)
        self.device_conf = device_data_addresses
        self.device_fs = device_data_addresses.get('fs', 1)
        self.last_data_time = datetime.now()
        self.data_thread = None
        self.is_running = True
        self.data_buff = queue.Queue(maxsize=1000)
        logger.info(f"Modbus TCP设备IP：{self.device_ip}：{self.device_port}")
        Log().printInfo(f"Modbus TCP设备IP：{self.device_ip}：{self.device_port}")

    def modbustcp_influx(self):
        """
        主函数
        """
        modbustcp_client = ModbustcpClient(self.device_ip, self.device_port, self.device_conf)
        influxdb_client = InfluxClient().connect()

        threads = []

        self.data_thread = threading.Thread(target=self.get_data,
                                            args=(modbustcp_client,))
        threads.append(self.data_thread)
        # 数据计算和存储
        threads.append(threading.Thread(target=self.calc_and_save, args=(influxdb_client,)))

        for thread in threads:
            thread.start()
            
        # 等待线程结束
        try:
            for thread in threads:
                thread.join()
        except KeyboardInterrupt:
            self.stop()
            Log().printInfo(f"Modbus TCP设备 {self.device_ip} 采集进程已停止")

    def force_stop_thread(self, thread):
        """强制停止线程"""
        if thread and thread.is_alive():
            try:
                _async_raise(thread.ident, SystemExit)
                thread.join(timeout=1)
                Log().printInfo(f"Modbus TCP设备 {self.device_ip} 数据获取线程已强制终止")
            except Exception as e:
                Log().printError(f"强制终止线程失败: {e}")

    def restart_data_thread(self, device_conf):
        """重启数据获取线程"""
        # 强制终止旧线程
        if self.data_thread and self.data_thread.is_alive():
            self.force_stop_thread(self.data_thread)
        time.sleep(5)
        modbustcp_client = ModbustcpClient(self.device_ip, self.device_port)
        # 创建并启动新线程
        self.data_thread = threading.Thread(target=self.get_data, args=(modbustcp_client, device_conf, self.slave_addr))
        self.data_thread.start()
        Log().printInfo(f"Modbus TCP设备 {self.device_ip} 数据获取线程已重启")

    def get_data(self, modbustcp_client):
        """获取数据线程"""
        consecutive_errors = 0
        max_consecutive_errors = 5
        
        while self.is_running:
            try:
                tag_data = modbustcp_client.read_modbustcp()
                # 成功获取数据
                if tag_data:
                    consecutive_errors = 0  # 重置错误计数
                    for data_item in tag_data:
                        self.data_buff.put(data_item)
                    time.sleep(1)  # 成功读取后等待1秒
                else:
                    consecutive_errors += 1
                    Log().printWarning(f"Modbus TCP {self.device_ip}:{self.device_port} 未获取到数据，连续错误次数: {consecutive_errors}")
                    time.sleep(5)  # 没有数据时等待5秒
                    
            except Exception as e:
                consecutive_errors += 1
                Log().printError(f"Modbus TCP {self.device_ip}:{self.device_port} get_data函数报错: {e}")
                print(f"Modbus TCP {self.device_ip}:{self.device_port} get_data函数报错: {e}")
                
                # 如果连续错误次数过多，增加等待时间
                if consecutive_errors >= max_consecutive_errors:
                    Log().printWarning(f"Modbus TCP {self.device_ip}:{self.device_port} 连续错误次数过多，等待30秒后重试")
                    time.sleep(30)
                    consecutive_errors = 0  # 重置错误计数
                else:
                    time.sleep(10)  # 出错后等待10秒再重试

    def calc_and_save(self, influxdb_client):
        """计算和保存数据线程"""
        # 创建一个列表来存储积累的数据
        batch_data = []
        batch_size = 50  # 设置批量提交的数据量
        consecutive_empty_count = 0
        max_empty_count = 10

        while self.is_running:
            try:
                tag_data = self.data_buff.get(timeout=60)  # 设置60秒超时
                consecutive_empty_count = 0  # 重置空数据计数
                self.last_data_time = datetime.now()

                # 提取数据字段
                kafka_position = tag_data.get('kafka_position', '')
                cn_name = tag_data.get('cn_name', '')
                device_a_tag = tag_data.get('device_a_tag', self.device_ip)
                device_name = tag_data.get('device_name', f'ModbusTCP_{self.device_ip}')

                # 移除非数据字段
                influx_data = tag_data.copy()
                for key in ['kafka_position', 'cn_name', 'device_a_tag', 'device_name']:
                    influx_data.pop(key, None)

                if not influx_data:
                    Log().printError("Modbus TCP data " + device_name + " is null")
                else:
                    # 将influx存储数据组织成对应的package存储格式
                    package = {
                        "measurement": device_a_tag,
                        "tags": {
                            "kafka_position": kafka_position,
                            "cn_name": cn_name,
                            "device_ip": self.device_ip,
                            "device_port": str(self.device_port)
                        },
                        "fields": influx_data
                    }

                    # 将数据添加到批处理列表中
                    batch_data.append(package)

                    # 当积累的数据达到指定数量时，一次性提交
                    if len(batch_data) >= batch_size:
                        w_influx(influxdb_client, device_name, batch_data)
                        Log().printInfo(f"批量提交了 {len(batch_data)} 条Modbus TCP数据到InfluxDB")
                        batch_data = []

            except queue.Empty:
                consecutive_empty_count += 1
                Log().printWarning(f"Modbus TCP设备 {self.device_ip} 60秒未收到数据，连续空数据次数: {consecutive_empty_count}")
                
                # 如果连续多次没有数据，考虑重启数据获取线程
                if consecutive_empty_count >= max_empty_count:
                    Log().printWarning(f"Modbus TCP设备 {self.device_ip} 连续{max_empty_count}次未收到数据，准备强制重启数据获取线程")
                    self.restart_data_thread(self.device_conf)
                    consecutive_empty_count = 0
                continue
            except Exception as e:
                Log().printError(f"Modbus TCP {self.device_ip}:{self.device_port} calc_and_save函数报错: {e}")
                print(f"Modbus TCP {self.device_ip}:{self.device_port} calc_and_save函数报错: {e}")
                
                # 重新连接InfluxDB
                try:
                    influxdb_client = InfluxClient().connect()
                except Exception as reconnect_error:
                    Log().printError(f"重新连接InfluxDB失败: {reconnect_error}")
                    time.sleep(10)  # 连接失败时等待10秒
                    continue

                # 如果发生错误但已有积累的数据，尝试提交这些数据
                if batch_data:
                    try:
                        w_influx(influxdb_client, device_name, batch_data)
                        Log().printInfo(f"错误恢复后提交了 {len(batch_data)} 条Modbus TCP数据到InfluxDB")
                        batch_data = []
                    except Exception as e2:
                        Log().printError(f"Modbus TCP {self.device_ip} 尝试提交积累数据时出错: {e2}")
                
                time.sleep(5)  # 出错后等待5秒再继续

    def stop(self):
        """停止采集进程"""
        self.is_running = False
        Log().printInfo(f"正在停止Modbus TCP设备 {self.device_ip} 的采集进程...")
        
        # 强制停止数据线程
        if self.data_thread and self.data_thread.is_alive():
            self.force_stop_thread(self.data_thread)


if __name__ == "__main__":
    import json
    import sys
    import os
    
    # 获取配置文件路径
    config_file = None
    if len(sys.argv) > 1:
        config_file = sys.argv[1]
    else:
        # 默认配置文件路径
        config_file = "configs/modbus_设备1_config.json"
    
    if not os.path.exists(config_file):
        print(f"配置文件不存在: {config_file}")
        sys.exit(1)
    
    try:
        # 读取配置文件
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        logger.info(f"正在启动Modbus TCP数据采集进程...")
        logger.info(f"配置文件: {config_file}")
        logger.info(f"设备地址: {config['source_ip']}:{config['source_port']}")
        print(f"正在启动Modbus TCP数据采集进程...")
        print(f"配置文件: {config_file}")
        print(f"设备地址: {config['source_ip']}:{config['source_port']}")
        
        # 创建并启动采集器
        logger.info("创建ModbustcpInflux实例...")
        collector = ModbustcpInflux(config)
        logger.info("开始执行数据采集...")
        collector.modbustcp_influx()
        
    except Exception as e:
        error_msg = f"启动Modbus TCP采集进程失败: {e}"
        logger.error(error_msg)
        print(error_msg)
        import traceback
        logger.error(f"详细错误信息: {traceback.format_exc()}")
        print(f"详细错误信息: {traceback.format_exc()}")
        sys.exit(1) 