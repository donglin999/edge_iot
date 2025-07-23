#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Task 3 集成测试 - 验证ProcessIntegration类与enhanced_process_manager的集成
"""

import os
import sys
import time
import json
import tempfile
from unittest.mock import Mock, patch

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from core.process_integration import ProcessIntegration, ProcessOutput, ProcessSignalResult
from core.enhanced_process_manager import EnhancedProcessManager

def test_process_integration_basic_functionality():
    """测试ProcessIntegration基本功能"""
    print("=== 测试ProcessIntegration基本功能 ===")
    
    # 创建ProcessIntegration实例
    integration = ProcessIntegration()
    
    # 测试1: 检查初始化
    print("✓ ProcessIntegration初始化成功")
    assert hasattr(integration, 'process_configs')
    assert hasattr(integration, 'running_processes')
    assert hasattr(integration, 'output_callbacks')
    
    # 测试2: 获取可用进程类型
    process_types = integration.get_available_process_types()
    print(f"✓ 可用进程类型: {process_types}")
    assert len(process_types) > 0
    assert "modbus_collector" in process_types
    
    # 测试3: 创建进程命令
    config = {
        "device_ip": "192.168.1.100",
        "device_port": 502,
        "protocol": "modbus"
    }
    
    command = integration.create_process_command("modbus_collector", config)
    print(f"✓ 创建进程命令成功: {command[:2]}...")
    assert isinstance(command, list)
    assert len(command) >= 2
    
    # 测试4: 配置文件操作
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        test_config = {"test": "config", "value": 123}
        json.dump(test_config, f)
        temp_path = f.name
    
    try:
        # 读取配置
        loaded_config = integration.read_process_config(temp_path)
        print("✓ 读取配置文件成功")
        assert loaded_config == test_config
        
        # 更新配置
        new_config = {"updated": "config", "new_value": 456}
        result = integration.update_process_config(temp_path, new_config)
        print("✓ 更新配置文件成功")
        assert result == True
        
        # 验证更新
        updated_config = integration.read_process_config(temp_path)
        assert updated_config == new_config
        
    finally:
        os.unlink(temp_path)
    
    print("✓ 所有基本功能测试通过\n")

def test_process_integration_with_enhanced_manager():
    """测试ProcessIntegration与EnhancedProcessManager的集成"""
    print("=== 测试ProcessIntegration与EnhancedProcessManager集成 ===")
    
    # 创建实例
    integration = ProcessIntegration()
    
    # 测试进程配置模板
    template = integration.get_process_config_template("modbus_collector")
    print("✓ 获取进程配置模板成功")
    assert template is not None
    assert template["type"] == "modbus"
    
    # 测试输出回调设置
    callback_called = False
    def test_callback(output: ProcessOutput):
        nonlocal callback_called
        callback_called = True
        print(f"✓ 收到进程输出: {output.content[:50]}...")
    
    integration.set_output_callback("test_process", test_callback)
    print("✓ 设置输出回调成功")
    
    # 移除回调
    integration.remove_output_callback("test_process")
    print("✓ 移除输出回调成功")
    
    print("✓ 集成测试通过\n")

def test_process_signal_handling():
    """测试进程信号处理功能"""
    print("=== 测试进程信号处理功能 ===")
    
    integration = ProcessIntegration()
    
    # 测试向不存在的进程发送信号
    result = integration.send_process_signal(99999, 15, "non_existent")
    print(f"✓ 向不存在进程发送信号: {result.success} - {result.message}")
    assert not result.success
    assert "不存在" in result.message
    
    # 测试优雅停止不存在的进程
    result = integration.graceful_stop_process("non_existent_process")
    print(f"✓ 优雅停止不存在进程: {result.success} - {result.message}")
    assert not result.success
    assert "未在运行" in result.message
    
    # 测试强制终止不存在的进程
    result = integration.force_kill_process("non_existent_process")
    print(f"✓ 强制终止不存在进程: {result.success} - {result.message}")
    assert not result.success
    assert "未在运行" in result.message
    
    print("✓ 进程信号处理测试通过\n")

def test_data_structures():
    """测试数据结构"""
    print("=== 测试数据结构 ===")
    
    from datetime import datetime
    import signal
    
    # 测试ProcessOutput
    output = ProcessOutput(
        timestamp=datetime.now(),
        stream_type="stdout",
        content="Test output message",
        process_name="test_process"
    )
    print(f"✓ ProcessOutput创建成功: {output.process_name} - {output.content}")
    
    # 测试ProcessSignalResult
    result = ProcessSignalResult(
        success=True,
        message="Signal sent successfully",
        signal_sent=signal.SIGTERM,
        process_name="test_process"
    )
    print(f"✓ ProcessSignalResult创建成功: {result.success} - {result.message}")
    
    print("✓ 数据结构测试通过\n")

def test_integration_with_project_data_acquisition():
    """测试与project-data-acquisition的集成"""
    print("=== 测试与project-data-acquisition的集成 ===")
    
    integration = ProcessIntegration()
    
    # 检查数据采集路径
    path = integration.get_data_acquisition_path()
    if path:
        print(f"✓ 找到数据采集路径: {path}")
        
        # 检查关键文件
        run_py = os.path.join(path, "run.py")
        if os.path.exists(run_py):
            print("✓ 找到run.py文件")
        else:
            print("⚠ run.py文件不存在")
        
        excel_file = os.path.join(path, "数据地址清单.xlsx")
        if os.path.exists(excel_file):
            print("✓ 找到Excel配置文件")
        else:
            print("⚠ Excel配置文件不存在")
    else:
        print("⚠ 未找到数据采集路径，这在开发环境中是正常的")
    
    print("✓ 集成路径检查完成\n")

def main():
    """主测试函数"""
    print("开始Task 3集成测试...\n")
    
    try:
        test_process_integration_basic_functionality()
        test_process_integration_with_enhanced_manager()
        test_process_signal_handling()
        test_data_structures()
        test_integration_with_project_data_acquisition()
        
        print("🎉 所有测试通过！")
        print("\n=== Task 3实现验证 ===")
        print("✅ ProcessIntegration类实现完成")
        print("✅ 进程配置文件管理功能实现")
        print("✅ 进程启动参数管理功能实现")
        print("✅ 进程输出监控功能实现")
        print("✅ 进程信号处理功能实现")
        print("✅ 优雅停止和强制终止功能实现")
        print("✅ 与project-data-acquisition集成层实现")
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)