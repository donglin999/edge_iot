# -*- coding: utf-8 -*-
"""
进程管理器测试 - 重构版本
"""

import unittest
from unittest.mock import patch, Mock, MagicMock
import sys
import os
import time
from pathlib import Path

# 添加项目根目录到Python路径
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from apps.utils.process_manager import ProcessManager
from tests.test_config import MOCK_DEVICE_CONFIG
from tests.base import UtilsTestCase


class TestProcessManager(UtilsTestCase):
    """进程管理器测试类"""

    def setUp(self):
        """测试前准备"""
        super().setUp()
        self.process_manager = ProcessManager()
        self.test_config = MOCK_DEVICE_CONFIG.copy()
        # Mock全局日志路径避免权限错误
        self.log_patcher = patch('apps.utils.baseLogger.log_path', self.temp_dir)
        self.log_patcher.start()

    def tearDown(self):
        """测试后清理"""
        super().tearDown()
        self.log_patcher.stop()

    def test_init(self):
        """测试进程管理器初始化"""
        pm = ProcessManager()
        self.assertIsInstance(pm.processes, dict)
        self.assertIsInstance(pm.process_configs, dict)
        self.assertEqual(len(pm.processes), 0)
        self.assertEqual(len(pm.process_configs), 0)

    def test_add_process_config(self):
        """测试添加进程配置"""
        process_type = 'modbustcp'
        config = self.test_config.copy()
        
        # 添加第一个配置
        self.process_manager.add_process_config(process_type, config)
        
        # 验证配置被添加
        self.assertIn(process_type, self.process_manager.process_configs)
        self.assertEqual(len(self.process_manager.process_configs[process_type]), 1)
        self.assertEqual(self.process_manager.process_configs[process_type][0], config)
        
        # 添加第二个配置
        config2 = config.copy()
        config2['source_ip'] = '192.168.1.101'
        self.process_manager.add_process_config(process_type, config2)
        
        # 验证有两个配置
        self.assertEqual(len(self.process_manager.process_configs[process_type]), 2)

    @patch('apps.utils.process_manager.Process')
    @patch('apps.collector.modbustcp_influx.ModbustcpInflux')
    def test_start_process_modbustcp(self, mock_influx_class, mock_process_class):
        """测试启动Modbus TCP进程"""
        # 设置模拟对象
        mock_influx_instance = Mock()
        mock_influx_class.return_value = mock_influx_instance
        
        mock_process_instance = Mock()
        mock_process_instance.pid = 12345
        mock_process_instance.start.return_value = None
        mock_process_class.return_value = mock_process_instance
        
        # 启动进程
        config = self.test_config.copy()
        pid = self.process_manager.start_process('modbustcp', config)
        
        # 验证结果
        self.assertEqual(pid, 12345)
        mock_influx_class.assert_called_once_with(config)
        mock_process_instance.start.assert_called_once()
        
        # 验证进程被添加到管理器
        self.assertIn(12345, self.process_manager.processes)
        process_info = self.process_manager.processes[12345]
        self.assertEqual(process_info['type'], 'modbustcp')
        self.assertEqual(process_info['config'], config)

    def test_start_process_unknown_type(self):
        """测试启动未知类型进程"""
        config = self.test_config.copy()
        pid = self.process_manager.start_process('unknown_type', config)
        
        # 应该返回None
        self.assertIsNone(pid)

    @patch('apps.utils.process_manager.Process')
    @patch('apps.collector.modbustcp_influx.ModbustcpInflux')
    def test_start_process_exception(self, mock_influx_class, mock_process_class):
        """测试启动进程异常处理"""
        # 设置模拟对象抛出异常
        mock_influx_class.side_effect = Exception("测试异常")
        
        config = self.test_config.copy()
        pid = self.process_manager.start_process('modbustcp', config)
        
        # 应该返回None
        self.assertIsNone(pid)

    @patch.object(ProcessManager, 'start_process')
    def test_start_all_processes(self, mock_start_process):
        """测试启动所有进程"""
        # 添加配置
        config1 = self.test_config.copy()
        config2 = self.test_config.copy()
        config2['source_ip'] = '192.168.1.101'
        
        self.process_manager.add_process_config('modbustcp', config1)
        self.process_manager.add_process_config('modbustcp', config2)
        
        # 模拟start_process返回值
        mock_start_process.side_effect = [12345, 12346]
        
        # 启动所有进程
        self.process_manager.start_all_processes()
        
        # 验证所有进程被启动
        self.assertEqual(mock_start_process.call_count, 2)
        mock_start_process.assert_any_call('modbustcp', config1)
        mock_start_process.assert_any_call('modbustcp', config2)

    @patch('time.sleep')
    @patch.object(ProcessManager, 'start_process')
    def test_monitor_processes(self, mock_start_process, mock_sleep):
        """测试进程监控"""
        # 创建模拟进程
        mock_process = Mock()
        mock_process.is_alive.side_effect = [True, False]  # 第一次检查活着，第二次检查死了
        
        config = self.test_config.copy()
        self.process_manager.processes[12345] = {
            'process': mock_process,
            'type': 'modbustcp',
            'config': config
        }
        
        # 模拟sleep被调用两次后停止循环
        mock_sleep.side_effect = [None, KeyboardInterrupt()]
        mock_start_process.return_value = 12346
        
        # 监控进程
        with self.assertRaises(KeyboardInterrupt):
            self.process_manager.monitor_processes()
        
        # 验证重启进程被调用
        mock_start_process.assert_called_once_with('modbustcp', config)
        # 验证死进程被从列表中移除
        self.assertNotIn(12345, self.process_manager.processes)


if __name__ == '__main__':
    unittest.main() 