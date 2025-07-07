#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
测试基类模块
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import tempfile
import shutil
import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from tests.config.test_config import TEST_CONFIG


class BaseTestCase(unittest.TestCase):
    """测试基类"""
    
    def setUp(self):
        """测试前准备"""
        self.temp_dir = tempfile.mkdtemp()
        self.test_config = TEST_CONFIG.copy()
        self.addCleanup(self.cleanup_temp_dir)
    
    def cleanup_temp_dir(self):
        """清理临时目录"""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def create_temp_file(self, content='', filename='test.txt'):
        """创建临时文件"""
        filepath = os.path.join(self.temp_dir, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return filepath
    
    def create_temp_dir(self, dirname='test_dir'):
        """创建临时目录"""
        dirpath = os.path.join(self.temp_dir, dirname)
        os.makedirs(dirpath, exist_ok=True)
        return dirpath


class MockDataMixin:
    """模拟数据混合类"""
    
    @staticmethod
    def get_mock_device_config():
        """获取模拟设备配置"""
        return {
            "device_id": "test_device_001",
            "device_name": "测试设备001",
            "source_ip": "192.168.1.100",
            "source_port": 502,
            "unit_id": 1,
            "protocol_type": "modbustcp",
            "sampling_interval": 1,
            "connection_timeout": 5,
            "retry_count": 3,
            "retry_delay": 1,
            "influx_config": {
                "host": "localhost",
                "port": 8086,
                "token": "test-token",
                "org": "test-org", 
                "bucket": "test-bucket"
            }
        }
    
    @staticmethod
    def get_mock_modbus_data():
        """获取模拟Modbus数据"""
        return {
            "holding_registers": [100, 200, 300, 400],
            "input_registers": [10, 20, 30, 40],
            "coils": [True, False, True, False],
            "discrete_inputs": [False, True, False, True]
        }
    
    @staticmethod
    def get_mock_opcua_data():
        """获取模拟OPC UA数据"""
        return {
            "ns=2;i=1": 25.5,
            "ns=2;i=2": 101325.0,
            "ns=2;i=3": 60.0
        }
    
    @staticmethod
    def get_mock_influx_data():
        """获取模拟InfluxDB数据"""
        return {
            "measurement": "test_measurement",
            "tags": {"device": "test_device"},
            "fields": {"temperature": 25.5, "pressure": 101325.0},
            "time": "2023-01-01T00:00:00Z"
        }


class LoggerTestMixin:
    """日志测试混合类"""
    
    def setUp(self):
        """设置日志测试环境"""
        super().setUp()
        self.log_dir = os.path.join(self.temp_dir, 'logs')
        os.makedirs(self.log_dir, exist_ok=True)
    
    def create_mock_logger(self):
        """创建模拟日志器"""
        mock_logger = Mock()
        mock_logger.info = Mock()
        mock_logger.warning = Mock()
        mock_logger.error = Mock()
        mock_logger.debug = Mock()
        mock_logger.critical = Mock()
        return mock_logger


class ProcessTestMixin:
    """进程测试混合类"""
    
    def create_mock_process(self, pid=12345, is_alive=True):
        """创建模拟进程"""
        mock_process = Mock()
        mock_process.pid = pid
        mock_process.is_alive.return_value = is_alive
        mock_process.start = Mock()
        mock_process.terminate = Mock()
        mock_process.join = Mock()
        return mock_process


class NetworkTestMixin:
    """网络测试混合类"""
    
    def create_mock_client(self, connected=True):
        """创建模拟客户端"""
        mock_client = Mock()
        mock_client.connect = Mock(return_value=connected)
        mock_client.disconnect = Mock()
        mock_client.is_connected = Mock(return_value=connected)
        mock_client.read = Mock()
        mock_client.write = Mock()
        return mock_client


class CollectorTestCase(BaseTestCase, MockDataMixin, LoggerTestMixin, ProcessTestMixin, NetworkTestMixin):
    """数据采集器测试基类"""
    
    def setUp(self):
        """设置采集器测试环境"""
        super().setUp()
        self.device_config = self.get_mock_device_config()
        self.mock_logger = self.create_mock_logger()
        self.mock_process = self.create_mock_process()
        self.mock_client = self.create_mock_client()


class UtilsTestCase(BaseTestCase, MockDataMixin, LoggerTestMixin):
    """工具类测试基类"""
    
    def setUp(self):
        """设置工具类测试环境"""
        super().setUp()
        self.mock_logger = self.create_mock_logger()


class IntegrationTestCase(BaseTestCase, MockDataMixin, LoggerTestMixin, ProcessTestMixin, NetworkTestMixin):
    """集成测试基类"""
    
    def setUp(self):
        """设置集成测试环境"""
        super().setUp()
        self.device_config = self.get_mock_device_config()
        # 在集成测试中，我们可能需要真实的服务
        self.skip_if_no_services()
    
    def skip_if_no_services(self):
        """如果没有外部服务则跳过测试"""
        # 这里可以添加检查外部服务的逻辑
        pass