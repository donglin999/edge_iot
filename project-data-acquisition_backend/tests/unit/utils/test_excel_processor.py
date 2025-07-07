# -*- coding: utf-8 -*-
"""
Excel处理器测试
"""

import unittest
import pandas as pd
from unittest.mock import patch, Mock
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from apps.utils.excel_processor import ExcelProcessor
from tests.test_config import EXCEL_TEST_DATA


class TestExcelProcessor(unittest.TestCase):
    """Excel处理器测试类"""

    def setUp(self):
        """测试前准备"""
        self.test_data = EXCEL_TEST_DATA.copy()

    def test_process_excel_data_basic(self):
        """测试基本的Excel数据处理"""
        # 创建测试DataFrame
        df = pd.DataFrame(self.test_data)
        
        # 处理数据
        result = process_excel_data(df)
        
        # 验证结果
        self.assertIsInstance(result, dict)
        self.assertGreater(len(result), 0)
        
        # 验证设备标识格式
        expected_key = "modbustcp192.168.1.100 : 502"
        self.assertIn(expected_key, result)
        
        # 验证设备配置
        device_config = result[expected_key]
        self.assertEqual(device_config['protocol_type'], 'modbustcp')
        self.assertEqual(device_config['source_ip'], '192.168.1.100')
        self.assertEqual(device_config['source_port'], 502)
        self.assertEqual(device_config['source_slave_addr'], 1)
        self.assertEqual(device_config['fs'], 1)

    def test_process_excel_data_with_temperature_data(self):
        """测试包含温度数据的Excel处理"""
        df = pd.DataFrame(self.test_data)
        result = process_excel_data(df)
        
        expected_key = "modbustcp192.168.1.100 : 502"
        device_config = result[expected_key]
        
        # 验证温度数据项
        self.assertIn('temperature', device_config)
        temp_config = device_config['temperature']
        
        self.assertEqual(temp_config['en_name'], 'temperature')
        self.assertEqual(temp_config['cn_name'], '温度')
        self.assertEqual(temp_config['source_addr'], 'HR001')
        self.assertEqual(temp_config['unit'], '℃')
        self.assertEqual(temp_config['coefficient'], 1.0)
        self.assertEqual(temp_config['precision'], 2)
        self.assertEqual(temp_config['kafka_position'], 'test_position')
        self.assertTrue(temp_config['to_kafka'])

    def test_process_excel_data_multiple_devices(self):
        """测试多设备处理"""
        # 创建多设备测试数据
        multi_device_data = self.test_data.copy()
        multi_device_data.extend([
            {
                'protocol_type': 'opc',
                'source_ip': '192.168.1.101',
                'source_port': 4840,
                'source_slave_addr': 1,
                'fs': 1,
                'device_a_tag': 'opc_device',
                'device_name': 'OPCDevice',
                'en_name': 'pressure',
                'cn_name': '压力',
                'source_addr': 'ns=2;s=pressure',
                'part_name': 'sensor2',
                'input_data_maximum': 1000,
                'input_data_minimum': 0,
                'output_data_minimum': 0,
                'output_data_maximum': 1000,
                'unit': 'Pa',
                'data_source': 'opc',
                'num': 2,
                'type': 'float',
                'coefficient': 1.0,
                'precision': 2,
                'kafka_position': 'test_position_2',
                'to_kafka': True
            }
        ])
        
        df = pd.DataFrame(multi_device_data)
        result = process_excel_data(df)
        
        # 验证有两个设备
        self.assertEqual(len(result), 2)
        
        # 验证设备标识
        self.assertIn("modbustcp192.168.1.100 : 502", result)
        self.assertIn("opc192.168.1.101 : 4840", result)

    def test_process_excel_data_empty_protocol_type(self):
        """测试空协议类型的处理"""
        empty_protocol_data = self.test_data.copy()
        empty_protocol_data[0]['protocol_type'] = None
        
        df = pd.DataFrame(empty_protocol_data)
        result = process_excel_data(df)
        
        # 应该忽略空协议类型的记录
        self.assertEqual(len(result), 0)

    def test_process_excel_data_same_device_multiple_tags(self):
        """测试同一设备多个标签的处理"""
        # 为同一设备添加多个标签
        multi_tag_data = self.test_data.copy()
        multi_tag_data.append({
            'protocol_type': 'modbustcp',
            'source_ip': '192.168.1.100',
            'source_port': 502,
            'source_slave_addr': 1,
            'fs': 1,
            'device_a_tag': 'test_device',
            'device_name': 'TestDevice',
            'en_name': 'humidity',
            'cn_name': '湿度',
            'source_addr': 'HR002',
            'part_name': 'sensor2',
            'input_data_maximum': 100,
            'input_data_minimum': 0,
            'output_data_minimum': 0,
            'output_data_maximum': 100,
            'unit': '%RH',
            'data_source': 'modbus',
            'num': 2,
            'type': 'float',
            'coefficient': 1.0,
            'precision': 1,
            'kafka_position': 'test_position_2',
            'to_kafka': True
        })
        
        df = pd.DataFrame(multi_tag_data)
        result = process_excel_data(df)
        
        # 验证只有一个设备
        self.assertEqual(len(result), 1)
        
        device_key = "modbustcp192.168.1.100 : 502"
        device_config = result[device_key]
        
        # 验证有两个标签
        self.assertIn('temperature', device_config)
        self.assertIn('humidity', device_config)
        
        # 验证湿度配置
        humidity_config = device_config['humidity']
        self.assertEqual(humidity_config['en_name'], 'humidity')
        self.assertEqual(humidity_config['cn_name'], '湿度')
        self.assertEqual(humidity_config['unit'], '%RH')

    def tearDown(self):
        """测试后清理"""
        pass


if __name__ == '__main__':
    unittest.main() 