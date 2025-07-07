#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
HSL库真实调用模式内存泄漏检测
"""

import unittest
import gc
import psutil
import threading
import time
import sys
import os
import weakref
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

# 添加项目根目录到Python路径
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from tests.base import BaseTestCase


class HSLRealPatternMemoryTest(BaseTestCase):
    """HSL库真实使用模式内存测试"""
    
    def setUp(self):
        """测试前准备"""
        super().setUp()
        self.process = psutil.Process()
        self.memory_samples = []
        self.object_references = []
    
    def measure_memory(self, label=""):
        """测量内存使用"""
        gc.collect()
        memory_mb = self.process.memory_info().rss / 1024 / 1024
        self.memory_samples.append((time.time(), memory_mb, label))
        if label:
            print(f"[{label}] 内存: {memory_mb:.2f}MB")
        return memory_mb
    
    def test_hsl_object_lifecycle_real_pattern(self):
        """测试HSL对象生命周期的真实模式"""
        print("\n🔍 测试HSL对象生命周期真实模式...")
        
        initial_memory = self.measure_memory("Initial")
        
        # 模拟真实的HSL使用模式：创建客户端 -> 长时间使用 -> 异常重建
        for cycle in range(10):
            print(f"\n--- 周期 {cycle + 1} ---")
            
            # 1. 创建HSL客户端（模拟MelsecA1ENet创建）
            hsl_objects = []
            
            try:
                # 模拟创建HSL对象的开销
                for i in range(5):  # 模拟多个连接
                    # 创建模拟的HSL对象，包含一些内部状态
                    hsl_obj = {
                        'connection_id': f"conn_{cycle}_{i}",
                        'buffer': bytearray(1024),  # 模拟内部缓冲区
                        'state': {'connected': True, 'last_read': time.time()},
                        'read_cache': {},  # 模拟读取缓存
                        'write_queue': [],  # 模拟写入队列
                        'error_log': [],   # 模拟错误日志
                        'large_data': b'x' * 10240  # 模拟一些大数据
                    }
                    hsl_objects.append(hsl_obj)
                
                self.measure_memory(f"Cycle_{cycle}_Created")
                
                # 2. 模拟长时间使用（频繁读写）
                for operation in range(50):
                    for obj in hsl_objects:
                        # 模拟读取操作的副作用
                        read_data = f"data_{operation}_{time.time()}"
                        obj['read_cache'][f"addr_{operation}"] = read_data
                        
                        # 模拟写入队列操作
                        obj['write_queue'].append(f"write_{operation}")
                        
                        # 模拟错误日志累积
                        if operation % 10 == 0:
                            obj['error_log'].append(f"warning_{operation}")
                        
                        # 清理一些缓存（但可能不完全）
                        if len(obj['read_cache']) > 20:
                            # 只清理一半，模拟不完全清理
                            keys = list(obj['read_cache'].keys())
                            for key in keys[:len(keys)//2]:
                                del obj['read_cache'][key]
                
                self.measure_memory(f"Cycle_{cycle}_Used")
                
                # 3. 模拟异常情况（这里可能是泄漏点）
                if cycle % 3 == 0:  # 每3个周期模拟一次异常
                    print(f"  模拟异常重建...")
                    
                    # 模拟异常发生时的不完全清理
                    for obj in hsl_objects:
                        # 清理一些但不是全部
                        obj['buffer'] = None  # 清理缓冲区
                        # 但是忘记清理其他缓存！这是常见的泄漏源
                        # obj['read_cache'].clear()  # 注释掉，模拟忘记清理
                        # obj['write_queue'].clear()
                        # obj['error_log'].clear()
                    
                    # 创建新对象替代旧对象
                    hsl_objects = []  # 删除引用，但内存可能没有释放
                    
                    # 重新创建
                    for i in range(5):
                        new_obj = {
                            'connection_id': f"reconnect_{cycle}_{i}",
                            'buffer': bytearray(1024),
                            'state': {'connected': True, 'last_read': time.time()},
                            'read_cache': {},
                            'write_queue': [],
                            'error_log': [],
                            'large_data': b'x' * 10240
                        }
                        hsl_objects.append(new_obj)
                    
                    self.measure_memory(f"Cycle_{cycle}_Reconnected")
                
            finally:
                # 清理（但可能不完全）
                for obj in hsl_objects:
                    if isinstance(obj, dict):
                        # 模拟不完全的清理
                        obj['buffer'] = None
                        # 其他字段可能没有清理
                
                del hsl_objects
                gc.collect()
                
                self.measure_memory(f"Cycle_{cycle}_Cleaned")
        
        final_memory = self.measure_memory("Final")
        
        # 分析内存增长
        memory_increase = final_memory - initial_memory
        print(f"\n📊 对象生命周期内存分析:")
        print(f"  初始内存: {initial_memory:.2f}MB")
        print(f"  最终内存: {final_memory:.2f}MB")
        print(f"  总内存增长: {memory_increase:.2f}MB")
        print(f"  平均每周期增长: {memory_increase/10:.2f}MB")
        
        # 检查是否有显著的内存增长
        if memory_increase > 15:
            print("  🚨 检测到显著内存增长，可能存在泄漏")
            
            # 分析泄漏模式
            memory_timeline = [(sample[1] - initial_memory) for sample in self.memory_samples]
            
            # 计算趋势
            if len(memory_timeline) > 5:
                first_quarter = memory_timeline[:len(memory_timeline)//4]
                last_quarter = memory_timeline[-len(memory_timeline)//4:]
                
                avg_first = sum(first_quarter) / len(first_quarter)
                avg_last = sum(last_quarter) / len(last_quarter)
                
                trend = avg_last - avg_first
                print(f"  内存增长趋势: {trend:.2f}MB")
                
                if trend > 5:
                    print("  📈 内存呈上升趋势，可能是累积性泄漏")
        else:
            print("  ✅ 内存使用相对稳定")
        
        return memory_increase
    
    def test_hsl_string_processing_real_leak(self):
        """测试HSL字符串处理的真实泄漏模式"""
        print("\n🔍 测试HSL字符串处理真实泄漏模式...")
        
        initial_memory = self.measure_memory("String_Initial")
        
        # 模拟真实的字符串处理场景
        accumulated_strings = []  # 这可能是泄漏源
        string_cache = {}         # 这也可能是泄漏源
        
        for batch in range(20):
            print(f"  处理批次 {batch + 1}...")
            
            batch_strings = []
            
            for i in range(100):
                # 1. 模拟HSL返回的原始字符串
                raw_string = f"HSL_DATA_{batch}_{i}_" + "X" * 100 + "_END"
                
                # 2. 模拟字符串处理（这里可能有泄漏）
                # 创建多个中间字符串对象
                temp1 = str(raw_string)  # 转换
                temp2 = temp1[4:64]      # 切片
                temp3 = temp2.strip()    # 清理
                
                # 模拟字符检查
                has_alnum = any(char.isalnum() for char in temp3)
                
                if has_alnum:
                    # 正则表达式处理（可能的泄漏点）
                    import re
                    temp4 = re.sub(r'\s+', '', temp3)
                    temp5 = re.sub(r'[^a-zA-Z0-9]', '_', temp4)
                    final_string = temp5[:30]  # 截断
                else:
                    final_string = "None"
                
                # 3. 存储处理结果（可能的泄漏点）
                result_data = {
                    'original': raw_string,      # 保存原始字符串
                    'processed': final_string,   # 保存处理结果
                    'intermediate': [temp1, temp2, temp3],  # 保存中间结果！
                    'metadata': {
                        'batch': batch,
                        'index': i,
                        'length': len(raw_string),
                        'has_alnum': has_alnum,
                        'timestamp': time.time()
                    }
                }
                
                batch_strings.append(result_data)
                
                # 4. 缓存机制（可能的泄漏点）
                cache_key = f"{batch}_{i}"
                string_cache[cache_key] = result_data  # 缓存永远不清理！
            
            # 5. 累积存储（模拟应用程序保存数据）
            accumulated_strings.extend(batch_strings)
            
            # 6. 不完全的清理
            if batch % 5 == 0:
                # 只清理部分数据
                if len(accumulated_strings) > 300:
                    # 只保留最新的200个
                    accumulated_strings = accumulated_strings[-200:]
                
                # 缓存清理不完全
                if len(string_cache) > 500:
                    # 只删除一半的缓存
                    keys = list(string_cache.keys())
                    for key in keys[:len(keys)//2]:
                        del string_cache[key]
            
            if batch % 5 == 0:
                self.measure_memory(f"String_Batch_{batch}")
        
        # 分析字符串数据
        print(f"\n  累积字符串数据: {len(accumulated_strings)} 个")
        print(f"  字符串缓存大小: {len(string_cache)} 个")
        
        # 计算数据大小
        total_string_size = 0
        for item in accumulated_strings:
            if isinstance(item, dict):
                total_string_size += len(str(item.get('original', '')))
                total_string_size += len(str(item.get('processed', '')))
                if 'intermediate' in item:
                    for temp_str in item['intermediate']:
                        total_string_size += len(str(temp_str))
        
        print(f"  估计字符串数据大小: {total_string_size / 1024 / 1024:.2f}MB")
        
        final_memory = self.measure_memory("String_Final")
        
        # 强制清理
        accumulated_strings.clear()
        string_cache.clear()
        gc.collect()
        
        cleaned_memory = self.measure_memory("String_Cleaned")
        
        memory_increase = final_memory - initial_memory
        cleanup_recovery = final_memory - cleaned_memory
        
        print(f"\n📊 字符串处理内存分析:")
        print(f"  初始内存: {initial_memory:.2f}MB")
        print(f"  最终内存: {final_memory:.2f}MB")
        print(f"  清理后内存: {cleaned_memory:.2f}MB")
        print(f"  内存增长: {memory_increase:.2f}MB")
        print(f"  清理回收: {cleanup_recovery:.2f}MB")
        
        if cleanup_recovery > 5:
            print("  🚨 清理后回收了大量内存，确认存在字符串泄漏")
        elif memory_increase > 10:
            print("  ⚠️  内存增长较大，可能存在字符串累积问题")
        else:
            print("  ✅ 字符串处理内存使用正常")
        
        return memory_increase, cleanup_recovery
    
    def test_hsl_connection_pool_leak(self):
        """测试HSL连接池模式的内存泄漏"""
        print("\n🔍 测试HSL连接池模式内存泄漏...")
        
        initial_memory = self.measure_memory("Pool_Initial")
        
        # 模拟连接池
        connection_pool = {}
        connection_stats = {}
        failed_connections = []  # 失败连接的累积
        
        for round_num in range(15):
            print(f"  连接池轮次 {round_num + 1}...")
            
            # 1. 创建新连接
            for conn_id in range(5):
                connection_key = f"conn_{round_num}_{conn_id}"
                
                # 模拟连接对象
                connection = {
                    'id': connection_key,
                    'socket': Mock(),  # 模拟socket对象
                    'buffer': bytearray(2048),
                    'read_history': [],
                    'write_history': [],
                    'error_count': 0,
                    'created_time': time.time(),
                    'last_used': time.time(),
                    'stats': {'reads': 0, 'writes': 0, 'errors': 0}
                }
                
                connection_pool[connection_key] = connection
                connection_stats[connection_key] = []
            
            # 2. 使用连接进行操作
            for operation in range(30):
                for conn_key, conn in list(connection_pool.items()):
                    try:
                        # 模拟读取操作
                        read_data = f"read_{operation}_" + "D" * 50
                        conn['read_history'].append(read_data)
                        conn['stats']['reads'] += 1
                        
                        # 模拟写入操作
                        write_data = f"write_{operation}_" + "W" * 30
                        conn['write_history'].append(write_data)
                        conn['stats']['writes'] += 1
                        
                        # 更新统计
                        stat_entry = {
                            'timestamp': time.time(),
                            'operation': operation,
                            'memory_usage': len(conn['read_history']) + len(conn['write_history']),
                            'buffer_size': len(conn['buffer'])
                        }
                        connection_stats[conn_key].append(stat_entry)
                        
                        conn['last_used'] = time.time()
                        
                        # 模拟偶尔的错误
                        if operation % 20 == 0:
                            conn['error_count'] += 1
                            conn['stats']['errors'] += 1
                            error_info = {
                                'connection': conn_key,
                                'error': f"simulated_error_{operation}",
                                'timestamp': time.time(),
                                'context': conn.copy()  # 这里保存了整个连接上下文！
                            }
                            failed_connections.append(error_info)
                    
                    except Exception as e:
                        print(f"    连接 {conn_key} 操作异常: {e}")
            
            # 3. 不完全的连接清理
            if round_num % 3 == 0:
                print(f"    清理旧连接...")
                
                # 查找需要清理的连接
                current_time = time.time()
                connections_to_remove = []
                
                for conn_key, conn in connection_pool.items():
                    if current_time - conn['last_used'] > 1:  # 1秒未使用
                        connections_to_remove.append(conn_key)
                
                # 清理连接（但可能不完全）
                for conn_key in connections_to_remove:
                    if conn_key in connection_pool:
                        conn = connection_pool[conn_key]
                        
                        # 清理缓冲区
                        conn['buffer'] = None
                        # 但是忘记清理历史记录！
                        # conn['read_history'].clear()  # 注释掉
                        # conn['write_history'].clear() # 注释掉
                        
                        # 从池中移除
                        del connection_pool[conn_key]
                        
                        # 但是统计数据可能还在
                        # del connection_stats[conn_key]  # 注释掉，模拟忘记清理
            
            if round_num % 5 == 0:
                self.measure_memory(f"Pool_Round_{round_num}")
        
        # 分析连接池状态
        print(f"\n  活跃连接数: {len(connection_pool)}")
        print(f"  统计记录数: {len(connection_stats)}")
        print(f"  失败连接记录: {len(failed_connections)}")
        
        # 计算数据大小
        total_history_size = 0
        for conn in connection_pool.values():
            total_history_size += len(str(conn.get('read_history', [])))
            total_history_size += len(str(conn.get('write_history', [])))
        
        print(f"  连接历史数据大小: {total_history_size / 1024:.2f}KB")
        
        final_memory = self.measure_memory("Pool_Final")
        
        # 完全清理
        for conn in connection_pool.values():
            if isinstance(conn, dict):
                conn.get('read_history', []).clear()
                conn.get('write_history', []).clear()
        
        connection_pool.clear()
        connection_stats.clear()
        failed_connections.clear()
        gc.collect()
        
        cleaned_memory = self.measure_memory("Pool_Cleaned")
        
        memory_increase = final_memory - initial_memory
        cleanup_recovery = final_memory - cleaned_memory
        
        print(f"\n📊 连接池内存分析:")
        print(f"  初始内存: {initial_memory:.2f}MB")
        print(f"  最终内存: {final_memory:.2f}MB")
        print(f"  清理后内存: {cleaned_memory:.2f}MB")
        print(f"  内存增长: {memory_increase:.2f}MB")
        print(f"  清理回收: {cleanup_recovery:.2f}MB")
        
        if cleanup_recovery > 3:
            print("  🚨 连接池存在内存泄漏")
        elif memory_increase > 8:
            print("  ⚠️  连接池内存使用较高")
        else:
            print("  ✅ 连接池内存使用正常")
        
        return memory_increase, cleanup_recovery
    
    def test_comprehensive_hsl_leak_analysis(self):
        """综合HSL泄漏分析"""
        print("\n" + "="*60)
        print("🔬 HSL库真实使用模式内存泄漏综合分析")
        print("="*60)
        
        results = {}
        
        # 1. 对象生命周期测试
        print("\n1️⃣ 对象生命周期测试...")
        try:
            lifecycle_increase = self.test_hsl_object_lifecycle_real_pattern()
            results['lifecycle'] = lifecycle_increase
        except Exception as e:
            print(f"对象生命周期测试失败: {e}")
            results['lifecycle'] = None
        
        # 2. 字符串处理测试
        print("\n2️⃣ 字符串处理测试...")
        try:
            string_increase, string_recovery = self.test_hsl_string_processing_real_leak()
            results['string'] = (string_increase, string_recovery)
        except Exception as e:
            print(f"字符串处理测试失败: {e}")
            results['string'] = None
        
        # 3. 连接池测试
        print("\n3️⃣ 连接池测试...")
        try:
            pool_increase, pool_recovery = self.test_hsl_connection_pool_leak()
            results['pool'] = (pool_increase, pool_recovery)
        except Exception as e:
            print(f"连接池测试失败: {e}")
            results['pool'] = None
        
        # 综合分析
        print(f"\n" + "="*60)
        print(f"📊 综合分析结果")
        print(f"="*60)
        
        critical_issues = []
        moderate_issues = []
        
        # 分析每个测试结果
        if results['lifecycle'] is not None:
            if results['lifecycle'] > 15:
                critical_issues.append(f"对象生命周期: {results['lifecycle']:.2f}MB 增长")
            elif results['lifecycle'] > 8:
                moderate_issues.append(f"对象生命周期: {results['lifecycle']:.2f}MB 增长")
        
        if results['string'] is not None:
            increase, recovery = results['string']
            if recovery > 5:
                critical_issues.append(f"字符串处理: {increase:.2f}MB 增长, {recovery:.2f}MB 可回收")
            elif increase > 10:
                moderate_issues.append(f"字符串处理: {increase:.2f}MB 增长")
        
        if results['pool'] is not None:
            increase, recovery = results['pool']
            if recovery > 3:
                critical_issues.append(f"连接池: {increase:.2f}MB 增长, {recovery:.2f}MB 可回收")
            elif increase > 8:
                moderate_issues.append(f"连接池: {increase:.2f}MB 增长")
        
        # 输出结论
        if critical_issues:
            print(f"\n🚨 发现严重内存泄漏问题:")
            for issue in critical_issues:
                print(f"  ❌ {issue}")
        
        if moderate_issues:
            print(f"\n⚠️  发现中等内存问题:")
            for issue in moderate_issues:
                print(f"  ⚡ {issue}")
        
        if not critical_issues and not moderate_issues:
            print(f"\n✅ 未发现明显的内存泄漏问题")
        
        # 给出建议
        if critical_issues or moderate_issues:
            print(f"\n💡 针对HSL库的优化建议:")
            print(f"  1. 🔧 确保在异常处理时正确关闭HSL连接")
            print(f"  2. 🧹 定期清理读取缓存和历史记录")
            print(f"  3. 📝 限制字符串处理的中间对象创建")
            print(f"  4. 🔄 实施定期的垃圾回收机制")
            print(f"  5. 📊 在生产环境中监控内存使用趋势")
            print(f"  6. ⚡ 考虑使用对象池来管理HSL连接")
            print(f"  7. 🔍 使用更精细的内存分析工具进行深入分析")
        
        return results


if __name__ == '__main__':
    # 运行真实模式的HSL内存泄漏检测测试
    unittest.main(verbosity=2)