#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
测试模块初始化
"""

# 版本信息
__version__ = "1.0.0"
__author__ = "Edge IoT Team"
__description__ = "工业物联网数据采集后端测试套件"

# 导入主要测试配置
from .config.test_config import TEST_CONFIG, TEST_OPTIONS

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) 