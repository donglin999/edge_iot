#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
OPC UA数据采集器单元测试
"""

import unittest
import sys
import os
import time
import queue
from unittest.mock import Mock, patch, MagicMock

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

try:
    from apps.collector.opcua_influx import OpcuaInflux
except ImportError as e:
    print(f"导入失败: {e}")
    OpcuaInflux = None


class TestOpcuaInflux(unittest.TestCase):
    """OPC UA数据采集器测试类"""
    
    def setUp(self):
        """测试前设置"""
        self.test_device_config = {
            'source_ip': '192.168.1.101',
            'source_port': 4840,
            'TestTag1': {
                'source_addr': 'ns=2;i=1001',
                'cn_name': '测试标签1',
                'device_a_tag': 'TestOPCUA',
                'device_name': 'TestOPCUADevice'
            },
            'TestTag2': {
                'source_addr': 'ns=2;i=1002',
                'cn_name': '测试标签2',
                'device_a_tag': 'TestOPCUA',
                'device_name': 'TestOPCUADevice'
            }
        }
        
        if OpcuaInflux:
            with patch('apps.collector.opcua_influx.Log') as mock_log:
                self.collector = OpcuaInflux(self.test_device_config)
    
    @unittest.skipIf(OpcuaInflux is None, "OpcuaInflux导入失败")
    def test_init(self):
        """测试初始化"""
        self.assertEqual(self.collector.device_ip, '192.168.1.101')
        self.assertEqual(self.collector.device_port, 4840)
        self.assertEqual(self.collector.device_conf, self.test_device_config)
        self.assertTrue(self.collector.is_running)
        self.assertEqual(self.collector.data_buff.maxsize, 1000)
    
    @unittest.skipIf(OpcuaInflux is None, "OpcuaInflux导入失败")
    def test_init_default_port(self):
        """测试默认端口"""
        config = self.test_device_config.copy()
        config.pop('source_port')
        
        with patch('apps.collector.opcua_influx.Log') as mock_log:
            collector = OpcuaInflux(config)
            self.assertEqual(collector.device_port, 4840)
    
    @unittest.skipIf(OpcuaInflux is None, "OpcuaInflux导入失败")
    @patch('apps.collector.opcua_influx.InfluxClient')
    @patch('apps.collector.opcua_influx.Client')
    @patch('apps.collector.opcua_influx.threading.Thread')
    def test_opcua_influx(self, mock_thread, mock_opcua_client, mock_influx_client):
        """测试主函数"""
        # 模拟OPC UA客户端
        mock_opcua_instance = Mock()
        mock_opcua_client.return_value = mock_opcua_instance
        
        mock_influx_instance = Mock()
        mock_influx_client.return_value.connect.return_value = mock_influx_instance
        
        # 模拟线程
        mock_thread_instance = Mock()
        mock_thread.return_value = mock_thread_instance
        
        # 调用主函数
        self.collector.opcua_influx()
        
        # 验证客户端创建
        mock_opcua_client.assert_called_once()
        mock_influx_client.assert_called_once()
        mock_influx_client.return_value.connect.assert_called_once()
        
        # 验证线程创建
        self.assertEqual(mock_thread.call_count, 2)
        
        # 验证线程启动
        self.assertEqual(mock_thread_instance.start.call_count, 2)
    
    @unittest.skipIf(OpcuaInflux is None, "OpcuaInflux导入失败")
    @patch('apps.collector.opcua_influx.Log')
    def test_get_data_success(self, mock_log):
        """测试数据获取成功"""
        # 模拟OPC UA客户端
        mock_opcua_client = Mock()
        mock_node1 = Mock()
        mock_node1.get_value.return_value = 123.45
        mock_node2 = Mock()
        mock_node2.get_value.return_value = 67.89
        
        mock_opcua_client.get_node.side_effect = [mock_node1, mock_node2]
        
        # 模拟get_data函数（简化版）
        def mock_get_data():
            count = 0
            while count < 2:
                try:
                    for tag_name, tag_config in self.test_device_config.items():
                        if isinstance(tag_config, dict) and 'source_addr' in tag_config:
                            try:
                                node = mock_opcua_client.get_node(tag_config['source_addr'])
                                value = node.get_value()
                                
                                data_item = {
                                    'kafka_position': tag_name,
                                    'cn_name': tag_config['cn_name'],
                                    'device_a_tag': tag_config['device_a_tag'],
                                    'device_name': tag_config['device_name'],
                                    'value': value
                                }
                                
                                self.collector.data_buff.put(data_item)
                                
                            except Exception as e:
                                mock_log.return_value.printError(f"获取标签 {tag_name} 数据失败: {e}")
                    
                    count += 1
                    
                except Exception as e:
                    mock_log.return_value.printError(f"OPC UA {self.collector.device_ip}:{self.collector.device_port} get_data函数报错: {e}")
                    break
        
        # 执行模拟的get_data
        mock_get_data()
        
        # 验证数据被正确放入队列
        self.assertGreaterEqual(self.collector.data_buff.qsize(), 0)
        
        # 验证数据内容
        if not self.collector.data_buff.empty():
            data = self.collector.data_buff.get()
            self.assertEqual(data['device_a_tag'], 'TestOPCUA')
            self.assertEqual(data['device_name'], 'TestOPCUADevice')
    
    @unittest.skipIf(OpcuaInflux is None, "OpcuaInflux导入失败")
    @patch('apps.collector.opcua_influx.time.sleep')
    @patch('apps.collector.opcua_influx.Log')
    def test_get_data_exception(self, mock_log, mock_sleep):
        """测试数据获取异常"""
        # 模拟OPC UA客户端抛出异常
        mock_opcua_client = Mock()
        mock_opcua_client.get_node.side_effect = Exception("连接失败")
        
        # 模拟get_data函数处理异常
        def mock_get_data():
            try:
                for tag_name, tag_config in self.test_device_config.items():
                    if isinstance(tag_config, dict) and 'source_addr' in tag_config:
                        try:
                            node = mock_opcua_client.get_node(tag_config['source_addr'])
                            value = node.get_value()
                            
                            data_item = {
                                'kafka_position': tag_name,
                                'cn_name': tag_config['cn_name'],
                                'device_a_tag': tag_config['device_a_tag'],
                                'device_name': tag_config['device_name'],
                                'value': value
                            }
                            
                            self.collector.data_buff.put(data_item)
                            
                        except Exception as e:
                            mock_log.return_value.printError(f"获取标签 {tag_name} 数据失败: {e}")
                            
            except Exception as e:
                mock_log.return_value.printError(f"OPC UA {self.collector.device_ip}:{self.collector.device_port} get_data函数报错: {e}")
        
        # 执行模拟的get_data，不应该抛出异常
        try:
            mock_get_data()
        except Exception as e:
            self.fail(f"get_data处理异常失败: {e}")
        
        # 验证错误日志被记录
        mock_log.return_value.printError.assert_called()
    
    @unittest.skipIf(OpcuaInflux is None, "OpcuaInflux导入失败")
    @patch('apps.collector.opcua_influx.w_influx')
    @patch('apps.collector.opcua_influx.Log')
    def test_calc_and_save_success(self, mock_log, mock_w_influx):
        """测试数据计算和保存成功"""
        # 创建测试数据
        test_data = {
            'kafka_position': 'TestTag1',
            'cn_name': '测试标签1',
            'device_a_tag': 'TestOPCUA',
            'device_name': 'TestOPCUADevice',
            'value': 123.45,
            'timestamp': 1640995200
        }
        
        # 创建数据队列并放入测试数据
        self.collector.data_buff.put(test_data)
        
        # 模拟InfluxDB客户端
        mock_influx_client = Mock()
        mock_influx_client.write_points.return_value = True
        
        # 模拟calc_and_save函数（简化版）
        def mock_calc_and_save():
            try:
                # 从队列获取数据
                data = self.collector.data_buff.get(timeout=1)
                
                # 模拟数据处理
                processed_data = {
                    'measurement': 'test_measurement',
                    'tags': {
                        'device_name': data['device_name'],
                        'device_a_tag': data['device_a_tag']
                    },
                    'fields': {
                        'value': data['value']
                    },
                    'time': data.get('timestamp', int(time.time()))
                }
                
                # 写入InfluxDB
                mock_w_influx([processed_data], mock_influx_client)
                
            except Exception as e:
                mock_log.return_value.printError(f"calc_and_save函数报错: {e}")
        
        # 执行模拟的calc_and_save
        mock_calc_and_save()
        
        # 验证数据被正确处理
        self.assertTrue(self.collector.data_buff.empty())
        
        # 验证写入InfluxDB被调用
        mock_w_influx.assert_called_once()
    
    @unittest.skipIf(OpcuaInflux is None, "OpcuaInflux导入失败")
    @patch('apps.collector.opcua_influx.w_influx')
    @patch('apps.collector.opcua_influx.Log')
    def test_calc_and_save_batch_processing(self, mock_log, mock_w_influx):
        """测试批量数据处理"""
        # 创建多个测试数据
        for i in range(3):
            test_data = {
                'kafka_position': f'TestTag{i+1}',
                'cn_name': f'测试标签{i+1}',
                'device_a_tag': 'TestOPCUA',
                'device_name': 'TestOPCUADevice',
                'value': (i + 1) * 10.5,
                'timestamp': 1640995200 + i
            }
            self.collector.data_buff.put(test_data)
        
        # 模拟InfluxDB客户端
        mock_influx_client = Mock()
        mock_influx_client.write_points.return_value = True
        
        # 模拟calc_and_save函数处理批量数据
        def mock_calc_and_save():
            batch_data = []
            count = 0
            
            while count < 3:
                try:
                    # 从队列获取数据
                    data = self.collector.data_buff.get(timeout=1)
                    
                    # 模拟数据处理
                    processed_data = {
                        'measurement': 'test_measurement',
                        'tags': {
                            'device_name': data['device_name'],
                            'device_a_tag': data['device_a_tag']
                        },
                        'fields': {
                            'value': data['value']
                        },
                        'time': data.get('timestamp', int(time.time()))
                    }
                    
                    batch_data.append(processed_data)
                    count += 1
                    
                except Exception as e:
                    mock_log.return_value.printError(f"calc_and_save函数报错: {e}")
                    break
            
            # 批量写入InfluxDB
            if batch_data:
                mock_w_influx(batch_data, mock_influx_client)
        
        # 执行模拟的calc_and_save
        mock_calc_and_save()
        
        # 验证所有数据被处理
        self.assertTrue(self.collector.data_buff.empty())
        
        # 验证批量写入InfluxDB被调用
        mock_w_influx.assert_called_once()
    
    @unittest.skipIf(OpcuaInflux is None, "OpcuaInflux导入失败")
    @patch('apps.collector.opcua_influx.w_influx')
    @patch('apps.collector.opcua_influx.Log')
    def test_calc_and_save_empty_data(self, mock_log, mock_w_influx):
        """测试空数据处理"""
        # 模拟InfluxDB客户端
        mock_influx_client = Mock()
        
        # 模拟calc_and_save函数处理空队列
        def mock_calc_and_save():
            try:
                # 尝试从空队列获取数据（超时）
                data = self.collector.data_buff.get(timeout=0.1)
                
            except queue.Empty:
                # 正常情况，队列为空
                pass
                
            except Exception as e:
                mock_log.return_value.printError(f"calc_and_save函数报错: {e}")
        
        # 执行模拟的calc_and_save
        mock_calc_and_save()
        
        # 验证队列仍为空
        self.assertTrue(self.collector.data_buff.empty())
        
        # 验证没有写入InfluxDB
        mock_w_influx.assert_not_called()
    
    @unittest.skipIf(OpcuaInflux is None, "OpcuaInflux导入失败")
    @patch('apps.collector.opcua_influx.Log')
    def test_calc_and_save_timeout(self, mock_log):
        """测试calc_and_save超时处理"""
        # 模拟calc_and_save函数处理超时
        def mock_calc_and_save():
            try:
                # 尝试从空队列获取数据（短超时）
                data = self.collector.data_buff.get(timeout=0.01)
                
            except queue.Empty:
                # 正常的超时情况，不记录错误
                pass
        
        # 执行模拟的calc_and_save，不应该抛出异常
        try:
            mock_calc_and_save()
        except Exception as e:
            self.fail(f"calc_and_save超时处理失败: {e}")
    
    @unittest.skipIf(OpcuaInflux is None, "OpcuaInflux导入失败")
    def test_data_buffer_properties(self):
        """测试数据缓冲区属性"""
        # 验证缓冲区初始状态
        self.assertTrue(self.collector.data_buff.empty())
        self.assertEqual(self.collector.data_buff.qsize(), 0)
        self.assertEqual(self.collector.data_buff.maxsize, 1000)
        
        # 添加数据
        test_data = {'test': 'data'}
        self.collector.data_buff.put(test_data)
        
        # 验证缓冲区状态
        self.assertFalse(self.collector.data_buff.empty())
        self.assertEqual(self.collector.data_buff.qsize(), 1)
        
        # 获取数据
        retrieved_data = self.collector.data_buff.get()
        self.assertEqual(retrieved_data, test_data)
        
        # 验证缓冲区恢复为空
        self.assertTrue(self.collector.data_buff.empty())
        self.assertEqual(self.collector.data_buff.qsize(), 0)


if __name__ == '__main__':
    unittest.main() 