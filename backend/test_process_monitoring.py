#!/usr/bin/env python3
"""
测试进程状态监控和数据收集功能
"""

import sys
import os
import time
import json
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from core.enhanced_process_manager import EnhancedProcessManager
from models.process_models import ProcessState, ConnectionStatus

def test_process_monitoring():
    """测试进程监控功能"""
    print("=== 测试进程状态监控和数据收集功能 ===")
    
    # 创建进程管理器实例
    manager = EnhancedProcessManager()
    
    print(f"初始化完成，加载了 {len(manager.processes)} 个进程配置")
    
    # 测试1: 获取所有进程状态
    print("\n1. 测试获取所有进程状态:")
    all_processes = manager.get_all_processes()
    for name, info in all_processes.items():
        print(f"  进程: {name}")
        print(f"    状态: {info['status']}")
        print(f"    类型: {info['type']}")
        print(f"    PID: {info['pid']}")
        print(f"    CPU使用率: {info['cpu_percent']}%")
        print(f"    内存使用: {info['memory_mb']}MB")
        print(f"    健康评分: {info['health_score']}")
        print(f"    重启次数: {info['restart_count']}")
        print(f"    连接状态: {info['connection_status']}")
        print()
    
    # 测试2: 获取进程统计信息
    print("2. 测试获取进程统计信息:")
    stats = manager.get_all_process_statistics()
    print(f"  总进程数: {stats['summary']['total_processes']}")
    print(f"  运行中: {stats['summary']['running_processes']}")
    print(f"  已停止: {stats['summary']['stopped_processes']}")
    print(f"  错误状态: {stats['summary']['error_processes']}")
    print(f"  崩溃状态: {stats['summary']['crashed_processes']}")
    print(f"  平均健康评分: {stats['summary']['average_health_score']}")
    print()
    
    # 测试3: 测试健康检查功能
    print("3. 测试健康检查功能:")
    for process_name in manager.processes.keys():
        health_report = manager.get_process_health_report(process_name)
        if health_report:
            print(f"  进程 {process_name} 健康报告:")
            print(f"    总体评分: {health_report['overall_score']}")
            print(f"    总体状态: {health_report['overall_status']}")
            print(f"    健康检查项目:")
            for check in health_report['health_checks']:
                print(f"      - {check['check']}: {check['status']} (评分: {check['score']})")
            print(f"    建议: {', '.join(health_report['recommendations'])}")
            print()
    
    # 测试4: 测试数据收集功能
    print("4. 测试数据收集功能:")
    for process_name in list(manager.processes.keys())[:1]:  # 只测试第一个进程
        print(f"  测试进程: {process_name}")
        
        # 模拟更新数据采集速率
        manager.update_process_data_collection_rate(process_name, 10.5)
        print(f"    更新数据采集速率: 10.5 点/分钟")
        
        # 模拟增加错误计数
        manager.increment_process_error_count(process_name, "测试错误信息")
        print(f"    增加错误计数")
        
        # 模拟更新连接状态
        manager.update_connection_status(process_name, ConnectionStatus.CONNECTED, "192.168.1.100", 502)
        print(f"    更新连接状态: 已连接")
        
        # 获取更新后的状态
        updated_info = manager.get_process_statistics(process_name)
        print(f"    更新后状态:")
        print(f"      数据采集速率: {updated_info['data_collection_rate']}")
        print(f"      错误计数: {updated_info['error_count_24h']}")
        print(f"      连接状态: {updated_info['connection_status']}")
        print()
    
    # 测试5: 测试性能历史数据
    print("5. 测试性能历史数据:")
    for process_name in list(manager.processes.keys())[:1]:  # 只测试第一个进程
        history = manager.get_process_performance_history(process_name, hours=1)
        print(f"  进程 {process_name} 最近1小时性能数据: {len(history)} 条记录")
        if history:
            latest = history[0]
            print(f"    最新记录时间: {latest['timestamp']}")
            print(f"    CPU使用率: {latest['cpu_percent']}%")
            print(f"    内存使用: {latest['memory_mb']}MB")
        print()
    
    # 测试6: 测试心跳检查
    print("6. 测试心跳检查:")
    for process_name in manager.processes.keys():
        heartbeat_ok = manager.check_process_heartbeat(process_name)
        print(f"  进程 {process_name} 心跳检查: {'正常' if heartbeat_ok else '异常'}")
    print()
    
    # 测试7: 监控循环测试（运行几秒钟）
    print("7. 测试监控循环（运行5秒）:")
    print("  监控状态:", "活跃" if manager.monitoring_active else "停止")
    
    # 等待几秒让监控循环运行
    for i in range(5):
        time.sleep(1)
        print(f"  监控运行中... {i+1}/5")
    
    print("\n=== 测试完成 ===")
    
    # 清理
    manager.stop_monitoring()
    print("监控已停止")

def create_test_config():
    """创建测试配置文件"""
    config = {
        "processes": {
            "test_process_1": {
                "type": "modbus",
                "command": ["python", "-c", "import time; time.sleep(60)"],
                "config_file": "test_config.json",
                "description": "测试进程1",
                "auto_restart": True,
                "max_restarts": 3,
                "device_ip": "192.168.1.100",
                "device_port": 502
            },
            "test_process_2": {
                "type": "opcua",
                "command": ["python", "-c", "import time; time.sleep(60)"],
                "config_file": "test_config2.json",
                "description": "测试进程2",
                "auto_restart": False,
                "max_restarts": 5,
                "device_ip": "192.168.1.101",
                "device_port": 4840
            }
        }
    }
    
    # 确保配置目录存在
    config_dir = "backend/configs"
    os.makedirs(config_dir, exist_ok=True)
    
    # 写入测试配置
    config_path = os.path.join(config_dir, "process_config.json")
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
    
    print(f"创建测试配置文件: {config_path}")

if __name__ == "__main__":
    try:
        # 创建测试配置
        create_test_config()
        
        # 运行测试
        test_process_monitoring()
        
    except KeyboardInterrupt:
        print("\n测试被用户中断")
    except Exception as e:
        print(f"测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()