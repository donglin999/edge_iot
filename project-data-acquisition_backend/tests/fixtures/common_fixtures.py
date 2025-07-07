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

# 导入增强的夹具
from .enhanced_fixtures import *

# 保持向后兼容的夹具
@pytest.fixture
def mock_influx_client():
    """模拟InfluxDB客户端"""
    client = Mock()
    client.write_api.return_value = Mock()
    client.query_api.return_value = Mock()
    client.ping.return_value = True
    return client

@pytest.fixture 
def mock_modbus_client():
    """模拟Modbus TCP客户端"""
    client = Mock()
    client.connect.return_value = True
    client.read_holding_registers.return_value = [10, 20, 30, 40]
    client.read_input_registers.return_value = [100, 200]
    client.is_socket_open.return_value = True
    return client

@pytest.fixture
def mock_opcua_client():
    """模拟OPC UA客户端"""
    client = Mock()
    client.connect.return_value = True
    client.get_node.return_value = Mock()
    client.disconnect.return_value = True
    return client

@pytest.fixture
def temp_config_file():
    """临时配置文件"""
    import json
    config_data = {
        "device_id": "test_device",
        "ip": "127.0.0.1",
        "port": 502,
        "addresses": [
            {"address": 1, "type": "holding", "name": "test_value"}
        ]
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(config_data, f)
        temp_file = f.name
    
    yield temp_file
    
    # 清理
    Path(temp_file).unlink(missing_ok=True)

@pytest.fixture(scope="function")
def temp_log_dir():
    """临时日志目录 - 向后兼容"""
    temp_path = tempfile.mkdtemp()
    yield temp_path
    shutil.rmtree(temp_path)

@pytest.fixture(scope="function") 
def logger_instance(mock_logger):
    """日志实例 - 向后兼容"""
    return mock_logger