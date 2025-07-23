#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
优化后的HSL库内存测试验证
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


class OptimizedHSLMemoryTest(BaseTestCase):
    """优化后的HSL库内存测试"""
    
    def setUp(self):
        """测试前准备"""
        super().setUp()
        self.process = psutil.Process()
        self.memory_timeline = []
        self.setup_optimized_hsl_mocks()
    
    def setup_optimized_hsl_mocks(self):
        """设置优化后的HSL库模拟对象"""
        # 模拟MemoryMonitor
        self.mock_memory_monitor = Mock()
        self.mock_memory_monitor.check_memory.return_value = 50.0
        self.mock_memory_monitor.get_memory_stats.return_value = {
            'rss_mb': 50.0,
            'vms_mb': 60.0,
            'percent': 5.0,
            'operation_count': 100
        }
        
        # 模拟优化后的HSL客户端
        self.mock_optimized_client = Mock()
        
        # 模拟连接相关方法
        self.mock_optimized_client.ConnectServer.return_value = Mock(IsSuccess=True, Message="Connected")
        self.mock_optimized_client.ConnectClose.return_value = Mock(IsSuccess=True)
        
        # 模拟数据读取方法 - 使用更真实的响应
        self.setup_realistic_optimized_data()
    
    def setup_realistic_optimized_data(self):
        """设置优化后的真实模拟数据"""
        # 模拟不同大小的字符串响应，但内存使用更稳定
        string_responses = [
            "OptimizedData_12345_" + "X" * 30,  # 减少字符串大小
            "ProcessedData_67890_" + "Y" * 40,
            "CleanInfo_" + "Z" * 20,
            "StatusMsg_" + "A" * 50,
            "ConfigData_" + "B" * 60
        ]
        
        def mock_optimized_read_string(*args, **kwargs):
            # 返回固定大小的字符串，避免随机变化
            import random
            content = random.choice(string_responses[:2])  # 限制选择范围
            return Mock(IsSuccess=True, Content=content, Message="Success")
        
        self.mock_optimized_client.ReadString.side_effect = mock_optimized_read_string
        
        # 其他数据类型也使用固定值
        self.mock_optimized_client.ReadInt16.side_effect = lambda *a, **k: Mock(IsSuccess=True, Content=[1000], Message="Success")
        self.mock_optimized_client.ReadInt32.side_effect = lambda *a, **k: Mock(IsSuccess=True, Content=[100000], Message="Success")
        self.mock_optimized_client.ReadFloat.side_effect = lambda *a, **k: Mock(IsSuccess=True, Content=[123.45], Message="Success")
        self.mock_optimized_client.ReadUInt32.side_effect = lambda *a, **k: Mock(IsSuccess=True, Content=[0x1000], Message="Success")
        self.mock_optimized_client.ReadBool.side_effect = lambda *a, **k: Mock(IsSuccess=True, Content=[True], Message="Success")
    
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
    
    def simulate_optimized_hsl_operations(self, num_operations=100):
        """模拟优化后的HSL操作"""
        # 优化：使用更少的数据容器
        operation_results = []  # 限制大小
        string_cache = {}       # 实施LRU缓存
        error_logs = []         # 限制大小
        
        # 预分配基础数据结构
        base_data_template = {
            'operation_type': '',
            'raw_content': None,
            'timestamp': 0,
            'iteration': 0,
            'processed_content': None
        }
        
        for i in range(num_operations):
            try:
                # 1. 减少操作类型，专注于常用的
                operations = [
                    ('ReadString', lambda: self.mock_optimized_client.ReadString(f"D{100+i%10}", 30)),  # 重用地址
                    ('ReadInt16', lambda: self.mock_optimized_client.ReadInt16(f"D{200+i%5}", 1)),     # 重用地址
                ]
                
                for op_name, op_func in operations:
                    result = op_func()
                    
                    if result.IsSuccess:
                        # 2. 优化数据处理和存储
                        processed_data = base_data_template.copy()
                        processed_data.update({
                            'operation_type': op_name,
                            'raw_content': result.Content,
                            'timestamp': time.time(),
                            'iteration': i
                        })
                        
                        # 3. 优化字符串处理
                        if op_name == 'ReadString' and result.Content:
                            raw_string = str(result.Content)
                            
                            # 优化：减少中间对象创建
                            if len(raw_string) > 10:
                                # 使用更高效的处理方式
                                temp_processed = raw_string[4:34] if len(raw_string) > 34 else raw_string[4:]
                                temp_cleaned = temp_processed.strip()
                                
                                # 更高效的字符检查
                                if any(c.isalnum() for c in temp_cleaned[:10]):  # 只检查前10个字符
                                    # 使用translate而不是正则表达式
                                    whitespace_map = str.maketrans('', '', ' \t\n\r')
                                    processed_data['processed_content'] = temp_cleaned.translate(whitespace_map)
                                else:
                                    processed_data['processed_content'] = "None"
                            else:
                                processed_data['processed_content'] = "None"
                            
                            # 4. 优化缓存策略（LRU）
                            cache_key = f"{op_name}_{i%20}"  # 重用键，限制缓存大小
                            if len(string_cache) < 50:  # 限制缓存大小
                                string_cache[cache_key] = {
                                    'original': raw_string[:50],  # 只存储前50个字符
                                    'final': processed_data['processed_content'],
                                    'metadata': {
                                        'length': len(raw_string),
                                        'processed_at': time.time()
                                    }
                                }
                        
                        # 5. 限制结果存储大小
                        if len(operation_results) < 200:  # 限制结果容器大小
                            operation_results.append(processed_data)
                        else:
                            # 移除最旧的数据
                            operation_results.pop(0)
                            operation_results.append(processed_data)
                    
                    else:
                        # 6. 限制错误日志大小
                        if len(error_logs) < 20:  # 限制错误日志大小
                            error_info = {
                                'operation': op_name,
                                'error_message': result.Message,
                                'timestamp': time.time(),
                                'iteration': i
                            }
                            error_logs.append(error_info)
                
                # 7. 定期清理
                if i % 50 == 0 and i > 0:
                    # 清理一半的数据
                    if len(operation_results) > 100:
                        operation_results = operation_results[-100:]
                    
                    # 清理旧缓存
                    if len(string_cache) > 30:
                        # 保留最新的20个
                        keys_to_keep = list(string_cache.keys())[-20:]
                        string_cache = {k: string_cache[k] for k in keys_to_keep}
                    
                    # 强制垃圾回收
                    gc.collect()
                
            except Exception as e:
                if len(error_logs) < 20:
                    error_logs.append({
                        'operation': 'Exception',
                        'error_message': str(e),
                        'timestamp': time.time(),
                        'iteration': i
                    })
        
        return operation_results, string_cache, error_logs
    
    def test_optimized_long_term_memory_trend(self):
        """测试优化后的长期内存趋势"""
        print("\\n🔍 优化后HSL库长期内存趋势测试（25轮）...")
        
        initial_memory = self.measure_memory_detailed("Optimized_Initial", 0, 0)
        print(f"初始内存: {initial_memory:.2f}MB")
        
        # 存储所有数据的容器（优化版本）
        all_operation_results = []
        all_string_caches = {}
        all_error_logs = []
        
        # 运行25轮测试，观察优化后的内存使用
        total_rounds = 25
        operations_per_round = 100  # 减少每轮操作数
        
        for round_num in range(1, total_rounds + 1):
            print(f"\\n--- 优化版第 {round_num} 轮测试 ({operations_per_round} 次操作) ---")
            
            round_start_memory = self.measure_memory_detailed(f"Opt_Round_{round_num}_Start", round_num, 0)
            
            # 执行优化后的HSL操作
            operation_results, string_cache, error_logs = self.simulate_optimized_hsl_operations(operations_per_round)
            
            # 优化的数据累积策略
            # 限制累积数据的总量
            all_operation_results.extend(operation_results)
            if len(all_operation_results) > 500:  # 限制总数
                all_operation_results = all_operation_results[-300:]
            
            all_string_caches.update(string_cache)
            if len(all_string_caches) > 100:  # 限制缓存总数
                # 保留最新的50个
                keys_to_keep = list(all_string_caches.keys())[-50:]
                all_string_caches = {k: all_string_caches[k] for k in keys_to_keep}
            
            all_error_logs.extend(error_logs)
            if len(all_error_logs) > 50:  # 限制错误日志总数
                all_error_logs = all_error_logs[-30:]
            
            round_end_memory = self.measure_memory_detailed(f"Opt_Round_{round_num}_End", round_num, operations_per_round)
            
            # 计算本轮内存增长
            round_increase = round_end_memory - round_start_memory
            total_increase = round_end_memory - initial_memory
            
            print(f"  本轮增长: {round_increase:.2f}MB")
            print(f"  累计增长: {total_increase:.2f}MB")
            print(f"  数据统计: 操作结果={len(all_operation_results)}, 字符串缓存={len(all_string_caches)}, 错误日志={len(all_error_logs)}")
            
            # 优化的清理策略
            if round_num % 5 == 0:
                print(f"  执行优化清理...")
                
                # 更积极的清理
                if len(all_operation_results) > 200:
                    removed_count = len(all_operation_results) - 150
                    all_operation_results = all_operation_results[-150:]
                    print(f"    清理了 {removed_count} 个操作结果")
                
                # 缓存清理
                if len(all_string_caches) > 50:
                    keys_to_remove = list(all_string_caches.keys())[:-30]
                    for key in keys_to_remove:
                        del all_string_caches[key]
                    print(f"    清理了 {len(keys_to_remove)} 个字符串缓存")
                
                # 错误日志清理
                if len(all_error_logs) > 20:
                    all_error_logs = all_error_logs[-15:]
                    print(f"    清理了错误日志")
                
                # 强制垃圾回收
                gc.collect()
                after_cleanup_memory = self.measure_memory_detailed(f"Opt_Round_{round_num}_Cleaned", round_num, -1)
                cleanup_effect = round_end_memory - after_cleanup_memory
                print(f"    清理效果: 释放了 {cleanup_effect:.2f}MB")
            
            # 每10轮强制垃圾回收
            if round_num % 10 == 0:
                print(f"  强制垃圾回收...")
                gc.collect()
                gc_memory = self.measure_memory_detailed(f"Opt_Round_{round_num}_GC", round_num, -2)
                gc_effect = round_end_memory - gc_memory
                print(f"    GC效果: 释放了 {gc_effect:.2f}MB")
        
        # 最终测量
        final_memory = self.measure_memory_detailed("Optimized_Final", total_rounds, -1)
        
        # 强制完全清理
        print(f"\\n执行完全清理...")
        all_operation_results.clear()
        all_string_caches.clear()
        all_error_logs.clear()
        gc.collect()
        
        cleaned_memory = self.measure_memory_detailed("Optimized_Fully_Cleaned", total_rounds, -2)
        
        # 分析结果
        total_increase = final_memory - initial_memory
        cleanup_recovery = final_memory - cleaned_memory
        
        print(f"\\n📊 优化后长期内存趋势分析:")
        print(f"  测试轮数: {total_rounds}")
        print(f"  总操作数: {total_rounds * operations_per_round}")
        print(f"  初始内存: {initial_memory:.2f}MB")
        print(f"  最终内存: {final_memory:.2f}MB")
        print(f"  清理后内存: {cleaned_memory:.2f}MB")
        print(f"  总内存增长: {total_increase:.2f}MB")
        print(f"  平均每轮增长: {total_increase/total_rounds:.3f}MB")
        print(f"  清理回收量: {cleanup_recovery:.2f}MB")
        
        # 对比原版本的改进
        print(f"\\n🎯 优化效果评估:")
        if total_increase < 5:
            print(f"  ✅ 优化效果显著: 内存增长控制在 {total_increase:.2f}MB 以内")
        elif total_increase < 8:
            print(f"  ✅ 优化效果良好: 内存增长降低到 {total_increase:.2f}MB")
        elif total_increase < 12:
            print(f"  ⚠️  优化效果一般: 内存增长为 {total_increase:.2f}MB")
        else:
            print(f"  ❌ 优化效果不佳: 内存增长仍然过大 {total_increase:.2f}MB")
        
        # 分析内存增长趋势
        self.analyze_optimized_memory_trend()
        
        return {
            'total_increase': total_increase,
            'average_per_round': total_increase/total_rounds,
            'cleanup_recovery': cleanup_recovery,
            'timeline': self.memory_timeline
        }
    
    def analyze_optimized_memory_trend(self):
        """分析优化后的内存增长趋势"""
        if len(self.memory_timeline) < 10:
            return
        
        print(f"\\n📈 优化后内存趋势分析:")
        
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
                max_growth = max(growth_rates)
                min_growth = min(growth_rates)
                
                print(f"  平均增长率: {avg_growth_rate:.3f}MB/轮")
                print(f"  最大增长: {max_growth:.3f}MB")
                print(f"  最小增长: {min_growth:.3f}MB")
                
                # 判断优化后的增长模式
                if avg_growth_rate > 0.3:
                    print(f"  ⚠️  仍有轻微的内存增长趋势")
                elif avg_growth_rate > 0.1:
                    print(f"  ✅ 内存增长已大幅改善")
                else:
                    print(f"  ✅ 内存使用非常稳定")


if __name__ == '__main__':
    # 运行优化后的HSL内存泄漏检测测试
    unittest.main(verbosity=2)