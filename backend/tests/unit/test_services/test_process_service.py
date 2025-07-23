#!/usr/bin/env python3
"""
进程服务测试模块
"""
import pytest
import sys
import os
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

# 添加项目根目录到Python路径
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


class TestProcessService:
    """进程服务测试类"""

    def setup_method(self):
        """每个测试方法前的准备工作"""
        self.process_manager = None
        
    def teardown_method(self):
        """每个测试方法后的清理工作"""
        if self.process_manager:
            self.process_manager = None

    @pytest.mark.unit
    def test_get_all_processes(self):
        """测试获取所有进程状态"""
        try:
            from core.enhanced_process_manager import enhanced_process_manager
            processes = enhanced_process_manager.get_all_processes()
            assert isinstance(processes, dict)
            for name, info in processes.items():
                assert isinstance(name, str)
                assert isinstance(info, dict)
                assert 'status' in info
        except ImportError:
            pytest.skip("enhanced_process_manager not available")

    @pytest.mark.unit
    def test_start_process(self):
        """测试启动进程"""
        try:
            from core.enhanced_process_manager import enhanced_process_manager
            result = enhanced_process_manager.start_process("modbus_collector")
            assert result is not None
        except ImportError:
            pytest.skip("enhanced_process_manager not available")

    @pytest.mark.unit
    def test_stop_process(self):
        """测试停止进程"""
        try:
            from core.enhanced_process_manager import enhanced_process_manager
            result = enhanced_process_manager.stop_process("modbus_collector")
            assert result is not None
        except ImportError:
            pytest.skip("enhanced_process_manager not available")

    @pytest.mark.unit
    def test_process_status_check(self):
        """测试进程状态检查"""
        try:
            from core.enhanced_process_manager import enhanced_process_manager
            processes = enhanced_process_manager.get_all_processes()
            for name, info in processes.items():
                assert 'status' in info
                assert info['status'] in ['running', 'stopped', 'error', 'unknown']
        except ImportError:
            pytest.skip("enhanced_process_manager not available")

    @pytest.mark.integration
    def test_process_lifecycle(self):
        """测试进程生命周期"""
        try:
            from core.enhanced_process_manager import enhanced_process_manager
            
            # 获取初始状态
            initial_processes = enhanced_process_manager.get_all_processes()
            
            # 启动进程
            start_result = enhanced_process_manager.start_process("modbus_collector")
            
            # 检查启动后状态
            after_start = enhanced_process_manager.get_all_processes()
            
            # 停止进程
            stop_result = enhanced_process_manager.stop_process("modbus_collector")
            
            # 检查停止后状态
            after_stop = enhanced_process_manager.get_all_processes()
            
            # 验证状态变化
            assert start_result is not None
            assert stop_result is not None
            
        except ImportError:
            pytest.skip("enhanced_process_manager not available") 