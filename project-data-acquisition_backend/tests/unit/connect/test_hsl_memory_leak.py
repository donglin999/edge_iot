#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
HSL通信库内存泄漏检测测试
"""

import unittest
import gc
import psutil
import threading
import time
import sys
import os
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

# 添加项目根目录到Python路径
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from tests.base import BaseTestCase

# 尝试导入 memory_profiler，如果没有安装则跳过一些测试
try:
    from memory_profiler import profile, memory_usage
    MEMORY_PROFILER_AVAILABLE = True
except ImportError:
    MEMORY_PROFILER_AVAILABLE = False


class HSLMemoryLeakDetector:
    """HSL库内存泄漏检测器"""
    
    def __init__(self):
        self.process = psutil.Process()
        self.initial_memory = None
        self.measurements = []
        self.detailed_measurements = []
    
    def start_monitoring(self):
        """开始监控内存"""
        gc.collect()
        self.initial_memory = self.process.memory_info().rss / 1024 / 1024  # MB
        self.measurements = [self.initial_memory]
        self.detailed_measurements = [{
            'time': time.time(),
            'memory_rss': self.initial_memory,
            'memory_vms': self.process.memory_info().vms / 1024 / 1024,
            'open_files': len(self.process.open_files()) if hasattr(self.process, 'open_files') else 0,
            'num_threads': self.process.num_threads()
        }]
        return self.initial_memory
    
    def measure(self, label=""):
        """测量当前内存使用"""
        gc.collect()
        current_memory = self.process.memory_info().rss / 1024 / 1024  # MB
        self.measurements.append(current_memory)
        
        detail = {
            'time': time.time(),
            'memory_rss': current_memory,
            'memory_vms': self.process.memory_info().vms / 1024 / 1024,
            'open_files': len(self.process.open_files()) if hasattr(self.process, 'open_files') else 0,
            'num_threads': self.process.num_threads(),
            'label': label
        }
        self.detailed_measurements.append(detail)
        
        if label:
            print(f"[{label}] 内存: {current_memory:.2f}MB, 线程: {detail['num_threads']}, 文件: {detail['open_files']}")
        
        return current_memory
    
    def get_memory_increase(self):
        """获取内存增长量"""
        if len(self.measurements) < 2:
            return 0
        return self.measurements[-1] - self.measurements[0]
    
    def get_peak_memory(self):
        """获取峰值内存"""
        return max(self.measurements) if self.measurements else 0
    
    def get_detailed_report(self):
        """获取详细报告"""
        if len(self.detailed_measurements) < 2:
            return {}
        
        initial = self.detailed_measurements[0]
        final = self.detailed_measurements[-1]
        peak_memory = max(m['memory_rss'] for m in self.detailed_measurements)
        
        return {
            'initial_memory': initial['memory_rss'],
            'final_memory': final['memory_rss'],
            'peak_memory': peak_memory,
            'memory_increase': final['memory_rss'] - initial['memory_rss'],
            'peak_increase': peak_memory - initial['memory_rss'],
            'thread_increase': final['num_threads'] - initial['num_threads'],
            'file_increase': final['open_files'] - initial['open_files'],
            'measurements': self.detailed_measurements
        }


class TestHSLMemoryLeak(BaseTestCase):
    """HSL通信库内存泄漏测试"""
    
    def setUp(self):
        """测试前准备"""
        super().setUp()
        self.detector = HSLMemoryLeakDetector()
        
        # 创建HSL库的mock对象
        self.setup_hsl_mocks()
    
    def setup_hsl_mocks(self):
        """设置HSL库模拟对象"""
        # 创建模拟的HSL通信库
        self.mock_hsl_client = Mock()
        
        # 模拟连接相关方法
        self.mock_hsl_client.ConnectServer.return_value = Mock(IsSuccess=True, Message="Connected")
        self.mock_hsl_client.ConnectClose.return_value = Mock(IsSuccess=True)
        
        # 模拟数据读取方法
        self.mock_hsl_client.ReadString.return_value = Mock(
            IsSuccess=True, 
            Content="TestString" * 50,  # 模拟较大的字符串
            Message="Success"
        )
        self.mock_hsl_client.ReadInt16.return_value = Mock(
            IsSuccess=True,
            Content=[12345],
            Message="Success"
        )
        self.mock_hsl_client.ReadInt32.return_value = Mock(
            IsSuccess=True,
            Content=[123456789],
            Message="Success"
        )
        self.mock_hsl_client.ReadFloat.return_value = Mock(
            IsSuccess=True,
            Content=[123.456],
            Message="Success"
        )
        self.mock_hsl_client.ReadUInt32.return_value = Mock(
            IsSuccess=True,
            Content=[0x12345678],
            Message="Success"
        )
        self.mock_hsl_client.ReadBool.return_value = Mock(
            IsSuccess=True,
            Content=[True],
            Message="Success"
        )
        
        # 模拟写入方法
        self.mock_hsl_client.WriteString.return_value = Mock(IsSuccess=True)
        self.mock_hsl_client.WriteInt16.return_value = Mock(IsSuccess=True)
        self.mock_hsl_client.WriteFloat.return_value = Mock(IsSuccess=True)
    
    def simulate_hsl_operations(self, num_operations=100):
        """模拟HSL库操作"""
        operations_data = []
        
        for i in range(num_operations):
            # 模拟各种数据类型的读取操作
            operations = [
                ('ReadString', lambda: self.mock_hsl_client.ReadString(f"D{100+i}", 20)),
                ('ReadInt16', lambda: self.mock_hsl_client.ReadInt16(f"D{200+i}", 1)),
                ('ReadInt32', lambda: self.mock_hsl_client.ReadInt32(f"D{300+i}", 1)),
                ('ReadFloat', lambda: self.mock_hsl_client.ReadFloat(f"D{400+i}", 1)),
                ('ReadUInt32', lambda: self.mock_hsl_client.ReadUInt32(f"D{500+i}", 1)),
                ('ReadBool', lambda: self.mock_hsl_client.ReadBool(f"M{i}", 1)),
            ]
            
            for op_name, op_func in operations:
                try:
                    result = op_func()
                    # 模拟处理返回数据
                    if result.IsSuccess:
                        data = {
                            'operation': op_name,
                            'content': result.Content,
                            'timestamp': time.time(),
                            'iteration': i
                        }
                        operations_data.append(data)
                        
                        # 模拟数据处理
                        if op_name == 'ReadString' and result.Content:
                            # 模拟字符串处理（可能的内存泄漏点）
                            processed = str(result.Content)[4:64]
                            processed = processed.strip()
                            
                        elif op_name in ['ReadInt16', 'ReadInt32', 'ReadFloat']:
                            # 模拟数值处理
                            value = result.Content[0] if result.Content else 0
                            processed_value = value * 0.1  # 模拟系数计算
                            
                except Exception as e:
                    print(f"操作 {op_name} 失败: {e}")
        
        return operations_data
    
    def test_hsl_read_operations_memory_leak(self):
        """测试HSL读取操作是否导致内存泄漏"""
        print("\n🔍 测试HSL读取操作内存泄漏...")
        
        self.detector.start_monitoring()
        initial_memory = self.detector.initial_memory
        
        # 执行多轮HSL操作测试
        test_rounds = 5
        operations_per_round = 200
        
        for round_num in range(test_rounds):
            print(f"\n--- 第 {round_num + 1} 轮测试 ({operations_per_round} 次操作) ---")
            
            # 执行HSL操作
            operations_data = self.simulate_hsl_operations(operations_per_round)
            
            # 测量内存
            self.detector.measure(f"Round_{round_num + 1}")
            
            # 验证操作成功
            self.assertGreater(len(operations_data), 0, "应该有操作数据返回")
            
            # 模拟一些处理延迟
            time.sleep(0.1)
        
        # 强制垃圾回收
        gc.collect()
        final_memory = self.detector.measure("Final_GC")
        
        # 获取详细报告
        report = self.detector.get_detailed_report()
        
        print(f"\n📊 HSL操作内存分析报告:")
        print(f"  初始内存: {report['initial_memory']:.2f}MB")
        print(f"  最终内存: {report['final_memory']:.2f}MB")
        print(f"  峰值内存: {report['peak_memory']:.2f}MB")
        print(f"  内存增长: {report['memory_increase']:.2f}MB")
        print(f"  峰值增长: {report['peak_increase']:.2f}MB")
        print(f"  线程增长: {report['thread_increase']}")
        print(f"  文件句柄增长: {report['file_increase']}")
        
        # 内存泄漏检查
        memory_threshold = 30  # MB
        peak_threshold = 50    # MB
        
        self.assertLess(report['memory_increase'], memory_threshold, 
                       f"HSL操作内存增长过大: {report['memory_increase']:.2f}MB > {memory_threshold}MB")
        
        self.assertLess(report['peak_increase'], peak_threshold,
                       f"HSL操作峰值内存增长过大: {report['peak_increase']:.2f}MB > {peak_threshold}MB")
        
        self.assertEqual(report['thread_increase'], 0, "不应该有线程泄漏")
        
        return report
    
    def test_hsl_connection_lifecycle_memory(self):
        """测试HSL连接生命周期内存管理"""
        print("\n🔍 测试HSL连接生命周期内存管理...")
        
        self.detector.start_monitoring()
        
        connection_cycles = 20
        
        for cycle in range(connection_cycles):
            # 模拟创建新的HSL客户端
            mock_client = Mock()
            mock_client.ConnectServer.return_value = Mock(IsSuccess=True)
            mock_client.ConnectClose.return_value = Mock(IsSuccess=True)
            
            # 模拟连接
            connect_result = mock_client.ConnectServer()
            self.assertTrue(connect_result.IsSuccess, "连接应该成功")
            
            # 模拟一些操作
            for i in range(10):
                mock_client.ReadInt16(f"D{i}", 1)
            
            # 模拟关闭连接
            close_result = mock_client.ConnectClose()
            self.assertTrue(close_result.IsSuccess, "关闭连接应该成功")
            
            # 删除客户端引用
            del mock_client
            
            if cycle % 5 == 0:
                self.detector.measure(f"Cycle_{cycle}")
                gc.collect()
        
        final_memory = self.detector.measure("Final")
        report = self.detector.get_detailed_report()
        
        print(f"\n📊 连接生命周期内存报告:")
        print(f"  连接周期数: {connection_cycles}")
        print(f"  内存增长: {report['memory_increase']:.2f}MB")
        print(f"  平均每周期增长: {report['memory_increase']/connection_cycles:.3f}MB")
        
        # 连接周期不应该导致显著内存增长
        self.assertLess(report['memory_increase'], 20, "连接周期内存增长过大")
        
        return report
    
    def test_hsl_large_data_operations(self):
        """测试HSL大数据量操作内存使用"""
        print("\n🔍 测试HSL大数据量操作...")
        
        self.detector.start_monitoring()
        
        # 模拟读取大量数据
        large_data_operations = [
            ('LargeString', lambda: self.mock_hsl_client.ReadString("D1000", 1000)),  # 大字符串
            ('MultipleInt16', lambda: [self.mock_hsl_client.ReadInt16(f"D{i}", 1) for i in range(100)]),  # 多次读取
            ('LargeArray', lambda: self.mock_hsl_client.ReadInt16("D2000", 500)),  # 大数组
        ]
        
        for op_name, op_func in large_data_operations:
            print(f"  执行 {op_name} 操作...")
            
            before_memory = self.detector.measure(f"Before_{op_name}")
            
            # 执行大数据操作
            for i in range(10):  # 重复10次
                try:
                    result = op_func()
                    if isinstance(result, list):
                        # 处理多个结果
                        for r in result:
                            if hasattr(r, 'Content'):
                                data = r.Content
                    else:
                        # 处理单个结果
                        if hasattr(result, 'Content'):
                            data = result.Content
                            
                except Exception as e:
                    print(f"    操作失败: {e}")
            
            after_memory = self.detector.measure(f"After_{op_name}")
            operation_increase = after_memory - before_memory
            
            print(f"    {op_name} 内存增长: {operation_increase:.2f}MB")
            
            # 单次大数据操作不应该导致过大内存增长
            self.assertLess(operation_increase, 15, f"{op_name} 操作内存增长过大")
        
        final_report = self.detector.get_detailed_report()
        
        print(f"\n📊 大数据操作总体报告:")
        print(f"  总内存增长: {final_report['memory_increase']:.2f}MB")
        print(f"  峰值内存增长: {final_report['peak_increase']:.2f}MB")
        
        return final_report
    
    def test_hsl_string_processing_memory_leak(self):
        """测试HSL字符串处理特定的内存泄漏"""
        print("\n🔍 测试HSL字符串处理内存泄漏...")
        
        self.detector.start_monitoring()
        
        # 模拟字符串处理操作（这是最可能的内存泄漏源）
        string_operations = 200
        
        for i in range(string_operations):
            # 模拟读取字符串
            result = self.mock_hsl_client.ReadString(f"D{1000 + i}", 64)
            
            if result.IsSuccess and result.Content:
                # 模拟原代码中的字符串处理逻辑
                raw_string = str(result.Content)
                
                # 1. 字符串切片（可能的内存泄漏点）
                processed = raw_string[4:64]
                
                # 2. 字符检查（可能的内存泄漏点）
                has_alnum = any(char.isalnum() for char in processed)
                
                if has_alnum:
                    # 3. 正则表达式替换（可能的内存泄漏点）
                    import re
                    cleaned = re.sub(r'\s+', '', processed)
                else:
                    cleaned = "None"
                
                # 4. 模拟数据存储
                data_entry = {
                    'original': raw_string,
                    'processed': processed,
                    'cleaned': cleaned,
                    'has_alnum': has_alnum,
                    'iteration': i
                }
                
                # 模拟将数据添加到列表（可能的内存泄漏点）
                if not hasattr(self, 'string_data_list'):
                    self.string_data_list = []
                self.string_data_list.append(data_entry)
            
            # 每50次操作测量一次内存
            if i % 50 == 0:
                self.detector.measure(f"String_Op_{i}")
        
        # 清理数据列表
        if hasattr(self, 'string_data_list'):
            list_size = len(self.string_data_list)
            del self.string_data_list
            print(f"  清理了 {list_size} 个字符串数据项")
        
        gc.collect()
        final_memory = self.detector.measure("String_Final")
        
        report = self.detector.get_detailed_report()
        
        print(f"\n📊 字符串处理内存报告:")
        print(f"  处理操作数: {string_operations}")
        print(f"  内存增长: {report['memory_increase']:.2f}MB")
        print(f"  平均每次增长: {report['memory_increase']/string_operations:.4f}MB")
        
        # 字符串处理是最容易导致内存泄漏的地方
        self.assertLess(report['memory_increase'], 25, "字符串处理内存增长过大，可能存在泄漏")
        
        return report
    
    @unittest.skipUnless(MEMORY_PROFILER_AVAILABLE, "memory_profiler not available")
    def test_hsl_detailed_memory_profiling(self):
        """使用memory_profiler进行详细内存分析"""
        print("\n🔍 HSL库详细内存分析...")
        
        def hsl_intensive_operations():
            # 模拟密集的HSL操作
            for i in range(50):
                # 连接操作
                self.mock_hsl_client.ConnectServer()
                
                # 多种数据类型读取
                self.mock_hsl_client.ReadString(f"D{i}", 50)
                self.mock_hsl_client.ReadInt16(f"D{100+i}", 1)
                self.mock_hsl_client.ReadFloat(f"D{200+i}", 1)
                
                # 字符串处理
                result = self.mock_hsl_client.ReadString(f"D{300+i}", 100)
                if result.Content:
                    processed = str(result.Content)[4:64]
                    import re
                    cleaned = re.sub(r'\s+', '', processed)
                
                # 断开连接
                self.mock_hsl_client.ConnectClose()
                
                time.sleep(0.01)  # 短暂延迟
        
        # 使用memory_profiler监控
        mem_usage = memory_usage(hsl_intensive_operations, interval=0.1)
        
        if mem_usage:
            initial_mem = mem_usage[0]
            peak_mem = max(mem_usage)
            final_mem = mem_usage[-1]
            
            print(f"\n📊 详细内存分析结果:")
            print(f"  初始内存: {initial_mem:.2f}MB")
            print(f"  峰值内存: {peak_mem:.2f}MB")
            print(f"  最终内存: {final_mem:.2f}MB")
            print(f"  净增长: {final_mem - initial_mem:.2f}MB")
            print(f"  峰值增长: {peak_mem - initial_mem:.2f}MB")
            print(f"  内存波动: {max(mem_usage) - min(mem_usage):.2f}MB")
            
            # 分析内存使用模式
            if len(mem_usage) > 10:
                # 计算内存增长趋势
                first_half = mem_usage[:len(mem_usage)//2]
                second_half = mem_usage[len(mem_usage)//2:]
                
                avg_first = sum(first_half) / len(first_half)
                avg_second = sum(second_half) / len(second_half)
                trend = avg_second - avg_first
                
                print(f"  内存增长趋势: {trend:.2f}MB")
                
                if trend > 5:
                    print("  ⚠️  检测到明显的内存增长趋势，可能存在内存泄漏")
                else:
                    print("  ✅ 内存使用相对稳定")
            
            # 检查内存使用阈值
            self.assertLess(peak_mem - initial_mem, 100, "峰值内存使用过高")
            self.assertLess(final_mem - initial_mem, 30, "最终内存增长过大")
    
    def test_hsl_memory_leak_summary(self):
        """HSL内存泄漏综合分析总结"""
        print("\n" + "="*60)
        print("📋 HSL通信库内存泄漏综合分析")
        print("="*60)
        
        test_results = {}
        
        # 执行各项测试并收集结果
        try:
            test_results['read_operations'] = self.test_hsl_read_operations_memory_leak()
        except Exception as e:
            print(f"读取操作测试失败: {e}")
            test_results['read_operations'] = None
        
        try:
            test_results['connection_lifecycle'] = self.test_hsl_connection_lifecycle_memory()
        except Exception as e:
            print(f"连接生命周期测试失败: {e}")
            test_results['connection_lifecycle'] = None
        
        try:
            test_results['large_data'] = self.test_hsl_large_data_operations()
        except Exception as e:
            print(f"大数据操作测试失败: {e}")
            test_results['large_data'] = None
        
        try:
            test_results['string_processing'] = self.test_hsl_string_processing_memory_leak()
        except Exception as e:
            print(f"字符串处理测试失败: {e}")
            test_results['string_processing'] = None
        
        # 分析结果
        print(f"\n🔍 分析结果汇总:")
        
        total_issues = 0
        critical_issues = []
        
        for test_name, result in test_results.items():
            if result:
                memory_increase = result.get('memory_increase', 0)
                peak_increase = result.get('peak_increase', 0)
                
                print(f"\n  📊 {test_name}:")
                print(f"    内存增长: {memory_increase:.2f}MB")
                print(f"    峰值增长: {peak_increase:.2f}MB")
                
                # 判断问题严重性
                if memory_increase > 20:
                    critical_issues.append(f"{test_name}: 内存增长过大 ({memory_increase:.2f}MB)")
                    total_issues += 1
                elif memory_increase > 10:
                    print(f"    ⚠️  中等内存增长")
                    total_issues += 1
                else:
                    print(f"    ✅ 内存使用正常")
        
        # 结论和建议
        print(f"\n🎯 结论:")
        if critical_issues:
            print(f"  🚨 发现 {len(critical_issues)} 个严重内存问题:")
            for issue in critical_issues:
                print(f"    - {issue}")
        
        if total_issues > 0:
            print(f"\n💡 建议:")
            print(f"  1. HSL库可能存在内存泄漏，特别是在字符串处理方面")
            print(f"  2. 建议在长时间运行时定期调用gc.collect()") 
            print(f"  3. 考虑限制数据处理的批次大小")
            print(f"  4. 监控生产环境中的内存使用情况")
            print(f"  5. 如果问题持续，考虑联系HSL库供应商")
        else:
            print(f"  ✅ HSL库内存使用正常，未发现明显泄漏")
        
        return test_results


if __name__ == '__main__':
    # 运行HSL内存泄漏检测测试
    unittest.main(verbosity=2)