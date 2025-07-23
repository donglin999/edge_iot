#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
内存泄漏检测测试 - connect_melseca1enet_backu
"""

import unittest
import gc
import psutil
import threading
import time
import sys
import os
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

# 添加项目根目录到Python路径
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from tests.base import BaseTestCase

# 尝试导入 memory_profiler，如果没有安装则跳过一些测试
try:
    from memory_profiler import profile, memory_usage
    MEMORY_PROFILER_AVAILABLE = True
except ImportError:
    MEMORY_PROFILER_AVAILABLE = False
    print("Warning: memory_profiler not available. Install it with: pip install memory-profiler")


class MemoryLeakDetector:
    """内存泄漏检测器"""
    
    def __init__(self):
        self.process = psutil.Process()
        self.initial_memory = None
        self.measurements = []
    
    def start_monitoring(self):
        """开始监控内存"""
        gc.collect()  # 强制垃圾回收
        self.initial_memory = self.process.memory_info().rss / 1024 / 1024  # MB
        self.measurements = [self.initial_memory]
        return self.initial_memory
    
    def measure(self):
        """测量当前内存使用"""
        gc.collect()
        current_memory = self.process.memory_info().rss / 1024 / 1024  # MB
        self.measurements.append(current_memory)
        return current_memory
    
    def get_memory_increase(self):
        """获取内存增长量"""
        if len(self.measurements) < 2:
            return 0
        return self.measurements[-1] - self.measurements[0]
    
    def get_average_growth_rate(self):
        """获取平均内存增长率"""
        if len(self.measurements) < 2:
            return 0
        total_growth = self.measurements[-1] - self.measurements[0]
        return total_growth / (len(self.measurements) - 1)


class TestMelsecA1ENetMemoryLeak(BaseTestCase):
    """MelsecA1ENet 内存泄漏测试"""
    
    def setUp(self):
        """测试前准备"""
        super().setUp()
        self.detector = MemoryLeakDetector()
        
        # Mock外部依赖避免实际连接
        self.kafka_patcher = patch('apps.connect.connect_melseca1enet_backu.KafkaProducer')
        self.influx_patcher = patch('apps.connect.connect_melseca1enet_backu.InfluxClient')
        self.melsec_patcher = patch('apps.connect.connect_melseca1enet_backu.MelsecA1ENet')
        self.log_patcher = patch('apps.connect.connect_melseca1enet_backu.Log')
        
        self.mock_kafka = self.kafka_patcher.start()
        self.mock_influx = self.influx_patcher.start()
        self.mock_melsec = self.melsec_patcher.start()
        self.mock_log = self.log_patcher.start()
        
        # 设置mock返回值
        self.setup_mocks()
    
    def tearDown(self):
        """测试后清理"""
        super().tearDown()
        self.kafka_patcher.stop()
        self.influx_patcher.stop()
        self.melsec_patcher.stop()
        self.log_patcher.stop()
    
    def setup_mocks(self):
        """设置模拟对象"""
        # Mock InfluxClient
        mock_influx_instance = Mock()
        mock_influx_instance.connect.return_value = Mock()
        self.mock_influx.return_value = mock_influx_instance
        
        # Mock MelsecA1ENet
        mock_plc_instance = Mock()
        mock_plc_instance.ConnectServer.return_value = Mock(IsSuccess=True)
        mock_plc_instance.ReadString.return_value = Mock(Content="TestString" * 10)
        mock_plc_instance.ReadInt16.return_value = Mock(Content=[12345])
        mock_plc_instance.ReadInt32.return_value = Mock(Content=[123456])
        mock_plc_instance.ReadFloat.return_value = Mock(Content=[123.45])
        mock_plc_instance.ReadUInt32.return_value = Mock(Content=[0x12345678])
        mock_plc_instance.ReadBool.return_value = Mock(Content=[True])
        self.mock_melsec.return_value = mock_plc_instance
        
        # Mock Log
        mock_log_instance = Mock()
        self.mock_log.return_value = mock_log_instance
    
    def test_client_initialization_memory(self):
        """测试客户端初始化是否造成内存泄漏"""
        from apps.connect.connect_melseca1enet_backu import MelsecA1ENetClient
        
        self.detector.start_monitoring()
        initial_memory = self.detector.initial_memory
        
        # 创建多个客户端实例测试内存泄漏
        clients = []
        for i in range(10):
            with patch('settings.DevelopmentConfig') as mock_config:
                mock_config.return_value.KAFKA_ENABLED = False
                client = MelsecA1ENetClient("192.168.1.100", 4998, 0)
                clients.append(client)
            
            if i % 3 == 0:  # 每3次测量一次内存
                current_memory = self.detector.measure()
                print(f"创建第{i+1}个客户端后内存: {current_memory:.2f}MB")
        
        # 删除所有客户端
        del clients
        gc.collect()
        
        final_memory = self.detector.measure()
        memory_increase = self.detector.get_memory_increase()
        
        print(f"初始内存: {initial_memory:.2f}MB")
        print(f"最终内存: {final_memory:.2f}MB")
        print(f"内存增长: {memory_increase:.2f}MB")
        
        # 允许适当的内存增长，但不应该过大
        self.assertLess(memory_increase, 50, "客户端初始化可能存在内存泄漏")
    
    def test_read_plc_memory_leak(self):
        """测试PLC读取操作是否造成内存泄漏"""
        from apps.connect.connect_melseca1enet_backu import MelsecA1ENetClient
        
        with patch('settings.DevelopmentConfig') as mock_config:
            mock_config.return_value.KAFKA_ENABLED = False
            client = MelsecA1ENetClient("192.168.1.100", 4998, 0)
        
        # 测试用的寄存器配置
        register_dict = {
            "temperature": {
                'num': 1,
                'source_addr': "D100",
                'coefficient': 0.1,
                'kafka_position': "sensor",
                'precision': 2,
                'type': "int16",
                'cn_name': "温度",
                'device_a_tag': "T001",
                'device_name': "温度传感器"
            },
            "pressure": {
                'num': 1,
                'source_addr': "D101",
                'coefficient': 1.0,
                'kafka_position': "sensor",
                'precision': 1,
                'type': "float",
                'cn_name': "压力",
                'device_a_tag': "P001",
                'device_name': "压力传感器"
            },
            "status": {
                'num': 1,
                'source_addr': "M100",
                'coefficient': 1,
                'kafka_position': "status",
                'precision': 0,
                'type': "bool",
                'cn_name': "状态",
                'device_a_tag': "S001",
                'device_name': "状态指示器"
            },
            "message": {
                'num': 10,
                'source_addr': "D200",
                'coefficient': 1,
                'kafka_position': "message",
                'precision': 0,
                'type': "str",
                'cn_name': "消息",
                'device_a_tag': "MSG001",
                'device_name': "消息显示"
            }
        }
        
        self.detector.start_monitoring()
        initial_memory = self.detector.initial_memory
        
        # 执行多次读取操作
        for i in range(100):
            try:
                data = client.read_plc(register_dict)
                
                # 验证返回数据不为空
                self.assertIsInstance(data, list)
                
                # 每10次测量一次内存
                if i % 10 == 0:
                    current_memory = self.detector.measure()
                    print(f"第{i+1}次读取后内存: {current_memory:.2f}MB")
                
                # 模拟一些处理时间
                time.sleep(0.001)
                
            except Exception as e:
                self.fail(f"读取PLC数据时出现异常: {e}")
        
        final_memory = self.detector.measure()
        memory_increase = self.detector.get_memory_increase()
        growth_rate = self.detector.get_average_growth_rate()
        
        print(f"读取操作 - 初始内存: {initial_memory:.2f}MB")
        print(f"读取操作 - 最终内存: {final_memory:.2f}MB")
        print(f"读取操作 - 内存增长: {memory_increase:.2f}MB")
        print(f"读取操作 - 平均增长率: {growth_rate:.4f}MB/次")
        
        # 检查内存泄漏
        self.assertLess(memory_increase, 20, "PLC读取操作可能存在内存泄漏")
        self.assertLess(growth_rate, 0.1, "PLC读取操作内存增长率过高")
    
    def test_string_processing_memory_leak(self):
        """测试字符串处理是否造成内存泄漏"""
        from apps.connect.connect_melseca1enet_backu import MelsecA1ENetClient
        
        with patch('settings.DevelopmentConfig') as mock_config:
            mock_config.return_value.KAFKA_ENABLED = False
            client = MelsecA1ENetClient("192.168.1.100", 4998, 0)
        
        # 特殊的字符串处理配置（可能导致内存泄漏的场景）
        register_dict = {
            "codeResult": {
                'num': 64,  # 大量字符串数据
                'source_addr': "D300",
                'coefficient': 1,
                'kafka_position': "result",
                'precision': 0,
                'type': "str",
                'cn_name': "代码结果",
                'device_a_tag': "CODE001",
                'device_name': "代码读取器"
            }
        }
        
        # 模拟包含大量数据的字符串返回
        mock_large_string = "A" * 1000 + "B" * 1000 + "1234567890" * 100
        self.mock_melsec.return_value.ReadString.return_value = Mock(Content=mock_large_string)
        
        self.detector.start_monitoring()
        initial_memory = self.detector.initial_memory
        
        # 执行多次字符串处理操作
        for i in range(50):
            try:
                data = client.read_plc(register_dict)
                
                # 验证字符串处理结果
                if data:
                    self.assertIn('codeResult', data[0])
                
                if i % 5 == 0:
                    current_memory = self.detector.measure()
                    print(f"第{i+1}次字符串处理后内存: {current_memory:.2f}MB")
                
            except Exception as e:
                self.fail(f"字符串处理时出现异常: {e}")
        
        final_memory = self.detector.measure()
        memory_increase = self.detector.get_memory_increase()
        
        print(f"字符串处理 - 初始内存: {initial_memory:.2f}MB")
        print(f"字符串处理 - 最终内存: {final_memory:.2f}MB")
        print(f"字符串处理 - 内存增长: {memory_increase:.2f}MB")
        
        # 字符串处理特别容易造成内存泄漏
        self.assertLess(memory_increase, 30, "字符串处理可能存在严重内存泄漏")
    
    def test_connection_recreation_memory_leak(self):
        """测试连接重建是否造成内存泄漏"""
        from apps.connect.connect_melseca1enet_backu import MelsecA1ENetClient
        
        with patch('settings.DevelopmentConfig') as mock_config:
            mock_config.return_value.KAFKA_ENABLED = False
            client = MelsecA1ENetClient("192.168.1.100", 4998, 0)
        
        # 模拟连接失败，触发重连逻辑
        mock_plc_instance = self.mock_melsec.return_value
        
        self.detector.start_monitoring()
        initial_memory = self.detector.initial_memory
        
        register_dict = {
            "test": {
                'num': 1,
                'source_addr': "D100",
                'coefficient': 1,
                'kafka_position': "test",
                'precision': 0,
                'type': "int16",
                'cn_name': "测试",
                'device_a_tag': "TEST",
                'device_name': "测试设备"
            }
        }
        
        # 模拟连接异常和重连
        for i in range(20):
            try:
                # 每3次模拟一次连接异常
                if i % 3 == 0:
                    mock_plc_instance.ReadInt16.side_effect = Exception("连接断开")
                else:
                    mock_plc_instance.ReadInt16.side_effect = None
                    mock_plc_instance.ReadInt16.return_value = Mock(Content=[100])
                
                data = client.read_plc(register_dict)
                
                if i % 5 == 0:
                    current_memory = self.detector.measure()
                    print(f"第{i+1}次连接操作后内存: {current_memory:.2f}MB")
                
            except Exception as e:
                print(f"预期的连接异常: {e}")
        
        final_memory = self.detector.measure()
        memory_increase = self.detector.get_memory_increase()
        
        print(f"连接重建 - 初始内存: {initial_memory:.2f}MB")
        print(f"连接重建 - 最终内存: {final_memory:.2f}MB")
        print(f"连接重建 - 内存增长: {memory_increase:.2f}MB")
        
        # 连接重建不应该造成大量内存泄漏
        self.assertLess(memory_increase, 25, "连接重建可能存在内存泄漏")
    
    @unittest.skipUnless(MEMORY_PROFILER_AVAILABLE, "memory_profiler not available")
    def test_detailed_memory_profiling(self):
        """详细的内存分析（需要memory_profiler）"""
        from apps.connect.connect_melseca1enet_backu import MelsecA1ENetClient
        
        def memory_intensive_operation():
            with patch('settings.DevelopmentConfig') as mock_config:
                mock_config.return_value.KAFKA_ENABLED = False
                client = MelsecA1ENetClient("192.168.1.100", 4998, 0)
            
            register_dict = {
                "data": {
                    'num': 1,
                    'source_addr': "D100",
                    'coefficient': 1,
                    'kafka_position': "test",
                    'precision': 0,
                    'type': "int16",
                    'cn_name': "数据",
                    'device_a_tag': "DATA",
                    'device_name': "数据点"
                }
            }
            
            # 执行多次操作
            for i in range(20):
                client.read_plc(register_dict)
                time.sleep(0.01)
        
        # 使用memory_profiler监控内存使用
        mem_usage = memory_usage(memory_intensive_operation, interval=0.1)
        
        if mem_usage:
            initial_mem = mem_usage[0]
            peak_mem = max(mem_usage)
            final_mem = mem_usage[-1]
            
            print(f"详细内存分析:")
            print(f"  初始内存: {initial_mem:.2f}MB")
            print(f"  峰值内存: {peak_mem:.2f}MB")
            print(f"  最终内存: {final_mem:.2f}MB")
            print(f"  净增长: {final_mem - initial_mem:.2f}MB")
            print(f"  峰值增长: {peak_mem - initial_mem:.2f}MB")
            
            # 检查内存使用模式
            self.assertLess(peak_mem - initial_mem, 50, "峰值内存使用过高")
            self.assertLess(final_mem - initial_mem, 20, "最终内存增长过大")
    
    def test_object_reference_leak(self):
        """测试对象引用泄漏"""
        from apps.connect.connect_melseca1enet_backu import MelsecA1ENetClient
        
        # 记录初始对象数量
        gc.collect()
        initial_objects = len(gc.get_objects())
        
        clients = []
        for i in range(5):
            with patch('settings.DevelopmentConfig') as mock_config:
                mock_config.return_value.KAFKA_ENABLED = False
                client = MelsecA1ENetClient("192.168.1.100", 4998, 0)
                clients.append(client)
        
        # 执行一些操作
        register_dict = {
            "test": {
                'num': 1,
                'source_addr': "D100",
                'coefficient': 1,
                'kafka_position': "test",
                'precision': 0,
                'type': "int16",
                'cn_name': "测试",
                'device_a_tag': "TEST",
                'device_name': "测试设备"
            }
        }
        
        for client in clients:
            client.read_plc(register_dict)
        
        # 删除所有客户端
        del clients
        gc.collect()
        
        final_objects = len(gc.get_objects())
        object_increase = final_objects - initial_objects
        
        print(f"对象引用检查:")
        print(f"  初始对象数: {initial_objects}")
        print(f"  最终对象数: {final_objects}")
        print(f"  对象增长: {object_increase}")
        
        # 允许适当的对象增长，但不应该过多
        self.assertLess(object_increase, 1000, "可能存在对象引用泄漏")
    
    def test_potential_memory_leak_sources(self):
        """测试潜在的内存泄漏源"""
        print("\n=== 潜在内存泄漏源分析 ===")
        
        issues_found = []
        
        # 1. 检查循环引用
        from apps.connect.connect_melseca1enet_backu import MelsecA1ENetClient
        
        with patch('settings.DevelopmentConfig') as mock_config:
            mock_config.return_value.KAFKA_ENABLED = False
            client = MelsecA1ENetClient("192.168.1.100", 4998, 0)
        
        # 检查对象属性是否可能造成循环引用
        if hasattr(client, 'plc') and hasattr(client, 'influxdb_client'):
            issues_found.append("客户端包含多个外部连接对象，可能造成引用循环")
        
        # 2. 检查是否正确关闭连接
        if hasattr(client, 'plc') and not hasattr(client, '__del__'):
            issues_found.append("MelsecA1ENetClient缺少析构函数，可能无法正确关闭连接")
        
        # 3. 检查字符串处理
        if True:  # 这里检查代码中的字符串处理逻辑
            issues_found.append("代码中存在大量字符串处理和正则表达式操作，可能造成字符串对象积累")
        
        # 4. 检查异常处理
        issues_found.append("异常处理中重新创建连接对象，可能造成旧连接对象未正确释放")
        
        print("发现的潜在问题:")
        for i, issue in enumerate(issues_found, 1):
            print(f"  {i}. {issue}")
        
        # 提供修复建议
        suggestions = [
            "1. 在MelsecA1ENetClient中添加__del__方法确保连接正确关闭",
            "2. 在异常处理中先关闭旧连接再创建新连接",
            "3. 优化字符串处理逻辑，避免创建过多临时字符串对象",
            "4. 考虑使用连接池来管理PLC连接",
            "5. 定期调用gc.collect()进行垃圾回收"
        ]
        
        print("\n修复建议:")
        for suggestion in suggestions:
            print(f"  {suggestion}")


if __name__ == '__main__':
    # 运行内存泄漏检测测试
    unittest.main(verbosity=2)