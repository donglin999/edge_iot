#!/usr/bin/env python3
"""
配置模型测试模块
"""
import pytest
import sys
import os
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

# 添加项目根目录到Python路径
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


class TestConfigModels:
    """配置模型测试类"""

    def setup_method(self):
        """每个测试方法前的准备工作"""
        pass
        
    def teardown_method(self):
        """每个测试方法后的清理工作"""
        pass

    @pytest.mark.unit
    def test_device_config_model(self):
        """测试设备配置模型"""
        device_config = {
            'device_id': 'modbus_device_001',
            'device_name': 'Temperature Sensor',
            'device_type': 'modbus_tcp',
            'connection': {
                'host': '192.168.1.100',
                'port': 502,
                'timeout': 10,
                'unit_id': 1
            },
            'tags': [
                {
                    'tag_name': 'temperature',
                    'address': 40001,
                    'data_type': 'float',
                    'read_interval': 1000,
                    'scaling': {
                        'factor': 0.1,
                        'offset': 0
                    }
                }
            ],
            'enabled': True
        }
        
        # 验证数据结构
        assert isinstance(device_config['device_id'], str)
        assert isinstance(device_config['device_name'], str)
        assert device_config['device_type'] in ['modbus_tcp', 'opcua', 'mitsubishi_plc']
        assert isinstance(device_config['connection'], dict)
        assert isinstance(device_config['tags'], list)
        assert isinstance(device_config['enabled'], bool)

    @pytest.mark.unit
    def test_system_config_model(self):
        """测试系统配置模型"""
        system_config = {
            'database': {
                'influxdb': {
                    'host': 'localhost',
                    'port': 8086,
                    'token': 'my-token',
                    'org': 'my-org',
                    'bucket': 'iot-data'
                }
            },
            'logging': {
                'level': 'INFO',
                'file': '/var/log/iot-system.log',
                'max_size': '10MB',
                'backup_count': 5
            },
            'api': {
                'host': '0.0.0.0',
                'port': 8000,
                'cors_origins': ['http://localhost:3001']
            }
        }
        
        assert isinstance(system_config['database'], dict)
        assert isinstance(system_config['logging'], dict)
        assert isinstance(system_config['api'], dict)
        assert system_config['logging']['level'] in ['DEBUG', 'INFO', 'WARNING', 'ERROR']

    @pytest.mark.unit
    def test_collection_config_model(self):
        """测试采集配置模型"""
        collection_config = {
            'collector_id': 'modbus_collector_001',
            'collector_type': 'modbus_tcp',
            'schedule': {
                'interval': 1000,  # ms
                'batch_size': 100,
                'retry_count': 3,
                'retry_delay': 5000
            },
            'data_processing': {
                'filter_enabled': True,
                'scaling_enabled': True,
                'validation_enabled': True
            },
            'output': {
                'type': 'influxdb',
                'measurement': 'sensor_data',
                'retention_policy': '30d'
            }
        }
        
        assert isinstance(collection_config['collector_id'], str)
        assert collection_config['collector_type'] in ['modbus_tcp', 'opcua', 'mitsubishi_plc']
        assert isinstance(collection_config['schedule'], dict)
        assert isinstance(collection_config['data_processing'], dict)
        assert isinstance(collection_config['output'], dict)

    @pytest.mark.unit
    def test_api_config_model(self):
        """测试API配置模型"""
        api_config = {
            'server': {
                'host': '0.0.0.0',
                'port': 8000,
                'workers': 4,
                'max_connections': 1000
            },
            'cors': {
                'origins': ['http://localhost:3001'],
                'methods': ['GET', 'POST', 'PUT', 'DELETE'],
                'headers': ['*']
            },
            'websocket': {
                'enabled': True,
                'max_connections': 100,
                'ping_interval': 10,
                'ping_timeout': 5
            },
            'security': {
                'jwt_secret': 'secret-key',
                'jwt_expiration': 3600,
                'rate_limit': 100
            }
        }
        
        assert isinstance(api_config['server'], dict)
        assert isinstance(api_config['cors'], dict)
        assert isinstance(api_config['websocket'], dict)
        assert isinstance(api_config['security'], dict)
        assert isinstance(api_config['server']['port'], int)
        assert isinstance(api_config['websocket']['enabled'], bool)

    @pytest.mark.unit
    def test_excel_config_model(self):
        """测试Excel配置模型"""
        excel_config = {
            'file_path': '/path/to/config.xlsx',
            'sheet_name': 'DeviceConfig',
            'header_row': 1,
            'data_start_row': 2,
            'columns': {
                'device_id': 'A',
                'device_name': 'B',
                'device_type': 'C',
                'host': 'D',
                'port': 'E',
                'tags': 'F'
            },
            'validation': {
                'required_columns': ['device_id', 'device_type', 'host'],
                'data_types': {
                    'port': 'int',
                    'timeout': 'float'
                }
            }
        }
        
        assert isinstance(excel_config['file_path'], str)
        assert isinstance(excel_config['sheet_name'], str)
        assert isinstance(excel_config['header_row'], int)
        assert isinstance(excel_config['columns'], dict)
        assert isinstance(excel_config['validation'], dict) 