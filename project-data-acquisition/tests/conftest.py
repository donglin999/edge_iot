#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
pytest配置文件
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# 导入测试配置
from tests.config.test_config import TEST_CONFIG, TEST_OPTIONS, TEST_MARKERS
from tests.fixtures.common_fixtures import *
from tests.fixtures.enhanced_fixtures import *

# 注册pytest插件
pytest_plugins = [
    "tests.fixtures.common_fixtures",
    "tests.fixtures.enhanced_fixtures",
]

def pytest_configure(config):
    """pytest配置钩子"""
    # 动态注册标记
    for marker_name, marker_desc in TEST_MARKERS.items():
        config.addinivalue_line("markers", f"{marker_name}: {marker_desc}")

def pytest_collection_modifyitems(config, items):
    """修改测试收集项"""
    # 可以在这里添加自动标记逻辑
    for item in items:
        # 根据文件路径自动添加标记
        if "unit" in str(item.fspath):
            item.add_marker("unit")
        elif "integration" in str(item.fspath):
            item.add_marker("integration")
        elif "collector" in str(item.fspath):
            item.add_marker("collector")
        elif "utils" in str(item.fspath):
            item.add_marker("utils")

def pytest_sessionstart(session):
    """测试会话开始时的钩子"""
    # 确保报告目录存在
    reports_dir = Path(TEST_CONFIG["reports_dir"])
    reports_dir.mkdir(parents=True, exist_ok=True)

def pytest_sessionfinish(session, exitstatus):
    """测试会话结束时的钩子"""
    # 清理工作
    pass