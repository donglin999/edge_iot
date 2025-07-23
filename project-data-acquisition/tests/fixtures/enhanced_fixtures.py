#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
通用测试夹具
"""

import pytest
import tempfile
import shutil
import os
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

# 添加项目根目录到Python路径
PROJECT_ROOT = Path(__file__).parent.parent.parent
import sys
sys.path.insert(0, str(PROJECT_ROOT))

from tests.config.test_config import TEST_CONFIG


@pytest.fixture(scope="function")
def temp_dir():
    """临时目录夹具"""
    temp_path = tempfile.mkdtemp()
    yield temp_path
    shutil.rmtree(temp_path)


@pytest.fixture(scope="function")
def test_config():
    """测试配置夹具"""
    return TEST_CONFIG.copy()


@pytest.fixture(scope="function")
def mock_device_config():
    """模拟设备配置夹具"""
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
        },
        "data_points": [
            {
                "name": "temperature",
                "address": "30001",
                "data_type": "float",
                "unit": "℃",
                "scale": 1.0,
                "offset": 0.0
            }
        ]
    }


@pytest.fixture(scope="function")
def mock_logger():
    """模拟日志器夹具"""
    logger = Mock()
    logger.info = Mock()
    logger.warning = Mock()
    logger.error = Mock()
    logger.debug = Mock()
    logger.critical = Mock()
    return logger


@pytest.fixture(scope="function")
def mock_process():
    """模拟进程夹具"""
    process = Mock()
    process.pid = 12345
    process.is_alive.return_value = True
    process.start = Mock()
    process.terminate = Mock()
    process.join = Mock()
    return process


@pytest.fixture(scope="function")
def mock_modbus_client():
    """模拟Modbus客户端夹具"""
    client = Mock()
    client.connect = Mock(return_value=True)
    client.disconnect = Mock()
    client.is_connected = Mock(return_value=True)
    client.read_holding_registers = Mock(return_value=[100, 200, 300])
    client.read_input_registers = Mock(return_value=[10, 20, 30])
    client.read_coils = Mock(return_value=[True, False, True])
    client.read_discrete_inputs = Mock(return_value=[False, True, False])
    return client


@pytest.fixture(scope="function")
def mock_opcua_client():
    """模拟OPC UA客户端夹具"""
    client = Mock()
    client.connect = Mock()
    client.disconnect = Mock()
    client.get_node = Mock()
    
    # 模拟节点
    mock_node = Mock()
    mock_node.get_value = Mock(return_value=25.5)
    client.get_node.return_value = mock_node
    
    return client


@pytest.fixture(scope="function")
def mock_influx_client():
    """模拟InfluxDB客户端夹具"""
    client = Mock()
    client.write_api = Mock()
    client.query_api = Mock()
    client.ping = Mock(return_value=True)
    
    # 模拟写入API
    mock_write_api = Mock()
    mock_write_api.write = Mock()
    client.write_api.return_value = mock_write_api
    
    # 模拟查询API
    mock_query_api = Mock()
    mock_query_api.query = Mock(return_value=[])
    client.query_api.return_value = mock_query_api
    
    return client


@pytest.fixture(scope="function")
def mock_excel_data():
    """模拟Excel数据夹具"""
    return {
        "Sheet1": [
            {"列A": "值1", "列B": "值2", "列C": "值3"},
            {"列A": "值4", "列B": "值5", "列C": "值6"},
            {"列A": "值7", "列B": "值8", "列C": "值9"}
        ]
    }


@pytest.fixture(scope="function")
def sample_data_points():
    """样本数据点夹具"""
    return [
        {
            "name": "temperature",
            "address": "30001",
            "data_type": "float",
            "unit": "℃",
            "scale": 1.0,
            "offset": 0.0
        },
        {
            "name": "pressure",
            "address": "30002",
            "data_type": "float",
            "unit": "Pa",
            "scale": 1.0,
            "offset": 0.0
        },
        {
            "name": "humidity",
            "address": "30003",
            "data_type": "float",
            "unit": "%",
            "scale": 1.0,
            "offset": 0.0
        }
    ]


@pytest.fixture(scope="function")
def log_dir(temp_dir):
    """日志目录夹具"""
    log_path = os.path.join(temp_dir, 'logs')
    os.makedirs(log_path, exist_ok=True)
    return log_path


@pytest.fixture(scope="function")
def test_data_file(temp_dir):
    """测试数据文件夹具"""
    data_file = os.path.join(temp_dir, 'test_data.txt')
    with open(data_file, 'w', encoding='utf-8') as f:
        f.write("测试数据\n第二行\n第三行")
    return data_file


@pytest.fixture(scope="session")
def test_database():
    """测试数据库夹具"""
    # 这里可以创建临时数据库
    return ":memory:"  # SQLite内存数据库


@pytest.fixture(autouse=True)
def setup_test_environment():
    """自动设置测试环境"""
    # 在每个测试之前运行
    yield
    # 在每个测试之后运行 - 清理工作