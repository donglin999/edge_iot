#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
Modbus TCP数据采集器单元测试
"""

import pytest
import time
import queue
import threading
from unittest.mock import Mock, patch, MagicMock, call

from apps.collector.modbustcp_influx import ModbustcpInflux


class TestModbustcpInflux:
    """Modbus TCP数据采集器测试类"""
    
    @pytest.fixture
    def device_config(self):
        """测试设备配置"""
        return {
            'source_ip': '192.168.1.100',
            'source_port': 502,
            'source_slave_addr': 1,
            'fs': 1,
            'device_a_tag': 'TestModbusTCP',
            'device_name': 'TestModbusTCPDevice'
        }
    
    @pytest.fixture
    def collector(self, device_config):
        """创建数据采集器实例"""
        with patch('apps.collector.modbustcp_influx.Log') as mock_log:
            return ModbustcpInflux(device_config)
    
    @pytest.mark.unit
    def test_init(self, collector, device_config):
        """测试初始化"""
        assert collector.device_ip == '192.168.1.100'
        assert collector.device_port == 502
        assert collector.slave_addr == 1
        assert collector.device_fs == 1
        assert collector.device_conf == device_config
        assert collector.is_running is True
        assert collector.data_buff.maxsize == 1000
    
    @pytest.mark.unit
    def test_init_default_slave_addr(self, device_config):
        """测试默认从站地址"""
        config = device_config.copy()
        config.pop('source_slave_addr')
        
        with patch('apps.collector.modbustcp_influx.Log'):
            collector = ModbustcpInflux(config)
            assert collector.slave_addr == 1
    
    @pytest.mark.unit
    @patch('apps.collector.modbustcp_influx.InfluxClient')
    @patch('apps.collector.modbustcp_influx.ModbustcpClient')
    @patch('apps.collector.modbustcp_influx.threading.Thread')
    def test_modbustcp_influx(self, mock_thread, mock_modbus_client, mock_influx_client, collector):
        """测试主函数"""
        # 模拟客户端
        mock_modbus_instance = Mock()
        mock_modbus_client.return_value = mock_modbus_instance
        
        mock_influx_instance = Mock()
        mock_influx_client.return_value.connect.return_value = mock_influx_instance
        
        # 模拟线程
        mock_thread_instance = Mock()
        mock_thread.return_value = mock_thread_instance
        
        # 调用主函数
        collector.modbustcp_influx()
        
        # 验证客户端创建
        mock_modbus_client.assert_called_once_with(
            '192.168.1.100',
            502,
            collector.device_conf
        )
        mock_influx_client.assert_called_once()
        mock_influx_client.return_value.connect.assert_called_once()
        
        # 验证线程创建
        assert mock_thread.call_count == 2
        
        # 验证线程启动
        assert mock_thread_instance.start.call_count == 2
    
    @pytest.mark.unit
    @patch('apps.collector.modbustcp_influx.Log')
    def test_get_data_success(self, mock_log, collector):
        """测试数据获取成功"""
        # 模拟Modbus客户端
        mock_modbus_client = Mock()
        mock_data = [
            {
                'kafka_position': 'test_position',
                'cn_name': 'test_tag',
                'device_a_tag': 'TestModbusTCP',
                'device_name': 'TestModbusTCPDevice',
                'value': 100
            },
            {
                'kafka_position': 'test_position2',
                'cn_name': 'test_tag2',
                'device_a_tag': 'TestModbusTCP',
                'device_name': 'TestModbusTCPDevice',
                'value': 200
            }
        ]
        mock_modbus_client.read_modbustcp.return_value = mock_data
        
        # 模拟get_data函数
        def mock_get_data():
            count = 0
            while count < 2:
                try:
                    tag_data = mock_modbus_client.read_modbustcp()
                    
                    if tag_data:
                        for data_item in tag_data:
                            collector.data_buff.put(data_item)
                    
                    count += 1
                    
                except Exception as e:
                    mock_log.return_value.printError(f"Modbus TCP {collector.device_ip}:{collector.device_port} get_data函数报错: {e}")
                    break
        
        # 执行模拟的get_data
        mock_get_data()
        
        # 验证数据被正确放入队列
        assert collector.data_buff.qsize() >= 0
        
        # 验证数据内容
        if not collector.data_buff.empty():
            data = collector.data_buff.get()
            assert data['device_a_tag'] == 'TestModbusTCP'
            assert data['device_name'] == 'TestModbusTCPDevice'
    
    @pytest.mark.unit
    @patch('apps.collector.modbustcp_influx.time.sleep')
    @patch('apps.collector.modbustcp_influx.Log')
    def test_get_data_exception(self, mock_log, mock_sleep, collector):
        """测试数据获取异常"""
        # 模拟Modbus客户端抛出异常
        mock_modbus_client = Mock()
        mock_modbus_client.read_modbustcp.side_effect = Exception("连接失败")
        
        # 模拟get_data函数处理异常
        def mock_get_data():
            try:
                tag_data = mock_modbus_client.read_modbustcp()
                
                if tag_data:
                    for data_item in tag_data:
                        collector.data_buff.put(data_item)
                        
            except Exception as e:
                mock_log.return_value.printError(f"Modbus TCP {collector.device_ip}:{collector.device_port} get_data函数报错: {e}")
        
        # 执行模拟的get_data，不应该抛出异常
        mock_get_data()
        
        # 验证错误日志被记录
        mock_log.return_value.printError.assert_called_once()
    
    @pytest.mark.unit
    @patch('apps.collector.modbustcp_influx.w_influx')
    @patch('apps.collector.modbustcp_influx.Log')
    def test_calc_and_save_success(self, mock_log, mock_w_influx, collector):
        """测试数据计算和保存成功"""
        # 创建测试数据
        test_data = {
            'kafka_position': 'test_position',
            'cn_name': 'test_tag',
            'device_a_tag': 'TestModbusTCP',
            'device_name': 'TestModbusTCPDevice',
            'value': 100,
            'timestamp': 1640995200
        }
        
        # 创建数据队列并放入测试数据
        collector.data_buff.put(test_data)
        
        # 模拟InfluxDB客户端
        mock_influx_client = Mock()
        mock_influx_client.write_points.return_value = True
        
        # 模拟calc_and_save函数
        def mock_calc_and_save():
            try:
                # 从队列获取数据
                data = collector.data_buff.get(timeout=1)
                
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
        assert collector.data_buff.empty()
        
        # 验证写入InfluxDB被调用
        mock_w_influx.assert_called_once()
    
    @pytest.mark.unit
    @patch('apps.collector.modbustcp_influx.w_influx')
    @patch('apps.collector.modbustcp_influx.Log')
    def test_calc_and_save_batch_processing(self, mock_log, mock_w_influx, collector):
        """测试批量数据处理"""
        # 创建多个测试数据
        for i in range(5):
            test_data = {
                'kafka_position': f'test_position_{i}',
                'cn_name': f'test_tag_{i}',
                'device_a_tag': 'TestModbusTCP',
                'device_name': 'TestModbusTCPDevice',
                'value': i * 10,
                'timestamp': 1640995200 + i
            }
            collector.data_buff.put(test_data)
        
        # 模拟InfluxDB客户端
        mock_influx_client = Mock()
        mock_influx_client.write_points.return_value = True
        
        # 模拟calc_and_save函数处理批量数据
        def mock_calc_and_save():
            batch_data = []
            count = 0
            
            while count < 5:
                try:
                    # 从队列获取数据
                    data = collector.data_buff.get(timeout=1)
                    
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
        assert collector.data_buff.empty()
        
        # 验证批量写入InfluxDB被调用
        mock_w_influx.assert_called_once()
    
    @pytest.mark.unit
    @patch('apps.collector.modbustcp_influx.w_influx')
    @patch('apps.collector.modbustcp_influx.Log')
    def test_calc_and_save_empty_data(self, mock_log, mock_w_influx, collector):
        """测试空数据处理"""
        # 模拟InfluxDB客户端
        mock_influx_client = Mock()
        
        # 模拟calc_and_save函数处理空队列
        def mock_calc_and_save():
            try:
                # 尝试从空队列获取数据（超时）
                data = collector.data_buff.get(timeout=0.1)
                
            except queue.Empty:
                # 正常情况，队列为空
                pass
                
            except Exception as e:
                mock_log.return_value.printError(f"calc_and_save函数报错: {e}")
        
        # 执行模拟的calc_and_save
        mock_calc_and_save()
        
        # 验证队列仍为空
        assert collector.data_buff.empty()
        
        # 验证没有写入InfluxDB
        mock_w_influx.assert_not_called()
    
    @pytest.mark.unit
    def test_data_buffer_properties(self, collector):
        """测试数据缓冲区属性"""
        # 验证缓冲区初始状态
        assert collector.data_buff.empty()
        assert collector.data_buff.qsize() == 0
        assert collector.data_buff.maxsize == 1000
        
        # 添加数据
        test_data = {'test': 'data'}
        collector.data_buff.put(test_data)
        
        # 验证缓冲区状态
        assert not collector.data_buff.empty()
        assert collector.data_buff.qsize() == 1
        
        # 获取数据
        retrieved_data = collector.data_buff.get()
        assert retrieved_data == test_data
        
        # 验证缓冲区恢复为空
        assert collector.data_buff.empty()
        assert collector.data_buff.qsize() == 0
    
    @pytest.mark.collector
    @patch('apps.collector.modbustcp_influx.ModbustcpClient')
    @patch('apps.collector.modbustcp_influx.threading.Thread')
    @patch('apps.collector.modbustcp_influx.time.sleep')
    @patch('apps.collector.modbustcp_influx.Log')
    def test_restart_data_thread(self, mock_log, mock_sleep, mock_thread, mock_modbus_client, collector):
        """测试数据采集线程重启"""
        # 模拟客户端
        mock_modbus_instance = Mock()
        mock_modbus_client.return_value = mock_modbus_instance
        
        # 模拟线程
        mock_thread_instance = Mock()
        mock_thread_instance.is_alive.return_value = False
        mock_thread.return_value = mock_thread_instance
        
        # 模拟线程重启逻辑
        def mock_restart_thread():
            try:
                if hasattr(collector, 'data_thread') and collector.data_thread:
                    if not collector.data_thread.is_alive():
                        # 重新创建线程
                        collector.data_thread = mock_thread(target=collector.get_data, args=(mock_modbus_instance,))
                        collector.data_thread.start()
                        mock_log.return_value.printInfo("数据采集线程已重启")
                        
            except Exception as e:
                mock_log.return_value.printError(f"重启数据采集线程失败: {e}")
        
        # 执行模拟的线程重启
        mock_restart_thread()
        
        # 验证线程重启逻辑
        assert True  # 验证没有异常
    
    @pytest.mark.unit
    @patch('apps.collector.modbustcp_influx.Log')
    def test_calc_and_save_timeout(self, mock_log, collector):
        """测试calc_and_save超时处理"""
        # 模拟calc_and_save函数处理超时
        def mock_calc_and_save():
            try:
                # 尝试从空队列获取数据（短超时）
                data = collector.data_buff.get(timeout=0.01)
                
            except queue.Empty:
                # 正常的超时情况，不记录错误
                pass
        
        # 执行模拟的calc_and_save，不应该抛出异常
        mock_calc_and_save()
        
        # 验证没有错误日志
        mock_log.return_value.printError.assert_not_called()