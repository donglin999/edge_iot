#!/usr/bin/env python3
"""
测试进程启动脚本
"""
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(__file__))

from backend.core.enhanced_process_manager import enhanced_process_manager
import time

def test_process_start():
    """测试进程启动"""
    print("开始测试进程启动...")
    
    # 获取所有进程
    processes = enhanced_process_manager.get_all_processes()
    print(f"可用进程: {list(processes.keys())}")
    
    if not processes:
        print("没有发现可用进程，请检查配置文件")
        return
    
    # 尝试启动第一个进程
    process_name = list(processes.keys())[0]
    print(f"尝试启动进程: {process_name}")
    
    result = enhanced_process_manager.start_process(process_name)
    print(f"启动结果: {result}")
    
    # 等待一下
    time.sleep(3)
    
    # 检查进程状态
    status = enhanced_process_manager.get_process_status(process_name)
    print(f"进程状态: {status}")

if __name__ == "__main__":
    test_process_start()