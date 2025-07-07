#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
基础日志模块测试 - 重构版本
"""

import pytest
import os
import tempfile
import shutil
import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
from pathlib import Path

# 添加项目根目录到Python路径
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from apps.utils.baseLogger import Log, delete_files
from tests.base import UtilsTestCase


class TestBaseLogger(UtilsTestCase):
    """基础日志模块测试类"""

    def setUp(self):
        """测试前准备"""
        super().setUp()
        self.log_dir = os.path.join(self.temp_dir, 'logs')
        os.makedirs(self.log_dir, exist_ok=True)

    @pytest.mark.unit
    def test_log_initialization(self):
        """测试日志初始化"""
        with patch('apps.utils.baseLogger.log_path', self.log_dir):
            logger = Log("test_logger")
            self.assertIsNotNone(logger.logger)
            self.assertIn("test_logger", logger.log_path)

    @pytest.mark.unit
    def test_log_directory_creation(self):
        """测试日志目录创建"""
        test_name = "test_dir"
        with patch('apps.utils.baseLogger.log_path', self.log_dir):
            logger = Log(test_name)
            expected_path = os.path.join(self.log_dir, test_name + "/")
            self.assertTrue(os.path.exists(expected_path))

    @pytest.mark.unit
    def test_logger_configuration(self):
        """测试日志器配置"""
        with patch('apps.utils.baseLogger.log_path', self.log_dir):
            logger = Log("config_test")
            self.assertEqual(logger.logger.level, 20)  # INFO level
            self.assertIsNotNone(logger.formatter)

    @pytest.mark.unit
    def test_print_info(self):
        """测试info日志输出"""
        with patch('apps.utils.baseLogger.log_path', self.log_dir):
            logger = Log("info_test")
            # 直接测试方法调用
            try:
                logger.printInfo("测试信息")
                # 如果没有异常则测试通过
                self.assertTrue(True)
            except Exception as e:
                self.fail(f"printInfo方法调用失败: {e}")

    @pytest.mark.unit
    def test_print_error(self):
        """测试error日志输出"""
        with patch('apps.utils.baseLogger.log_path', self.log_dir):
            logger = Log("error_test")
            try:
                logger.printError("测试错误")
                self.assertTrue(True)
            except Exception as e:
                self.fail(f"printError方法调用失败: {e}")

    @pytest.mark.unit
    def test_print_warning(self):
        """测试warning日志输出"""
        with patch('apps.utils.baseLogger.log_path', self.log_dir):
            logger = Log("warning_test")
            try:
                logger.printWarning("测试警告")
                self.assertTrue(True)
            except Exception as e:
                self.fail(f"printWarning方法调用失败: {e}")

    @pytest.mark.unit
    def test_print_critical(self):
        """测试critical日志输出"""
        with patch('apps.utils.baseLogger.log_path', self.log_dir):
            logger = Log("critical_test")
            try:
                logger.printCritical("测试严重错误")
                self.assertTrue(True)
            except Exception as e:
                self.fail(f"printCritical方法调用失败: {e}")

    @pytest.mark.unit
    def test_delete_files_success(self):
        """测试删除文件功能"""
        test_file = self.create_temp_file("测试内容", "test.log")
        folder_path = os.path.dirname(test_file)
        
        # 测试函数调用不会出错
        try:
            delete_files(folder_path)
            self.assertTrue(True)
        except Exception as e:
            self.fail(f"delete_files调用失败: {e}")

    @pytest.mark.unit
    def test_delete_files_nonexistent(self):
        """测试删除不存在的文件夹"""
        nonexistent_path = os.path.join(self.temp_dir, "nonexistent")
        with self.assertRaises(FileNotFoundError):
            delete_files(nonexistent_path)

    @pytest.mark.unit
    def test_log_file_creation(self):
        """测试日志文件创建"""
        with patch('apps.utils.baseLogger.log_path', self.log_dir):
            logger = Log("file_test")
            
            # 测试日志记录能正常工作
            try:
                logger.printInfo("测试日志文件创建")
                self.assertTrue(True)
            except Exception as e:
                self.fail(f"日志文件创建测试失败: {e}")

    @pytest.mark.unit
    def test_log_init_default_name(self):
        """测试默认名称初始化"""
        with patch('apps.utils.baseLogger.log_path', self.log_dir):
            logger = Log()
            self.assertIn("default/", logger.log_path)

    @pytest.mark.unit
    def test_log_init_custom_name(self):
        """测试自定义名称初始化"""
        with patch('apps.utils.baseLogger.log_path', self.log_dir):
            logger = Log("custom_name")
            self.assertIn("custom_name/", logger.log_path)

    @pytest.mark.unit
    def test_log_init_name_with_slash(self):
        """测试名称已包含斜杠的情况"""
        with patch('apps.utils.baseLogger.log_path', self.log_dir):
            logger = Log("name_with_slash/")
            self.assertIn("name_with_slash/", logger.log_path)

    @pytest.mark.unit
    def test_log_methods_integration(self):
        """测试日志方法集成"""
        with patch('apps.utils.baseLogger.log_path', self.log_dir):
            logger = Log("integration_test")
            
            # 测试所有日志方法都能正常调用
            methods_to_test = [
                ("printInfo", "信息日志"),
                ("printWarning", "警告日志"),
                ("printError", "错误日志"),
                ("printCritical", "严重错误日志")
            ]
            
            for method_name, message in methods_to_test:
                try:
                    method = getattr(logger, method_name)
                    method(message)
                    self.assertTrue(True, f"{method_name}方法调用成功")
                except Exception as e:
                    self.fail(f"{method_name}方法调用失败: {e}")


if __name__ == '__main__':
    unittest.main()