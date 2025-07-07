#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
内存泄漏静态分析 - connect_melseca1enet_backu
"""

import unittest
import ast
import re
import sys
import os
from pathlib import Path
from typing import List, Dict, Any

# 添加项目根目录到Python路径
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from tests.base import BaseTestCase


class MemoryLeakStaticAnalyzer:
    """内存泄漏静态分析器"""
    
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.source_code = None
        self.ast_tree = None
        self.issues = []
        self.suggestions = []
        
    def load_source(self):
        """加载源代码"""
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                self.source_code = f.read()
            self.ast_tree = ast.parse(self.source_code)
            return True
        except Exception as e:
            print(f"加载源代码失败: {e}")
            return False
    
    def analyze_connection_management(self):
        """分析连接管理问题"""
        print("🔍 分析连接管理...")
        
        # 检查是否有析构函数
        has_destructor = '__del__' in self.source_code
        if not has_destructor:
            self.issues.append({
                "type": "连接管理",
                "severity": "高",
                "issue": "MelsecA1ENetClient类缺少__del__析构函数",
                "description": "没有析构函数可能导致PLC连接、InfluxDB连接和Kafka连接无法正确关闭",
                "line": "类定义处"
            })
            self.suggestions.append("添加__del__方法确保所有连接正确关闭")
        
        # 检查连接重建逻辑
        reconnect_pattern = r'self\.plc\s*=\s*MelsecA1ENet'
        reconnect_matches = re.findall(reconnect_pattern, self.source_code)
        if len(reconnect_matches) > 1:
            self.issues.append({
                "type": "连接管理", 
                "severity": "高",
                "issue": f"发现{len(reconnect_matches)}处PLC连接重建",
                "description": "在异常处理中重建连接但未先关闭旧连接，可能造成连接泄漏",
                "line": "异常处理代码块"
            })
            self.suggestions.append("在重建连接前先调用ConnectClose()关闭旧连接")
    
    def analyze_string_operations(self):
        """分析字符串操作问题"""
        print("🔍 分析字符串操作...")
        
        # 检查大字符串操作
        large_string_operations = [
            r'str\(.*\.ReadString\(.*\)\).*\[4:64\]',  # 字符串切片
            r're\.sub\(',  # 正则替换
            r'\.Content\)',  # 多次Content访问
        ]
        
        for pattern in large_string_operations:
            matches = re.findall(pattern, self.source_code)
            if matches:
                self.issues.append({
                    "type": "字符串处理",
                    "severity": "中",
                    "issue": f"发现{len(matches)}处可能的内存密集型字符串操作",
                    "description": "大量字符串处理和正则操作可能创建很多临时对象",
                    "line": "read_plc方法中"
                })
        
        # 检查字符串拼接
        string_concat_pattern = r'".*"\s*\+\s*.*\+\s*".*"'
        concat_matches = re.findall(string_concat_pattern, self.source_code)
        if concat_matches:
            self.suggestions.append("使用f-string或join方法替代字符串拼接以提高性能")
    
    def analyze_loop_and_iteration(self):
        """分析循环和迭代问题"""
        print("🔍 分析循环和迭代...")
        
        # 检查无限循环
        infinite_loop_pattern = r'while\s+True:'
        infinite_loops = re.findall(infinite_loop_pattern, self.source_code)
        if infinite_loops:
            self.issues.append({
                "type": "循环控制",
                "severity": "高", 
                "issue": f"发现{len(infinite_loops)}处无限循环",
                "description": "主程序和write_plc中的无限循环可能导致资源无法释放",
                "line": "__main__和write_plc方法"
            })
            self.suggestions.append("为无限循环添加适当的退出条件和资源清理逻辑")
        
        # 检查循环中的对象创建
        loop_object_creation = [
            r'for.*in.*:.*Log\(\)',  # 循环中创建Log对象
            r'for.*in.*:.*\.append\(',  # 循环中append操作
        ]
        
        for pattern in loop_object_creation:
            matches = re.findall(pattern, self.source_code, re.DOTALL)
            if matches:
                self.issues.append({
                    "type": "循环优化",
                    "severity": "中",
                    "issue": "循环中创建对象或进行内存分配",
                    "description": "循环中频繁创建对象可能导致内存使用增长",
                    "line": "read_plc方法循环中"
                })
    
    def analyze_exception_handling(self):
        """分析异常处理问题"""
        print("🔍 分析异常处理...")
        
        # 检查异常处理中的资源管理
        exception_blocks = re.findall(r'except.*?:(.*?)(?=\n\s*(?:except|else|finally|\n\S))', 
                                     self.source_code, re.DOTALL)
        
        resource_cleanup_found = False
        for block in exception_blocks:
            if 'ConnectClose' in block or 'close' in block:
                resource_cleanup_found = True
                break
        
        if not resource_cleanup_found:
            self.issues.append({
                "type": "异常处理",
                "severity": "高",
                "issue": "异常处理中缺少资源清理",
                "description": "异常发生时可能导致连接和资源无法正确释放",
                "line": "所有except块"
            })
            self.suggestions.append("在异常处理中添加资源清理代码")
    
    def analyze_data_structures(self):
        """分析数据结构使用"""
        print("🔍 分析数据结构使用...")
        
        # 检查列表和字典的使用模式
        if 'tag_data = []' in self.source_code:
            # 检查是否有合理的列表大小控制
            if 'tag_data.clear()' not in self.source_code and 'del tag_data' not in self.source_code:
                self.issues.append({
                    "type": "数据结构",
                    "severity": "中",
                    "issue": "列表tag_data可能无限增长",
                    "description": "在长时间运行中，tag_data列表可能积累大量数据而不清理",
                    "line": "read_plc方法"
                })
                self.suggestions.append("定期清理或限制tag_data列表大小")
        
        # 检查字典创建模式
        dict_creation_pattern = r'plc_data\s*=\s*{}'
        dict_matches = re.findall(dict_creation_pattern, self.source_code)
        if len(dict_matches) > 5:
            self.suggestions.append("考虑重用字典对象而不是每次都创建新的")
    
    def analyze_third_party_integrations(self):
        """分析第三方集成问题"""
        print("🔍 分析第三方集成...")
        
        # 检查Kafka集成
        if 'KafkaProducer' in self.source_code:
            if 'kafka_producer.close()' not in self.source_code:
                self.issues.append({
                    "type": "第三方集成",
                    "severity": "中",
                    "issue": "Kafka Producer未显式关闭",
                    "description": "KafkaProducer对象可能在程序结束时未正确关闭",
                    "line": "__init__方法"
                })
                self.suggestions.append("在析构函数中关闭KafkaProducer")
        
        # 检查InfluxDB集成  
        if 'InfluxClient' in self.source_code:
            if 'influxdb_client.close()' not in self.source_code:
                self.issues.append({
                    "type": "第三方集成", 
                    "severity": "中",
                    "issue": "InfluxDB客户端未显式关闭",
                    "description": "InfluxDB连接可能在程序结束时未正确关闭",
                    "line": "__init__方法"
                })
                self.suggestions.append("在析构函数中关闭InfluxDB连接")
    
    def analyze_memory_patterns(self):
        """分析内存使用模式"""
        print("🔍 分析内存使用模式...")
        
        # 检查垃圾回收
        if 'gc.collect()' not in self.source_code:
            self.suggestions.append("在适当位置添加gc.collect()进行垃圾回收")
        
        # 检查大对象处理
        large_object_patterns = [
            r'struct\.pack',
            r'struct\.unpack', 
            r'ReadString.*,\s*\d{2,}',  # 读取大量字符串
        ]
        
        for pattern in large_object_patterns:
            matches = re.findall(pattern, self.source_code)
            if matches:
                self.issues.append({
                    "type": "内存模式",
                    "severity": "中",
                    "issue": f"发现{len(matches)}处大对象操作",
                    "description": "大对象操作可能导致内存峰值使用",
                    "line": "数据处理部分"
                })
    
    def generate_report(self):
        """生成分析报告"""
        print("\n" + "="*60)
        print("📋 内存泄漏静态分析报告")
        print("="*60)
        
        if not self.issues:
            print("✅ 未发现明显的内存泄漏风险")
            return
        
        # 按严重程度分组
        high_issues = [i for i in self.issues if i['severity'] == '高']
        medium_issues = [i for i in self.issues if i['severity'] == '中']
        low_issues = [i for i in self.issues if i['severity'] == '低']
        
        print(f"\n🚨 高风险问题 ({len(high_issues)}个):")
        for i, issue in enumerate(high_issues, 1):
            print(f"  {i}. [{issue['type']}] {issue['issue']}")
            print(f"     位置: {issue['line']}")
            print(f"     说明: {issue['description']}")
            print()
        
        print(f"\n⚠️  中风险问题 ({len(medium_issues)}个):")
        for i, issue in enumerate(medium_issues, 1):
            print(f"  {i}. [{issue['type']}] {issue['issue']}")
            print(f"     位置: {issue['line']}")
            print(f"     说明: {issue['description']}")
            print()
        
        if low_issues:
            print(f"\n💡 低风险问题 ({len(low_issues)}个):")
            for i, issue in enumerate(low_issues, 1):
                print(f"  {i}. [{issue['type']}] {issue['issue']}")
                print(f"     说明: {issue['description']}")
                print()
        
        print(f"\n🔧 修复建议:")
        for i, suggestion in enumerate(self.suggestions, 1):
            print(f"  {i}. {suggestion}")
        
        return {
            'high_issues': len(high_issues),
            'medium_issues': len(medium_issues), 
            'low_issues': len(low_issues),
            'total_issues': len(self.issues),
            'suggestions': len(self.suggestions)
        }
    
    def run_full_analysis(self):
        """运行完整分析"""
        if not self.load_source():
            return None
        
        print(f"📁 分析文件: {self.file_path}")
        print(f"📊 源代码行数: {len(self.source_code.splitlines())}")
        
        # 运行各项分析
        self.analyze_connection_management()
        self.analyze_string_operations()
        self.analyze_loop_and_iteration() 
        self.analyze_exception_handling()
        self.analyze_data_structures()
        self.analyze_third_party_integrations()
        self.analyze_memory_patterns()
        
        return self.generate_report()


class TestMelsecA1ENetStaticAnalysis(BaseTestCase):
    """MelsecA1ENet 静态分析测试"""
    
    def setUp(self):
        """测试前准备"""
        super().setUp()
        self.target_file = str(PROJECT_ROOT / "apps" / "connect" / "connect_melseca1enet_backu.py")
        self.analyzer = MemoryLeakStaticAnalyzer(self.target_file)
    
    def test_static_memory_leak_analysis(self):
        """静态内存泄漏分析"""
        print("\n🚀 开始静态内存泄漏分析...")
        
        # 确保目标文件存在
        self.assertTrue(os.path.exists(self.target_file), f"目标文件不存在: {self.target_file}")
        
        # 运行分析
        result = self.analyzer.run_full_analysis()
        
        # 验证分析结果
        self.assertIsNotNone(result, "分析应该返回结果")
        self.assertIsInstance(result, dict, "分析结果应该是字典格式")
        
        # 检查是否发现了预期的问题
        self.assertGreater(result['total_issues'], 0, "应该发现一些潜在问题")
        self.assertGreater(result['suggestions'], 0, "应该提供修复建议")
        
        # 如果发现高风险问题，测试应该给出警告
        if result['high_issues'] > 0:
            print(f"\n⚠️  发现 {result['high_issues']} 个高风险内存泄漏问题，需要立即修复！")
        
        if result['medium_issues'] > 0:
            print(f"\n💡 发现 {result['medium_issues']} 个中风险问题，建议优化")
        
        # 返回分析结果供后续使用
        return result
    
    def test_generate_fix_recommendations(self):
        """生成修复建议"""
        print("\n🔨 生成修复建议...")
        
        # 运行分析
        self.analyzer.run_full_analysis()
        
        # 基于分析结果生成具体的修复代码建议
        fix_recommendations = self.generate_fix_code()
        
        print("\n📝 具体修复代码建议:")
        for i, (title, code) in enumerate(fix_recommendations.items(), 1):
            print(f"\n{i}. {title}:")
            print("-" * 40)
            print(code)
    
    def generate_fix_code(self):
        """生成具体的修复代码"""
        recommendations = {}
        
        # 1. 添加析构函数
        recommendations["添加析构函数确保资源释放"] = '''
def __del__(self):
    """析构函数 - 确保所有连接正确关闭"""
    try:
        # 关闭PLC连接
        if hasattr(self, 'plc') and self.plc:
            self.plc.ConnectClose()
            
        # 关闭InfluxDB连接
        if hasattr(self, 'influxdb_client') and self.influxdb_client:
            self.influxdb_client.close()
            
        # 关闭Kafka连接
        if hasattr(self, 'kafka_producer') and self.kafka_producer:
            self.kafka_producer.close()
            
        print("MelsecA1ENetClient 资源已释放")
    except Exception as e:
        print(f"资源释放时出现异常: {e}")'''
        
        # 2. 优化异常处理
        recommendations["优化异常处理中的连接重建"] = '''
def reconnect_plc(self):
    """安全地重新连接PLC"""
    try:
        # 先关闭旧连接
        if hasattr(self, 'plc') and self.plc:
            self.plc.ConnectClose()
            
        # 创建新连接
        self.plc = MelsecA1ENet(self.ip, self.port)
        result = self.plc.ConnectServer()
        
        if result.IsSuccess:
            Log().printInfo(f"PLC重连成功: {self.ip}:{self.port}")
            return True
        else:
            Log().printError(f"PLC重连失败: {result.Message}")
            return False
            
    except Exception as e:
        Log().printError(f"PLC重连异常: {e}")
        return False'''
        
        # 3. 优化read_plc方法
        recommendations["优化read_plc方法减少内存分配"] = '''
def read_plc(self, register_dict):
    """优化后的PLC读取方法"""
    tag_data = []
    
    try:
        # 预分配字典，减少重复创建
        base_plc_data = {
            'kafka_position': '',
            'cn_name': '',
            'device_a_tag': '',
            'device_name': ''
        }
        
        for en_name, register_conf in register_dict.items():
            if not isinstance(register_conf, dict):
                continue
                
            try:
                # 复用基础字典结构
                plc_data = base_plc_data.copy()
                plc_data.update({
                    'kafka_position': register_conf['kafka_position'],
                    'cn_name': register_conf['cn_name'],
                    'device_a_tag': register_conf['device_a_tag'],
                    'device_name': register_conf['device_name']
                })
                
                # 读取数据逻辑...
                value = self._read_by_type(register_conf)
                plc_data[en_name] = value
                
                tag_data.append(plc_data)
                
            except Exception as e:
                Log().printError(f"读取地址 {register_conf.get('source_addr', 'unknown')} 异常: {e}")
                continue
        
        return tag_data
        
    except Exception as e:
        # 使用安全重连方法
        if self.reconnect_plc():
            Log().printInfo("PLC重连成功，将在下次调用时重试")
        return []
    
    finally:
        # 强制垃圾回收（在必要时）
        if len(tag_data) > 100:  # 只在数据量大时才调用
            import gc
            gc.collect()'''
        
        # 4. 添加内存监控
        recommendations["添加内存监控和清理机制"] = '''
import psutil
import gc

class MemoryMonitor:
    def __init__(self, threshold_mb=100):
        self.threshold_mb = threshold_mb
        self.process = psutil.Process()
        self.read_count = 0
        
    def check_memory(self):
        """检查内存使用情况"""
        memory_mb = self.process.memory_info().rss / 1024 / 1024
        
        if memory_mb > self.threshold_mb:
            Log().printWarning(f"内存使用较高: {memory_mb:.2f}MB")
            gc.collect()  # 强制垃圾回收
            
        return memory_mb
    
    def periodic_cleanup(self):
        """定期清理"""
        self.read_count += 1
        if self.read_count % 100 == 0:  # 每100次读取后清理
            self.check_memory()

# 在MelsecA1ENetClient中添加：
def __init__(self, ...):
    # ... 原有初始化代码 ...
    self.memory_monitor = MemoryMonitor(threshold_mb=150)'''
        
        # 5. 优化字符串处理
        recommendations["优化字符串处理减少临时对象"] = '''
def process_string_data(self, addr, num, en_name):
    """优化的字符串处理方法"""
    try:
        # 使用一次性读取，避免多次访问Content
        read_result = self.plc.ReadString(addr, num)
        if not read_result.IsSuccess:
            return "ReadError"
            
        raw_content = read_result.Content
        
        if en_name == "codeResult":
            # 优化字符串切片和处理
            if len(raw_content) >= 64:
                processed = raw_content[4:64]
                # 使用更高效的字符检查
                if any(c.isalnum() for c in processed):
                    # 使用translate方法替代正则表达式
                    return processed.translate(str.maketrans('', '', ' \\t\\n\\r'))
                else:
                    return "None"
            else:
                return "None"
        else:
            return str(raw_content)
            
    except Exception as e:
        Log().printError(f"字符串处理异常: {e}")
        return "ProcessError"'''
        
        return recommendations


if __name__ == '__main__':
    # 运行静态分析测试
    unittest.main(verbosity=2)