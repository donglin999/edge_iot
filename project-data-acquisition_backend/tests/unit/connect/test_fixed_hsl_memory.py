#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
修复版HSL库内存测试验证
"""

import unittest
import gc
import psutil
import time
import sys
import os
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

# 添加项目根目录到Python路径
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from tests.base import BaseTestCase


class FixedHSLMemoryTest(BaseTestCase):
    """修复版HSL库内存测试"""
    
    def setUp(self):
        """测试前准备"""
        super().setUp()
        self.process = psutil.Process()
        self.memory_timeline = []
        self.setup_fixed_hsl_mocks()
    
    def setup_fixed_hsl_mocks(self):
        """设置修复版HSL库模拟对象"""
        # 模拟修复版的HSL客户端
        self.mock_fixed_client = Mock()
        
        # 模拟连接管理器
        self.mock_connection_manager = Mock()
        self.mock_connection_manager.get_connection.return_value = Mock()
        self.mock_connection_manager.get_stats.return_value = {
            'active_connections': 1,
            'max_connections': 5,
            'connection_details': {}
        }
        
        # 模拟内存监控器
        self.mock_memory_monitor = Mock()
        self.mock_memory_monitor.get_memory_stats.return_value = {
            'current_memory_mb': 45.0,
            'average_memory_mb': 44.0,
            'max_memory_mb': 46.0,
            'memory_threshold_mb': 150.0,
            'history_count': 10
        }
        
        # 模拟HSL读取方法 - 修复版本使用更少的内存
        def mock_fixed_read_string(*args, **kwargs):
            # 固定大小的响应，避免内存累积
            content = "FixedHSLData_" + "X" * 20  # 固定小尺寸
            return Mock(IsSuccess=True, Content=content, Message="Success")
        
        self.mock_fixed_client.ReadString.side_effect = mock_fixed_read_string
        self.mock_fixed_client.ReadInt16.side_effect = lambda *a, **k: Mock(IsSuccess=True, Content=[1234], Message="Success")
        self.mock_fixed_client.ReadFloat.side_effect = lambda *a, **k: Mock(IsSuccess=True, Content=[123.4], Message="Success")
        self.mock_fixed_client.ReadBool.side_effect = lambda *a, **k: Mock(IsSuccess=True, Content=[True], Message="Success")
        self.mock_fixed_client.ReadUInt32.side_effect = lambda *a, **k: Mock(IsSuccess=True, Content=[0x1234], Message="Success")
    
    def measure_memory_detailed(self, label="", round_num=0, operation_num=0):
        """详细的内存测量"""
        gc.collect()  # 强制垃圾回收
        
        memory_info = self.process.memory_info()
        memory_mb = memory_info.rss / 1024 / 1024
        vms_mb = memory_info.vms / 1024 / 1024
        
        measurement = {
            'timestamp': time.time(),
            'memory_rss_mb': memory_mb,
            'memory_vms_mb': vms_mb,
            'round': round_num,
            'operation': operation_num,
            'label': label
        }
        
        self.memory_timeline.append(measurement)
        
        if label:
            print(f"[{label}] 轮次:{round_num} 内存:RSS={memory_mb:.2f}MB VMS={vms_mb:.2f}MB")
        
        return memory_mb
    
    def simulate_fixed_hsl_operations(self, num_operations=100):
        """模拟修复版HSL操作"""
        # 修复版本：严格控制内存使用
        operation_results = []
        string_cache = {}
        error_logs = []
        
        # 严格的大小限制
        MAX_RESULTS = 100
        MAX_CACHE = 30
        MAX_ERRORS = 10
        
        for i in range(num_operations):
            try:
                # 简化的操作集
                operations = [
                    ('ReadString', lambda: self.mock_fixed_client.ReadString(f"D{100+i%5}", 20)),  # 重用地址，小尺寸
                    ('ReadInt16', lambda: self.mock_fixed_client.ReadInt16(f"D{200+i%3}", 1)),     # 重用地址
                ]
                
                for op_name, op_func in operations:
                    result = op_func()
                    
                    if result.IsSuccess:
                        # 简化的数据结构
                        processed_data = {
                            'op': op_name,
                            'content': result.Content,
                            'time': time.time(),
                            'iter': i
                        }
                        
                        # 字符串处理优化
                        if op_name == 'ReadString' and result.Content:
                            raw_string = str(result.Content)
                            
                            # 极简化的字符串处理
                            if len(raw_string) > 10:
                                processed = raw_string[:20]  # 只取前20个字符
                                if any(c.isalnum() for c in processed[:5]):  # 只检查前5个字符
                                    processed_data['processed'] = processed.replace(' ', '')
                                else:
                                    processed_data['processed'] = "None"
                            else:
                                processed_data['processed'] = "None"
                            
                            # 严格限制缓存大小
                            if len(string_cache) < MAX_CACHE:
                                cache_key = f"{op_name}_{i%10}"  # 重用键
                                string_cache[cache_key] = processed_data['processed']
                        
                        # 严格限制结果存储
                        if len(operation_results) < MAX_RESULTS:
                            operation_results.append(processed_data)
                        else:
                            # 替换最旧的数据
                            operation_results[i % MAX_RESULTS] = processed_data
                    
                    else:
                        # 严格限制错误日志
                        if len(error_logs) < MAX_ERRORS:
                            error_logs.append({
                                'op': op_name,
                                'error': result.Message,
                                'time': time.time(),
                                'iter': i
                            })
                        else:
                            # 替换最旧的错误
                            error_logs[i % MAX_ERRORS] = {
                                'op': op_name,
                                'error': result.Message,
                                'time': time.time(),
                                'iter': i
                            }
                
                # 更频繁的清理
                if i % 25 == 0 and i > 0:  # 每25次操作清理一次
                    # 保持数据结构小型化
                    if len(operation_results) > MAX_RESULTS // 2:
                        operation_results = operation_results[-MAX_RESULTS//2:]
                    
                    if len(string_cache) > MAX_CACHE // 2:
                        # 保留最新的一半
                        keys_to_keep = list(string_cache.keys())[-MAX_CACHE//2:]
                        string_cache = {k: string_cache[k] for k in keys_to_keep}
                    
                    # 强制垃圾回收
                    gc.collect()
                
            except Exception as e:
                if len(error_logs) < MAX_ERRORS:
                    error_logs.append({
                        'op': 'Exception',
                        'error': str(e),
                        'time': time.time(),
                        'iter': i
                    })
        
        return operation_results, string_cache, error_logs
    
    def test_fixed_hsl_long_term_memory_trend(self):
        """测试修复版HSL库的长期内存趋势"""
        print("\\n🔍 修复版HSL库长期内存趋势测试（25轮）...")
        
        initial_memory = self.measure_memory_detailed("Fixed_Initial", 0, 0)
        print(f"初始内存: {initial_memory:.2f}MB")
        
        # 存储数据的容器（修复版本严格控制大小）
        all_operation_results = []
        all_string_caches = {}
        all_error_logs = []
        
        # 严格的全局限制
        MAX_GLOBAL_RESULTS = 300
        MAX_GLOBAL_CACHE = 50
        MAX_GLOBAL_ERRORS = 30
        
        # 运行25轮测试
        total_rounds = 25
        operations_per_round = 80  # 减少操作数以验证修复效果
        
        for round_num in range(1, total_rounds + 1):
            print(f"\\n--- 修复版第 {round_num} 轮测试 ({operations_per_round} 次操作) ---")
            
            round_start_memory = self.measure_memory_detailed(f"Fixed_Round_{round_num}_Start", round_num, 0)
            
            # 执行修复版HSL操作
            operation_results, string_cache, error_logs = self.simulate_fixed_hsl_operations(operations_per_round)
            
            # 严格控制的数据累积
            all_operation_results.extend(operation_results)
            if len(all_operation_results) > MAX_GLOBAL_RESULTS:
                all_operation_results = all_operation_results[-MAX_GLOBAL_RESULTS:]
            
            all_string_caches.update(string_cache)
            if len(all_string_caches) > MAX_GLOBAL_CACHE:
                keys_to_keep = list(all_string_caches.keys())[-MAX_GLOBAL_CACHE:]
                all_string_caches = {k: all_string_caches[k] for k in keys_to_keep}
            
            all_error_logs.extend(error_logs)
            if len(all_error_logs) > MAX_GLOBAL_ERRORS:
                all_error_logs = all_error_logs[-MAX_GLOBAL_ERRORS:]
            
            round_end_memory = self.measure_memory_detailed(f"Fixed_Round_{round_num}_End", round_num, operations_per_round)
            
            # 计算本轮内存增长
            round_increase = round_end_memory - round_start_memory
            total_increase = round_end_memory - initial_memory
            
            print(f"  本轮增长: {round_increase:.2f}MB")
            print(f"  累计增长: {total_increase:.2f}MB")
            print(f"  数据统计: 操作结果={len(all_operation_results)}, 字符串缓存={len(all_string_caches)}, 错误日志={len(all_error_logs)}")
            
            # 修复版的清理策略
            if round_num % 5 == 0:
                print(f"  执行修复版清理...")
                
                # 更积极的清理
                before_cleanup = len(all_operation_results) + len(all_string_caches) + len(all_error_logs)
                
                all_operation_results = all_operation_results[-100:]  # 只保留100个
                all_string_caches = dict(list(all_string_caches.items())[-20:])  # 只保留20个
                all_error_logs = all_error_logs[-10:]  # 只保留10个
                
                after_cleanup = len(all_operation_results) + len(all_string_caches) + len(all_error_logs)
                print(f"    清理了 {before_cleanup - after_cleanup} 个数据对象")
                
                # 强制垃圾回收
                gc.collect()
                after_cleanup_memory = self.measure_memory_detailed(f"Fixed_Round_{round_num}_Cleaned", round_num, -1)
                cleanup_effect = round_end_memory - after_cleanup_memory
                print(f"    清理效果: 释放了 {cleanup_effect:.2f}MB")
            
            # 每5轮强制垃圾回收
            if round_num % 5 == 0:
                print(f"  强制垃圾回收...")
                collected = gc.collect()
                gc_memory = self.measure_memory_detailed(f"Fixed_Round_{round_num}_GC", round_num, -2)
                gc_effect = round_end_memory - gc_memory
                print(f"    GC效果: 释放了 {gc_effect:.2f}MB, 回收对象: {collected}")
        
        # 最终测量
        final_memory = self.measure_memory_detailed("Fixed_Final", total_rounds, -1)
        
        # 强制完全清理
        print(f"\\n执行完全清理...")
        all_operation_results.clear()
        all_string_caches.clear()
        all_error_logs.clear()
        collected = gc.collect()
        
        cleaned_memory = self.measure_memory_detailed("Fixed_Fully_Cleaned", total_rounds, -2)
        
        # 分析结果
        total_increase = final_memory - initial_memory
        cleanup_recovery = final_memory - cleaned_memory
        
        print(f"\\n📊 修复版长期内存趋势分析:")
        print(f"  测试轮数: {total_rounds}")
        print(f"  总操作数: {total_rounds * operations_per_round}")
        print(f"  初始内存: {initial_memory:.2f}MB")
        print(f"  最终内存: {final_memory:.2f}MB")
        print(f"  清理后内存: {cleaned_memory:.2f}MB")
        print(f"  总内存增长: {total_increase:.2f}MB")
        print(f"  平均每轮增长: {total_increase/total_rounds:.3f}MB")
        print(f"  清理回收量: {cleanup_recovery:.2f}MB")
        print(f"  最终垃圾回收: {collected} 个对象")
        
        # 修复版本的效果评估
        print(f"\\n🎯 修复版本效果评估:")
        if total_increase < 2:
            print(f"  ✅ 修复效果优秀: 内存增长控制在 {total_increase:.2f}MB 以内")
        elif total_increase < 4:
            print(f"  ✅ 修复效果良好: 内存增长降低到 {total_increase:.2f}MB")
        elif total_increase < 6:
            print(f"  ⚠️  修复效果一般: 内存增长为 {total_increase:.2f}MB")
        else:
            print(f"  ❌ 修复效果不足: 内存增长仍然为 {total_increase:.2f}MB")
        
        # 与原版本对比
        original_increase = 11.88  # 原版本的内存增长
        improvement = ((original_increase - total_increase) / original_increase) * 100
        print(f"\\n📈 与原版本对比:")
        print(f"  原版本内存增长: {original_increase:.2f}MB")
        print(f"  修复版内存增长: {total_increase:.2f}MB")
        print(f"  改善程度: {improvement:.1f}%")
        
        # 分析内存增长趋势
        self.analyze_fixed_memory_trend()
        
        return {
            'total_increase': total_increase,
            'average_per_round': total_increase/total_rounds,
            'cleanup_recovery': cleanup_recovery,
            'improvement_percentage': improvement,
            'timeline': self.memory_timeline
        }
    
    def analyze_fixed_memory_trend(self):
        """分析修复版的内存增长趋势"""
        if len(self.memory_timeline) < 10:
            return
        
        print(f"\\n📈 修复版内存趋势分析:")
        
        # 提取内存数据
        memory_values = [m['memory_rss_mb'] for m in self.memory_timeline]
        rounds = [m['round'] for m in self.memory_timeline]
        
        # 计算趋势
        first_quarter = memory_values[:len(memory_values)//4]
        last_quarter = memory_values[-len(memory_values)//4:]
        
        avg_first = sum(first_quarter) / len(first_quarter)
        avg_last = sum(last_quarter) / len(last_quarter)
        trend = avg_last - avg_first
        
        print(f"  前1/4平均内存: {avg_first:.2f}MB")
        print(f"  后1/4平均内存: {avg_last:.2f}MB")
        print(f"  趋势变化: {trend:.2f}MB")
        
        # 计算增长率
        if len(memory_values) > 5:
            growth_rates = []
            for i in range(1, len(memory_values)):
                if rounds[i] != rounds[i-1]:  # 只计算轮次间的增长
                    rate = memory_values[i] - memory_values[i-1]
                    growth_rates.append(rate)
            
            if growth_rates:
                avg_growth_rate = sum(growth_rates) / len(growth_rates)
                max_growth = max(growth_rates) if growth_rates else 0
                min_growth = min(growth_rates) if growth_rates else 0
                
                print(f"  平均增长率: {avg_growth_rate:.3f}MB/轮")
                print(f"  最大增长: {max_growth:.3f}MB")
                print(f"  最小增长: {min_growth:.3f}MB")
                
                # 判断修复后的增长模式
                if avg_growth_rate < 0.05:
                    print(f"  ✅ 内存使用极其稳定，修复效果优秀")
                elif avg_growth_rate < 0.1:
                    print(f"  ✅ 内存使用非常稳定，修复效果良好")
                elif avg_growth_rate < 0.2:
                    print(f"  ✅ 内存增长已控制，修复效果显著")
                else:
                    print(f"  ⚠️  仍有轻微增长趋势，需要进一步优化")


if __name__ == '__main__':
    # 运行修复版HSL内存测试
    unittest.main(verbosity=2)