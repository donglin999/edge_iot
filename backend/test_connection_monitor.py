#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
测试连接监控功能 - 验证数采进程与mock设备的连接状态监控
"""

import os
import sys
import time
import json
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from core.connection_monitor import connection_monitor, ConnectionCheckResult
from models.process_models import ConnectionInfo, ConnectionStatus

def test_connection_monitor():
    """测试连接监控功能"""
    print("=== 测试连接监控功能 ===")
    
    # 测试1: 注册连接
    print("\n1. 测试注册连接:")
    
    # 创建连接信息
    modbus_conn = ConnectionInfo(
        device_ip="127.0.0.1",
        device_port=502,
        protocol_type="modbus"
    )
    
    opcua_conn = ConnectionInfo(
        device_ip="127.0.0.1",
        device_port=4840,
        protocol_type="opcua"
    )
    
    # 注册连接
    connection_monitor.register_connection("modbus_test", modbus_conn)
    connection_monitor.register_connection("opcua_test", opcua_conn)
    
    print("  已注册连接:")
    for name, conn in connection_monitor.get_all_connection_status().items():
        print(f"  - {name}: {conn.device_ip}:{conn.device_port} ({conn.protocol_type})")
    
    # 测试2: 检查连接
    print("\n2. 测试检查连接:")
    
    # 检查Modbus连接
    modbus_result = connection_monitor.check_connection("modbus_test")
    print(f"  Modbus连接检查结果:")
    print(f"    成功: {modbus_result.success}")
    print(f"    状态: {modbus_result.status.value}")
    print(f"    消息: {modbus_result.message}")
    print(f"    响应时间: {modbus_result.response_time_ms}ms")
    if modbus_result.error_details:
        print(f"    错误详情: {modbus_result.error_details}")
    
    # 检查OPC UA连接
    opcua_result = connection_monitor.check_connection("opcua_test")
    print(f"  OPC UA连接检查结果:")
    print(f"    成功: {opcua_result.success}")
    print(f"    状态: {opcua_result.status.value}")
    print(f"    消息: {opcua_result.message}")
    print(f"    响应时间: {opcua_result.response_time_ms}ms")
    if opcua_result.error_details:
        print(f"    错误详情: {opcua_result.error_details}")
    
    # 测试3: 启动监控
    print("\n3. 测试启动监控:")
    connection_monitor.start_monitoring(interval=5)
    print(f"  监控状态: {'活跃' if connection_monitor.monitoring_active else '停止'}")
    print(f"  检查间隔: {connection_monitor.check_interval}秒")
    
    # 等待几秒让监控运行
    print("  等待10秒让监控运行...")
    for i in range(10):
        time.sleep(1)
        print(f"  {i+1}/10", end="\r")
    print("\n  监控运行完成")
    
    # 测试4: 获取连接统计信息
    print("\n4. 测试获取连接统计信息:")
    for name in ["modbus_test", "opcua_test"]:
        stats = connection_monitor.get_connection_statistics(name)
        print(f"  {name} 连接统计:")
        print(f"    设备: {stats.get('device_ip')}:{stats.get('device_port')}")
        print(f"    协议: {stats.get('protocol_type')}")
        print(f"    连接状态: {stats.get('status')}")
        print(f"    是否连接: {stats.get('is_connected')}")
        print(f"    连接错误数: {stats.get('connection_errors')}")
        print(f"    检查次数: {stats.get('check_count')}")
        print(f"    成功率: {stats.get('success_rate')}%")
        print(f"    平均响应时间: {stats.get('avg_response_time')}ms")
        
        # 获取最近的检查结果
        latest = stats.get('latest_check', {})
        if latest:
            print(f"    最近检查:")
            print(f"      时间: {latest.get('timestamp')}")
            print(f"      成功: {latest.get('success')}")
            print(f"      状态: {latest.get('status')}")
            print(f"      消息: {latest.get('message')}")
    
    # 测试5: 获取连接历史记录
    print("\n5. 测试获取连接历史记录:")
    for name in ["modbus_test", "opcua_test"]:
        history = connection_monitor.get_connection_history(name)
        print(f"  {name} 连接历史记录: {len(history)} 条")
        for i, record in enumerate(history):
            print(f"    记录 {i+1}:")
            print(f"      时间: {record.timestamp}")
            print(f"      成功: {record.success}")
            print(f"      状态: {record.status.value}")
            print(f"      消息: {record.message}")
    
    # 测试6: 停止监控
    print("\n6. 测试停止监控:")
    connection_monitor.stop_monitoring()
    print(f"  监控状态: {'活跃' if connection_monitor.monitoring_active else '停止'}")
    
    # 测试7: 取消注册连接
    print("\n7. 测试取消注册连接:")
    connection_monitor.unregister_connection("modbus_test")
    connection_monitor.unregister_connection("opcua_test")
    print(f"  剩余连接数: {len(connection_monitor.get_all_connection_status())}")
    
    print("\n=== 测试完成 ===")

if __name__ == "__main__":
    try:
        test_connection_monitor()
    except KeyboardInterrupt:
        print("\n测试被用户中断")
    except Exception as e:
        print(f"测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()