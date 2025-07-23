#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
HSL库长时间内存泄漏趋势测试
"""

import unittest
import gc
import psutil
import time
import sys
import os
# 尝试导入matplotlib，如果没有安装则跳过绘图功能
try:
    import matplotlib.pyplot as plt
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

# 添加项目根目录到Python路径
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from tests.base import BaseTestCase


class HSLLongTermMemoryTest(BaseTestCase):
    """HSL库长期内存泄漏测试"""
    
    def setUp(self):
        """测试前准备"""
        super().setUp()
        self.process = psutil.Process()
        self.memory_timeline = []
        self.setup_hsl_mocks()
    
    def setup_hsl_mocks(self):
        """设置HSL库模拟对象"""
        self.mock_hsl_client = Mock()
        
        # 模拟连接相关方法
        self.mock_hsl_client.ConnectServer.return_value = Mock(IsSuccess=True, Message="Connected")
        self.mock_hsl_client.ConnectClose.return_value = Mock(IsSuccess=True)
        
        # 模拟数据读取方法 - 返回不同大小的数据模拟真实情况
        self.setup_realistic_mock_data()
    
    def setup_realistic_mock_data(self):
        """设置更真实的模拟数据"""
        # 模拟不同大小的字符串响应
        string_responses = [
            "TemperatureData_12345_" + "X" * 50,
            "PressureData_67890_" + "Y" * 80,
            "StatusInfo_" + "Z" * 30,
            "AlarmMessage_" + "A" * 120,
            "ConfigData_" + "B" * 200
        ]
        
        def mock_read_string(*args, **kwargs):
            # 每次返回不同大小的字符串，模拟真实的变化
            import random
            content = random.choice(string_responses) + f"_{time.time()}"
            return Mock(IsSuccess=True, Content=content, Message="Success")
        
        self.mock_hsl_client.ReadString.side_effect = mock_read_string
        
        # 其他数据类型也添加一些变化
        def mock_read_int16(*args, **kwargs):
            import random
            value = random.randint(1000, 9999)
            return Mock(IsSuccess=True, Content=[value], Message="Success")
        
        self.mock_hsl_client.ReadInt16.side_effect = mock_read_int16
        self.mock_hsl_client.ReadInt32.side_effect = lambda *a, **k: Mock(IsSuccess=True, Content=[random.randint(100000, 999999)], Message="Success")
        self.mock_hsl_client.ReadFloat.side_effect = lambda *a, **k: Mock(IsSuccess=True, Content=[random.uniform(0.1, 999.9)], Message="Success")
        self.mock_hsl_client.ReadUInt32.side_effect = lambda *a, **k: Mock(IsSuccess=True, Content=[random.randint(0x1000, 0xFFFF)], Message="Success")
        self.mock_hsl_client.ReadBool.side_effect = lambda *a, **k: Mock(IsSuccess=True, Content=[random.choice([True, False])], Message="Success")
    
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
    
    def simulate_realistic_hsl_operations(self, num_operations=100):
        """模拟更真实的HSL操作"""
        # 模拟数据累积容器（这可能是内存泄漏的源头）
        operation_results = []
        string_cache = {}
        error_logs = []
        
        for i in range(num_operations):
            try:
                # 1. 多种类型的读取操作
                operations = [
                    ('ReadString', lambda: self.mock_hsl_client.ReadString(f"D{100+i}", 50)),
                    ('ReadInt16', lambda: self.mock_hsl_client.ReadInt16(f"D{200+i}", 1)),
                    ('ReadFloat', lambda: self.mock_hsl_client.ReadFloat(f"D{300+i}", 1)),
                ]
                
                for op_name, op_func in operations:
                    result = op_func()
                    
                    if result.IsSuccess:
                        # 2. 模拟数据处理和存储
                        processed_data = {
                            'operation_type': op_name,
                            'raw_content': result.Content,
                            'timestamp': time.time(),
                            'iteration': i,
                            'processed_content': None
                        }
                        
                        # 3. 特殊的字符串处理（可能的泄漏点）
                        if op_name == 'ReadString' and result.Content:
                            # 模拟connect_melseca1enet_backu.py中的字符串处理
                            raw_string = str(result.Content)
                            
                            # 创建多个中间字符串对象
                            temp1 = raw_string[4:64] if len(raw_string) > 64 else raw_string
                            temp2 = temp1.strip()
                            
                            # 字符检查
                            has_alnum = any(char.isalnum() for char in temp2)
                            
                            if has_alnum:
                                # 正则表达式处理
                                import re
                                temp3 = re.sub(r'\s+', '', temp2)
                                processed_data['processed_content'] = temp3
                            else:
                                processed_data['processed_content'] = "None"
                            
                            # 缓存字符串结果（潜在泄漏点）
                            cache_key = f"{op_name}_{i}"
                            string_cache[cache_key] = {
                                'original': raw_string,
                                'intermediate': [temp1, temp2],  # 保存中间结果
                                'final': processed_data['processed_content'],
                                'metadata': {
                                    'length': len(raw_string),
                                    'has_alnum': has_alnum,
                                    'processed_at': time.time()
                                }
                            }
                        
                        # 4. 累积操作结果（潜在泄漏点）
                        operation_results.append(processed_data)
                        
                    else:
                        # 5. 错误日志累积（潜在泄漏点）
                        error_info = {
                            'operation': op_name,
                            'error_message': result.Message,
                            'timestamp': time.time(),
                            'iteration': i,
                            'context': f"Failed at iteration {i}"
                        }
                        error_logs.append(error_info)
                
                # 6. 模拟一些数据处理延迟
                if i % 10 == 0:
                    time.sleep(0.001)  # 短暂延迟
                
            except Exception as e:
                error_logs.append({
                    'operation': 'Exception',
                    'error_message': str(e),
                    'timestamp': time.time(),
                    'iteration': i
                })
        
        return operation_results, string_cache, error_logs
    
    def test_long_term_memory_trend(self):
        """长期内存趋势测试"""
        print("\n🔍 HSL库长期内存趋势测试（20轮+）...")
        
        initial_memory = self.measure_memory_detailed("Initial", 0, 0)
        print(f"初始内存: {initial_memory:.2f}MB")
        
        # 存储所有数据的容器（模拟真实应用场景）
        all_operation_results = []
        all_string_caches = {}
        all_error_logs = []
        
        # 运行25轮测试，观察内存增长趋势
        total_rounds = 25
        operations_per_round = 150
        
        for round_num in range(1, total_rounds + 1):
            print(f"\n--- 第 {round_num} 轮测试 ({operations_per_round} 次操作) ---")
            
            round_start_memory = self.measure_memory_detailed(f"Round_{round_num}_Start", round_num, 0)
            
            # 执行HSL操作
            operation_results, string_cache, error_logs = self.simulate_realistic_hsl_operations(operations_per_round)
            
            # 累积所有数据（模拟真实应用中的数据累积）
            all_operation_results.extend(operation_results)
            all_string_caches.update(string_cache)
            all_error_logs.extend(error_logs)
            
            round_end_memory = self.measure_memory_detailed(f"Round_{round_num}_End", round_num, operations_per_round)
            
            # 计算本轮内存增长
            round_increase = round_end_memory - round_start_memory
            total_increase = round_end_memory - initial_memory
            
            print(f"  本轮增长: {round_increase:.2f}MB")
            print(f"  累计增长: {total_increase:.2f}MB")
            print(f"  数据统计: 操作结果={len(all_operation_results)}, 字符串缓存={len(all_string_caches)}, 错误日志={len(all_error_logs)}")
            
            # 模拟不完全的数据清理（真实场景中的问题）
            if round_num % 5 == 0:
                print(f"  执行部分数据清理...")
                
                # 只清理部分旧数据
                if len(all_operation_results) > 500:
                    # 只保留最新的300个结果
                    removed_count = len(all_operation_results) - 300
                    all_operation_results = all_operation_results[-300:]
                    print(f"    清理了 {removed_count} 个操作结果")
                
                # 字符串缓存的不完全清理
                if len(all_string_caches) > 200:
                    # 只删除一半的缓存
                    keys_to_remove = list(all_string_caches.keys())[:len(all_string_caches)//2]
                    for key in keys_to_remove:
                        del all_string_caches[key]
                    print(f"    清理了 {len(keys_to_remove)} 个字符串缓存")
                
                # 错误日志的清理
                if len(all_error_logs) > 100:
                    all_error_logs = all_error_logs[-50:]  # 只保留最新50个
                    print(f"    清理了错误日志")
                
                # 清理后测量内存
                after_cleanup_memory = self.measure_memory_detailed(f"Round_{round_num}_Cleaned", round_num, -1)
                cleanup_effect = round_end_memory - after_cleanup_memory
                print(f"    清理效果: 释放了 {cleanup_effect:.2f}MB")
            
            # 每10轮强制垃圾回收
            if round_num % 10 == 0:
                print(f"  强制垃圾回收...")
                gc.collect()
                gc_memory = self.measure_memory_detailed(f"Round_{round_num}_GC", round_num, -2)
                gc_effect = round_end_memory - gc_memory
                print(f"    GC效果: 释放了 {gc_effect:.2f}MB")
        
        # 最终测量
        final_memory = self.measure_memory_detailed("Final", total_rounds, -1)
        
        # 强制完全清理
        print(f"\n执行完全清理...")
        all_operation_results.clear()
        all_string_caches.clear()
        all_error_logs.clear()
        gc.collect()
        
        cleaned_memory = self.measure_memory_detailed("Fully_Cleaned", total_rounds, -2)
        
        # 分析结果
        total_increase = final_memory - initial_memory
        cleanup_recovery = final_memory - cleaned_memory
        
        print(f"\n📊 长期内存趋势分析:")
        print(f"  测试轮数: {total_rounds}")
        print(f"  总操作数: {total_rounds * operations_per_round}")
        print(f"  初始内存: {initial_memory:.2f}MB")
        print(f"  最终内存: {final_memory:.2f}MB")
        print(f"  清理后内存: {cleaned_memory:.2f}MB")
        print(f"  总内存增长: {total_increase:.2f}MB")
        print(f"  平均每轮增长: {total_increase/total_rounds:.3f}MB")
        print(f"  清理回收量: {cleanup_recovery:.2f}MB")
        
        # 分析内存增长趋势
        self.analyze_memory_trend()
        
        # 判断是否存在内存泄漏
        if total_increase > 30:
            print(f"\n🚨 严重内存泄漏警告:")
            print(f"  - 内存增长过大: {total_increase:.2f}MB")
            print(f"  - 平均每轮增长: {total_increase/total_rounds:.3f}MB")
            if cleanup_recovery > 10:
                print(f"  - 大量数据可被清理，确认存在累积性内存泄漏")
        elif total_increase > 15:
            print(f"\n⚠️  中等内存泄漏警告:")
            print(f"  - 内存增长较大: {total_increase:.2f}MB")
            print(f"  - 建议进一步优化数据管理")
        else:
            print(f"\n✅ 内存使用相对正常")
        
        return {
            'total_increase': total_increase,
            'average_per_round': total_increase/total_rounds,
            'cleanup_recovery': cleanup_recovery,
            'timeline': self.memory_timeline
        }
    
    def analyze_memory_trend(self):
        """分析内存增长趋势"""
        if len(self.memory_timeline) < 10:
            return
        
        print(f"\n📈 内存趋势分析:")
        
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
                
                # 判断增长模式
                if avg_growth_rate > 0.5:
                    print(f"  🚨 检测到持续的内存增长模式")
                elif avg_growth_rate > 0.2:
                    print(f"  ⚠️  检测到轻微的内存增长趋势")
                else:
                    print(f"  ✅ 内存增长在可接受范围内")
        
        # 查找内存增长的关键点
        significant_increases = []
        for i in range(1, len(memory_values)):
            increase = memory_values[i] - memory_values[i-1]
            if increase > 2:  # 单次增长超过2MB
                significant_increases.append((rounds[i], increase, self.memory_timeline[i]['label']))
        
        if significant_increases:
            print(f"\n📌 显著内存增长点:")
            for round_num, increase, label in significant_increases[:5]:  # 显示前5个
                print(f"  轮次 {round_num}: +{increase:.2f}MB ({label})")
    
    def save_memory_plot(self):
        """保存内存使用图表"""
        try:
            if len(self.memory_timeline) < 5:
                return
            
            if not MATPLOTLIB_AVAILABLE:
                print("matplotlib not available, skipping plot generation")
                return
            
            import matplotlib.pyplot as plt
            
            rounds = [m['round'] for m in self.memory_timeline]
            memory_values = [m['memory_rss_mb'] for m in self.memory_timeline]
            labels = [m['label'] for m in self.memory_timeline]
            
            plt.figure(figsize=(12, 6))
            plt.plot(rounds, memory_values, 'b-', linewidth=2, label='内存使用 (RSS)')
            
            # 标记关键点
            key_points = [m for m in self.memory_timeline if 'End' in m['label'] or 'GC' in m['label']]
            if key_points:
                key_rounds = [m['round'] for m in key_points]
                key_memory = [m['memory_rss_mb'] for m in key_points]
                plt.scatter(key_rounds, key_memory, color='red', s=30, label='关键点', zorder=5)
            
            plt.xlabel('测试轮次')
            plt.ylabel('内存使用 (MB)')
            plt.title('HSL库长期内存使用趋势')
            plt.legend()
            plt.grid(True, alpha=0.3)
            
            # 保存图表
            plot_file = os.path.join(self.temp_dir, 'hsl_memory_trend.png')
            plt.savefig(plot_file, dpi=150, bbox_inches='tight')
            plt.close()
            
            print(f"\n📊 内存趋势图已保存: {plot_file}")
            
        except Exception as e:
            print(f"保存图表失败: {e}")


if __name__ == '__main__':
    # 运行长期内存泄漏检测测试
    unittest.main(verbosity=2)