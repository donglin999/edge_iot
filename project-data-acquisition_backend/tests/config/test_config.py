#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
测试配置文件
"""

import os
import tempfile
from pathlib import Path

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent.parent
TESTS_ROOT = PROJECT_ROOT / "tests"

# 测试配置
TEST_CONFIG = {
    "project_root": str(PROJECT_ROOT),
    "tests_root": str(TESTS_ROOT),
    "fixtures_dir": str(TESTS_ROOT / "fixtures"),
    "data_dir": str(TESTS_ROOT / "fixtures" / "data"),
    "reports_dir": str(TESTS_ROOT / "reports"),
    "temp_dir": tempfile.gettempdir(),
    
    # 数据库配置
    "test_db": {
        "type": "sqlite",
        "path": ":memory:",  # 内存数据库用于测试
    },
    
    # InfluxDB 测试配置
    "influxdb": {
        "host": "localhost",
        "port": 8086,
        "token": "test-token",
        "org": "test-org",
        "bucket": "test-bucket",
    },
    
    # Modbus 测试配置
    "modbus": {
        "host": "127.0.0.1",
        "port": 502,
        "unit_id": 1,
        "timeout": 5,
    },
    
    # OPC UA 测试配置
    "opcua": {
        "endpoint": "opc.tcp://127.0.0.1:4840/freeopcua/server/",
        "timeout": 10,
    },
    
    # 测试日志配置
    "logging": {
        "level": "DEBUG",
        "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        "file": str(TESTS_ROOT / "reports" / "test.log"),
    },
}

# 测试选项
TEST_OPTIONS = {
    "strict_markers": True,
    "verbose": True,
    "capture": "no",  # 不捕获输出，便于调试
    "tb": "short",    # 简短的traceback
    "junit_xml": str(TESTS_ROOT / "reports" / "junit.xml"),
    "cov_report": str(TESTS_ROOT / "reports" / "htmlcov"),
    "cov_config": str(PROJECT_ROOT / "pytest.ini"),
}

# 测试标记
TEST_MARKERS = {
    "unit": "Unit tests",
    "integration": "Integration tests", 
    "collector": "Data collector tests",
    "utils": "Utility function tests",
    "slow": "Slow running tests",
    "network": "Tests requiring network access",
    "external": "Tests requiring external services",
}

# 测试夹具配置
FIXTURE_CONFIG = {
    "scope": "function",  # 默认作用域
    "autouse": False,     # 不自动使用
}