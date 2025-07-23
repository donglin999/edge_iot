#!/usr/bin/env python
# -*- encoding: utf-8 -*-
'''
@File    :   connect_melseca1enet.py
@Time    :   2024/03/12 
@Author  :   AI Assistant
@Version :   1.0
@Desc    :   三菱A1E系列PLC连接模块
'''

import json
import re
import time
import struct
import gc
import psutil
from kafka import KafkaProducer
from lib.HslCommunication import MelsecA1ENet
from apps.connect.connect_influx import w_influx, InfluxClient
from settings import DevelopmentConfig
from utils.baseLogger import Log

def circular_shift_left(value, shift):
    bit_size = 32  # 32位整数
    # 计算实际需要移动的位数，因为移动32位相当于没有移动
    shift = shift % bit_size
    # 进行循环左移
    return ((value << shift) | (value >> (bit_size - shift))) & ((1 << bit_size) - 1)

class MemoryMonitor:
    """内存监控器"""
    
    def __init__(self, threshold_mb=100, log_interval=1000):
        self.threshold_mb = threshold_mb
        self.log_interval = log_interval
        self.process = psutil.Process()
        self.operation_count = 0
        self.last_memory = 0
        
    def check_memory(self, force_gc=False):
        """检查内存使用"""
        self.operation_count += 1
        
        try:
            # 获取当前内存使用
            current_memory = self.process.memory_info().rss / 1024 / 1024  # MB
            
            # 检查是否超过阈值
            if current_memory > self.threshold_mb:
                Log().printWarning(f"内存使用较高: {current_memory:.2f}MB")
                gc.collect()
                
                # 重新检查
                after_gc = self.process.memory_info().rss / 1024 / 1024
                freed = current_memory - after_gc
                if freed > 1:
                    Log().printInfo(f"垃圾回收释放了 {freed:.2f}MB 内存")
            
            # 定期日志记录
            if self.operation_count % self.log_interval == 0:
                memory_increase = current_memory - self.last_memory if self.last_memory > 0 else 0
                Log().printInfo(f"内存监控: 当前 {current_memory:.2f}MB, 增长 {memory_increase:.2f}MB")
                self.last_memory = current_memory
            
            # 强制垃圾回收
            if force_gc or self.operation_count % (self.log_interval // 10) == 0:
                gc.collect()
                
            return current_memory
            
        except Exception as e:
            Log().printError(f"内存监控异常: {e}")
            return 0
    
    def get_memory_stats(self):
        """获取内存统计"""
        try:
            memory_info = self.process.memory_info()
            return {
                'rss_mb': memory_info.rss / 1024 / 1024,
                'vms_mb': memory_info.vms / 1024 / 1024,
                'percent': self.process.memory_percent(),
                'operation_count': self.operation_count
            }
        except Exception as e:
            Log().printError(f"获取内存统计异常: {e}")
            return {}

class MelsecA1ENetClient:
    def __init__(self, ip, port, plc_number=0) -> None:
        """
        初始化MelsecA1ENet客户端
        
        Args:
            ip: PLC的IP地址
            port: PLC的端口号
            device_a_tag: 设备A码
            device_name: 设备名称
            plc_number: PLC站号，默认为0
        """
        self.ip = ip
        self.port = port
        # self.device_a_tag = device_a_tag
        # self.device_name = device_name
        self.plc_number = plc_number
        
        # 初始化Kafka连接（如果启用）
        if DevelopmentConfig().KAFKA_ENABLED:
            self.kafka_producer = KafkaProducer(
                bootstrap_servers=DevelopmentConfig().kafka_bootstrap_servers,
                value_serializer=lambda x: json.dumps(x).encode('utf-8')
            )
            print(f"kafka连接成功，{DevelopmentConfig().kafka_bootstrap_servers}")
            Log().printInfo(f"kafka连接成功，{DevelopmentConfig().kafka_bootstrap_servers}")
            
        # 初始化InfluxDB连接
        self.influxdb_client = InfluxClient().connect()
        Log().printInfo(f"influxdb对象创建成功")
        
        # 初始化MelsecA1ENet连接
        self.plc = MelsecA1ENet(self.ip, self.port)
        self.plc.ConnectServer()
        Log().printInfo(f"MelsecA1ENet连接成功，IP: {self.ip}, 端口: {self.port}")
        print(f"MelsecA1ENet连接成功，IP: {self.ip}, 端口: {self.port}")
        self.count = 0
        
        # 添加内存管理配置
        self.max_cache_size = 100  # 限制缓存大小
        self.cleanup_interval = 50  # 清理间隔
        self.operation_count = 0   # 操作计数器
        self.memory_monitor = MemoryMonitor(threshold_mb=150, log_interval=100)
        # print(f"尝试读数据")
        # result = self.plc.ReadInt16("D5000", 1).Content[0]
        # print(f"result:{result}")

    def contains_alpha_or_digit(self, s):
        """检查字符串是否包含字母或数字"""
        # 检查是否包含字母
        contains_alpha = any(char.isalpha() for char in s)
        # 检查是否包含数字
        contains_digit = any(char.isdigit() for char in s)

        # 如果包含字母或数字，就打印消息
        if contains_alpha or contains_digit:
            print(f"{s}变量包含字母或数字")
        return contains_alpha or contains_digit

    def __del__(self):
        """析构函数 - 确保资源释放"""
        try:
            # 关闭PLC连接
            if hasattr(self, 'plc') and self.plc:
                try:
                    self.plc.ConnectClose()
                except:
                    pass  # 忽略关闭时的异常
                    
            # 关闭InfluxDB连接
            if hasattr(self, 'influxdb_client') and self.influxdb_client:
                try:
                    if hasattr(self.influxdb_client, 'close'):
                        self.influxdb_client.close()
                except:
                    pass
                    
            # 关闭Kafka连接
            if hasattr(self, 'kafka_producer') and self.kafka_producer:
                try:
                    self.kafka_producer.close()
                except:
                    pass
                
            Log().printInfo("MelsecA1ENetClient 资源已释放")
        except Exception as e:
            Log().printError(f"资源释放异常: {e}")
    
    def safe_reconnect(self):
        """安全重连方法"""
        try:
            # 1. 先关闭旧连接
            if hasattr(self, 'plc') and self.plc:
                try:
                    self.plc.ConnectClose()
                except:
                    pass  # 忽略关闭异常
                finally:
                    self.plc = None
            
            # 2. 强制垃圾回收
            gc.collect()
            
            # 3. 创建新连接
            self.plc = MelsecA1ENet(self.ip, self.port)
            result = self.plc.ConnectServer()
            
            if result.IsSuccess:
                Log().printInfo(f"PLC重连成功: {self.ip}:{self.port}")
                return True
            else:
                Log().printError(f"PLC重连失败: {result.Message}")
                return False
                
        except Exception as e:
            Log().printError(f"重连异常: {e}")
            return False
    
    def memory_cleanup(self):
        """内存清理方法"""
        try:
            # 强制垃圾回收
            gc.collect()
            
            # 清理可能的缓存数据
            if hasattr(self, 'read_cache'):
                self.read_cache.clear()
            if hasattr(self, 'write_cache'):
                self.write_cache.clear()
                
            Log().printInfo("内存清理完成")
        except Exception as e:
            Log().printError(f"内存清理异常: {e}")

    def read_plc(self, register_dict):
        """
        优化的PLC读取方法
        
        Args:
            register_dict: 寄存器配置字典
            
        Returns:
            list: 读取到的数据列表
        """
        try:
            # 增加操作计数
            self.operation_count += 1
            
            # 定期内存清理
            if self.operation_count % self.cleanup_interval == 0:
                self.memory_cleanup()
            
            # 监控内存
            self.memory_monitor.check_memory()
            
            tag_data = []
            
            # 预分配基础数据结构，减少重复创建
            base_data = {
                'kafka_position': '',
                'cn_name': '',
                'device_a_tag': '',
                'device_name': ''
            }
            
            for en_name, register_conf in register_dict.items():
                if not isinstance(register_conf, dict):
                    continue
                    
                try:
                    # 复用基础结构
                    plc_data = base_data.copy()
                    plc_data.update({
                        'kafka_position': register_conf.get('kafka_position', ''),
                        'cn_name': register_conf.get('cn_name', ''),
                        'device_a_tag': register_conf.get('device_a_tag', ''),
                        'device_name': register_conf.get('device_name', '')
                    })
                    
                    # 读取数据
                    value = self._read_register_value(en_name, register_conf)
                    plc_data[en_name] = value
                    
                    tag_data.append(plc_data)
                    
                except Exception as e:
                    addr = register_conf.get('source_addr', 'unknown')
                    Log().printError(f"读取地址 {addr} 异常: {e}")
                    continue
            
            return tag_data

        except Exception as e:
            # 使用安全重连
            Log().printError(f"读取PLC数据异常: {e}")
            if self.safe_reconnect():
                Log().printInfo("重连成功，下次调用将重试")
            return []
        
        finally:
            # 大批量数据时强制垃圾回收
            if len(tag_data) > self.max_cache_size:
                gc.collect()

    def _read_register_value(self, en_name, register_conf):
        """优化的寄存器读取方法"""
        addr = register_conf['source_addr']
        num = int(register_conf['num'])
        data_type = register_conf['type']
        coefficient = register_conf.get('coefficient', 1)
        precision = int(register_conf.get('precision', 0))
        
        try:
            if data_type == 'str':
                result = self.plc.ReadString(addr, num)
                if result.IsSuccess:
                    content = result.Content
                    if en_name == "codeResult":
                        # 优化字符串处理，减少中间对象
                        return self._process_code_result(content)
                    else:
                        return str(content)
                return "ReadError"
                
            elif data_type == 'int16':
                result = self.plc.ReadInt16(addr, num)
                if result.IsSuccess and result.Content:
                    return round(result.Content[0] * coefficient, precision)
                return 0
                
            elif data_type == 'int32':
                result = self.plc.ReadInt32(addr, num)
                if result.IsSuccess and result.Content:
                    return round(result.Content[0] * coefficient, precision)
                return 0
                
            elif data_type == 'float':
                result = self.plc.ReadFloat(addr, num)
                if result.IsSuccess and result.Content:
                    return round(result.Content[0] * coefficient, precision)
                return 0.0
                
            elif data_type == 'float2':
                result = self.plc.ReadUInt32(addr, num)
                if result.IsSuccess and result.Content:
                    value = result.Content[0]
                    value2 = circular_shift_left(value, 16)
                    value3 = struct.unpack('<f', struct.pack('<I', value2))[0]
                    return round(value3, precision)
                return 0.0
                
            elif data_type == 'bool':
                result = self.plc.ReadBool(addr, num)
                if result.IsSuccess and result.Content:
                    return int(result.Content[0])
                return 0
                
            elif data_type == 'hex':
                result = self.plc.ReadUInt32(addr, num)
                if result.IsSuccess and result.Content:
                    return hex(result.Content[0])
                return "0x0"
                
            else:
                Log().printWarning(f"未知数据类型: {data_type}")
                return None
                
        except Exception as e:
            Log().printError(f"读取 {addr} ({data_type}) 异常: {e}")
            return None

    def _process_code_result(self, content):
        """优化的代码结果处理"""
        try:
            if not content or len(content) < 64:
                return "None"
            
            # 一次性完成字符串处理，减少中间对象
            processed = content[4:64]
            
            # 使用更高效的字符检查
            if any(c.isalnum() for c in processed):
                # 使用translate替代正则表达式
                whitespace_trans = str.maketrans('', '', ' \t\n\r')
                return processed.translate(whitespace_trans)
            else:
                return "None"
                
        except Exception as e:
            Log().printError(f"字符串处理异常: {e}")
            return "ProcessError"

    def write_plc(self, register_dict):
        """
        优化的PLC写入方法
        
        Args:
            register_dict: 寄存器配置字典
        """
        # 确保连接成功，设置最大重试次数避免无限循环
        max_retries = 5
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                if not self.plc.ConnectServer().IsSuccess:
                    Log().printError(f"PLC连接失败，正在重试... ({retry_count + 1}/{max_retries})")
                    retry_count += 1
                    time.sleep(1)
                    continue
                else:
                    break
            except Exception as e:
                Log().printError(f"PLC连接异常: {e}")
                retry_count += 1
                if retry_count >= max_retries:
                    Log().printError("PLC连接失败，超过最大重试次数")
                    return False
                time.sleep(1)
        
        if retry_count >= max_retries:
            Log().printError("PLC连接失败，无法执行写入操作")
            return False
        
        # 监控内存
        self.memory_monitor.check_memory()
        
        success_count = 0
        total_count = len(register_dict)
        
        # 遍历寄存器配置，写入数据
        for register_name, register_conf in register_dict.items():
            try:
                num = register_conf['num']
                addr = register_conf['addr']
                value = register_conf['value']
                
                # 根据不同的数据类型写入数据
                if register_conf['type'] == 'str':
                    result = self.plc.WriteUnicodeString(addr, value, num)
                elif register_conf['type'] == 'int16':
                    result = self.plc.WriteInt16(addr, value)
                elif register_conf['type'] == 'int32':
                    result = self.plc.WriteInt32(addr, value)
                elif register_conf['type'] == 'float':
                    result = self.plc.WriteFloat(addr, value)
                elif register_conf['type'] == 'bool':
                    result = self.plc.WriteBool(addr, value)
                else:
                    Log().printError(f"不支持的写入数据类型: {register_conf['type']}")
                    continue
                
                if hasattr(result, 'IsSuccess') and result.IsSuccess:
                    success_count += 1
                    Log().printInfo(f"写入PLC地址: {addr}, 值: {value}, 类型: {register_conf['type']} 成功")
                else:
                    Log().printError(f"写入PLC地址: {addr} 失败")
                    
            except Exception as e:
                Log().printError(f'写入PLC {register_name} 失败: {e}')
                print(f'写入PLC {register_name} 失败: {e}')
        
        # 确保连接正确关闭
        try:
            self.plc.ConnectClose()
        except Exception as e:
            Log().printError(f"关闭PLC连接异常: {e}")
        
        Log().printInfo(f"写入操作完成: {success_count}/{total_count} 成功")
        return success_count == total_count

if __name__ == "__main__":
    # 测试代码
    ip = "192.168.3.251"
    port = 4998
    device_a_tag = "A_test"
    device_name = "test_device"
    plc_number = 0
    
    # 创建MelsecA1ENet客户端
    melsec_client = MelsecA1ENetClient(ip, port, plc_number)
    
    # 测试寄存器配置
    register_dict = {
        "en_name": {
            'num': 1,
            'source_addr': "D100",
            'coefficient': 1,
            'kafka_position': "meatear",
            'precision': 2,
            'type': "int16",
            'cn_name': "test1",
            'device_a_tag': device_a_tag,
            'device_name': device_name
        }
    }
    
    # 添加退出条件的循环读取数据
    max_iterations = 1000  # 最大迭代次数
    iteration_count = 0
    
    try:
        while iteration_count < max_iterations:
            try:
                tag_data = melsec_client.read_plc(register_dict)
                print(f"读取数据 #{iteration_count}: {tag_data}")
                
                # 检查内存使用
                if iteration_count % 100 == 0:
                    stats = melsec_client.memory_monitor.get_memory_stats()
                    print(f"内存统计: {stats}")
                
                iteration_count += 1
                time.sleep(1)
                
            except KeyboardInterrupt:
                print("\\n用户中断，正在退出...")
                break
            except Exception as e:
                Log().printError(f"主循环异常: {e}")
                time.sleep(5)  # 异常后等待5秒再重试
                
    except Exception as e:
        Log().printError(f"程序异常: {e}")
    finally:
        # 确保资源清理
        try:
            del melsec_client
            print("资源清理完成")
        except Exception as e:
            print(f"资源清理异常: {e}")
    
    print("程序结束")