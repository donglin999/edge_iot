#!/usr/bin/env python3
"""
测试数据采集性能监控功能
"""

import sys
import os
import time
import json
from datetime import datetime, timedelta

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from core.data_acquisition_monitor import data_acquisition_monitor, DataFlowStatus, DataAcquisitionAlert
from models.process_models import HealthStatus

def test_data_acquisition_monitor():
    """测试数据采集性能监控功能"""
    print("=== 测试数据采集性能监控功能 ===")
    
    # 确保数据库目录存在
    os.makedirs("backend/data", exist_ok=True)
    
    # 测试1: 注册进程监控
    print("\n1. 测试注册进程监控:")
    process_names = ["test_process_1", "test_process_2"]
    for process_name in process_names:
        result = data_acquisition_monitor.register_process(process_name)
        print(f"  注册进程 {process_name}: {'成功' if result else '失败'}")
    
    # 测试2: 更新数据点信息
    print("\n2. 测试更新数据点信息:")
    for process_name in process_names:
        # 模拟数据点更新
        data_acquisition_monitor.update_data_point(
            process_name=process_name,
            data_points=10,
            errors=0,
            response_time_ms=50.0
        )
        print(f"  更新进程 {process_name} 数据点: 10点, 0错误, 50ms响应时间")
        
        # 再次更新，模拟持续数据流
        data_acquisition_monitor.update_data_point(
            process_name=process_name,
            data_points=15,
            errors=1,
            response_time_ms=60.0
        )
        print(f"  更新进程 {process_name} 数据点: 15点, 1错误, 60ms响应时间")
    
    # 测试3: 获取数据流状态
    print("\n3. 测试获取数据流状态:")
    for process_name in process_names:
        status = data_acquisition_monitor.get_data_flow_status(process_name)
        print(f"  进程 {process_name} 数据流状态:")
        print(f"    状态: {status['status']}")
        print(f"    数据点/分钟: {status['data_points_per_minute']}")
        print(f"    错误率: {status['error_rate']}")
        print(f"    响应时间: {status['response_time_ms']}ms")
        print(f"    数据质量评分: {status['data_quality_score']}")
        print(f"    最后数据时间: {status['last_data_time']}")
    
    # 测试4: 模拟数据超时告警
    print("\n4. 测试数据超时告警:")
    # 设置较短的超时时间进行测试
    data_acquisition_monitor.data_timeout = 2
    print(f"  设置数据超时时间为 {data_acquisition_monitor.data_timeout} 秒")
    
    # 等待超时
    print("  等待数据超时...")
    time.sleep(3)
    
    # 检查数据流状态
    for process_name in process_names:
        # 手动触发检查
        status = data_acquisition_monitor.data_flow_status[process_name]
        data_acquisition_monitor._check_data_flow_status(process_name, status)
        
        # 获取更新后的状态
        updated_status = data_acquisition_monitor.get_data_flow_status(process_name)
        print(f"  进程 {process_name} 超时后状态: {updated_status['status']}")
        
        # 获取告警
        alerts = data_acquisition_monitor.get_alerts(process_name)
        print(f"  进程 {process_name} 告警数量: {len(alerts)}")
        if alerts:
            print(f"    最新告警: {alerts[0]['alert_type']} - {alerts[0]['message']}")
    
    # 测试5: 恢复数据流
    print("\n5. 测试恢复数据流:")
    for process_name in process_names:
        # 更新数据点，恢复数据流
        data_acquisition_monitor.update_data_point(
            process_name=process_name,
            data_points=20,
            errors=0,
            response_time_ms=45.0
        )
        print(f"  更新进程 {process_name} 数据点: 20点, 0错误, 45ms响应时间")
        
        # 获取更新后的状态
        status = data_acquisition_monitor.get_data_flow_status(process_name)
        print(f"  进程 {process_name} 恢复后状态: {status['status']}")
    
    # 测试6: 模拟高错误率
    print("\n6. 测试高错误率:")
    process_name = process_names[0]  # 只测试第一个进程
    
    # 更新数据点，设置高错误率
    data_acquisition_monitor.update_data_point(
        process_name=process_name,
        data_points=10,
        errors=6,  # 60%错误率
        response_time_ms=100.0
    )
    print(f"  更新进程 {process_name} 数据点: 10点, 6错误 (60%错误率), 100ms响应时间")
    
    # 手动触发检查
    status = data_acquisition_monitor.data_flow_status[process_name]
    data_acquisition_monitor._check_data_flow_status(process_name, status)
    
    # 获取更新后的状态
    updated_status = data_acquisition_monitor.get_data_flow_status(process_name)
    print(f"  进程 {process_name} 高错误率后状态: {updated_status['status']}")
    print(f"  错误率: {updated_status['error_rate']}")
    print(f"  数据质量评分: {updated_status['data_quality_score']}")
    
    # 获取告警
    alerts = data_acquisition_monitor.get_alerts(process_name)
    print(f"  进程 {process_name} 告警数量: {len(alerts)}")
    if alerts:
        print(f"    最新告警: {alerts[0]['alert_type']} - {alerts[0]['message']}")
    
    # 测试7: 获取数据流历史记录
    print("\n7. 测试获取数据流历史记录:")
    for process_name in process_names:
        history = data_acquisition_monitor.get_data_flow_history(process_name, hours=1)
        print(f"  进程 {process_name} 历史记录数量: {len(history)}")
        if history:
            print(f"    最新记录: {history[0]}")
    
    # 测试8: 获取数据流统计信息
    print("\n8. 测试获取数据流统计信息:")
    for process_name in process_names:
        stats = data_acquisition_monitor.get_data_flow_statistics(process_name, hours=1)
        print(f"  进程 {process_name} 统计信息:")
        if "samples" in stats:
            print(f"    样本数: {stats['samples']}")
            if stats['samples'] > 0:
                print(f"    平均数据点/分钟: {stats['data_points']['avg']}")
                print(f"    平均错误率: {stats['error_rate']['avg']}")
                print(f"    平均响应时间: {stats['response_time']['avg']}ms")
                print(f"    平均数据质量评分: {stats['quality_score']['avg']}")
    
    # 测试9: 解决告警
    print("\n9. 测试解决告警:")
    for process_name in process_names:
        alerts = data_acquisition_monitor.get_alerts(process_name, include_resolved=False)
        if alerts:
            alert_id = alerts[0]['id']
            result = data_acquisition_monitor.resolve_alert(alert_id)
            print(f"  解决进程 {process_name} 告警 ID {alert_id}: {'成功' if result else '失败'}")
    
    # 测试10: 启动监控线程
    print("\n10. 测试启动监控线程:")
    data_acquisition_monitor.start_monitoring(interval=5, data_timeout=10)
    print(f"  监控线程已启动，检查间隔: 5秒，数据超时: 10秒")
    
    # 等待几秒让监控线程运行
    print("  等待监控线程运行...")
    time.sleep(7)
    
    # 停止监控线程
    data_acquisition_monitor.stop_monitoring()
    print("  监控线程已停止")
    
    print("\n=== 测试完成 ===")

if __name__ == "__main__":
    try:
        test_data_acquisition_monitor()
    except KeyboardInterrupt:
        print("\n测试被用户中断")
    except Exception as e:
        print(f"测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()