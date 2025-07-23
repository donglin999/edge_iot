#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
测试配置文件
"""

# 模拟设备配置
MOCK_DEVICE_CONFIG = {
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
        },
        {
            "name": "pressure",
            "address": "30002", 
            "data_type": "float",
            "unit": "Pa",
            "scale": 1.0,
            "offset": 0.0
        }
    ]
}

# Excel测试数据
EXCEL_TEST_DATA = {
    "protocol_type": ["modbustcp", "modbustcp", "opcua"],
    "source_ip": ["192.168.1.100", "192.168.1.100", "192.168.1.101"],
    "source_port": [502, 502, 4840],
    "source_slave_addr": [1, 1, 0],
    "fs": [1, 1, 1],
    "en_name": ["temperature", "pressure", "humidity"],
    "device_a_tag": ["T001", "P001", "H001"],
    "device_name": ["温度传感器", "压力传感器", "湿度传感器"],
    "cn_name": ["温度", "压力", "湿度"]
}

# 测试数据样本
TEST_DATA_SAMPLES = {
    "modbus_data": {
        "temperature": 25.5,
        "pressure": 101325.0,
        "humidity": 60.0
    },
    "opcua_data": {
        "node_temperature": 23.8,
        "node_pressure": 101280.0
    },
    "melsec_data": {
        "D0": 1234,
        "D1": 5678
    }
}

# 测试配置参数
TEST_CONFIG_PARAMS = {
    "test_timeout": 30,
    "mock_delay": 0.1,
    "max_retries": 3,
    "log_level": "DEBUG"
}