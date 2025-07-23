#!/usr/bin/env python3
"""
OPC UA服务器测试模块
"""
import pytest
import threading
import time
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from opcua.opcua_server import OPCUAServer


class TestOPCUAServer:
    """OPC UA服务器测试类"""
    
    def setup_method(self):
        """每个测试方法前的准备工作"""
        self.config = {
            'device_id': 'test_opcua_001',
            'host': '127.0.0.1',
            'port': 48400,  # 使用不同端口避免冲突
            'update_interval': 0.1,
            'server_name': 'Test OPC UA Server',
            'namespace': 'http://test.mock.device/opcua001',
            'nodes': [
                {'name': 'Temperature', 'data_type': 'Double', 'initial_value': 25.0},
                {'name': 'Pressure', 'data_type': 'Double', 'initial_value': 1013.25},
                {'name': 'Status', 'data_type': 'Boolean', 'initial_value': True},
                {'name': 'Counter', 'data_type': 'Int32', 'initial_value': 0}
            ]
        }
        self.server = None
        self.server_thread = None
    
    def teardown_method(self):
        """每个测试方法后的清理工作"""
        if self.server:
            self.server.stop()
            if self.server_thread and self.server_thread.is_alive():
                self.server_thread.join(timeout=2)
    
    def start_test_server(self):
        """启动测试服务器"""
        self.server = OPCUAServer(self.config)
        self.server_thread = threading.Thread(target=self.server.start)
        self.server_thread.daemon = True
        self.server_thread.start()
        
        # 等待服务器启动
        time.sleep(1)
    
    @pytest.mark.unit
    def test_server_initialization(self):
        """测试服务器初始化"""
        server = OPCUAServer(self.config)
        
        assert server.device_id == 'test_opcua_001'
        assert server.host == '127.0.0.1'
        assert server.port == 48400
        assert server.endpoint == 'opc.tcp://127.0.0.1:48400/freeopcua/server/'
    
    @pytest.mark.unit
    def test_mock_nodes_creation(self):
        """测试模拟节点创建（无asyncua库模式）"""
        server = OPCUAServer(self.config)
        
        # 创建模拟节点
        server._create_mock_nodes()
        
        # 验证节点是否创建
        assert len(server.nodes) == 4
        assert 'Temperature' in server.nodes
        assert 'Pressure' in server.nodes
        assert 'Status' in server.nodes
        assert 'Counter' in server.nodes
        
        # 验证初始值
        assert server.nodes['Temperature']['current_value'] == 25.0
        assert server.nodes['Pressure']['current_value'] == 1013.25
        assert server.nodes['Status']['current_value'] is True
        assert server.nodes['Counter']['current_value'] == 0
    
    @pytest.mark.unit
    def test_node_value_update(self):
        """测试节点值更新"""
        server = OPCUAServer(self.config)
        server._create_mock_nodes()
        
        # 测试设置节点值
        result = server.set_node_value('Temperature', 30.5)
        assert result is True
        assert server.nodes['Temperature']['current_value'] == 30.5
        
        # 测试设置不存在的节点
        result = server.set_node_value('NonExistent', 100)
        assert result is False
    
    @pytest.mark.unit
    def test_get_node_values(self):
        """测试获取所有节点值"""
        server = OPCUAServer(self.config)
        server._create_mock_nodes()
        
        # 修改一些值
        server.set_node_value('Temperature', 35.0)
        server.set_node_value('Status', False)
        
        # 获取所有节点值
        values = server.get_node_values()
        
        assert values['Temperature'] == 35.0
        assert values['Pressure'] == 1013.25
        assert values['Status'] is False
        assert values['Counter'] == 0
    
    @pytest.mark.unit
    def test_address_to_node_mapping(self):
        """测试地址到节点名称的映射"""
        server = OPCUAServer(self.config)
        server._create_mock_nodes()
        
        # 测试地址映射
        assert server._address_to_node_name(0) == 'Temperature'
        assert server._address_to_node_name(1) == 'Pressure'
        assert server._address_to_node_name(2) == 'Status'
        assert server._address_to_node_name(3) == 'Counter'
        
        # 测试无效地址
        assert server._address_to_node_name(999) is None
    
    @pytest.mark.unit
    def test_mock_nodes_update(self):
        """测试模拟节点数据更新"""
        server = OPCUAServer(self.config)
        server._create_mock_nodes()
        
        # 记录初始值
        initial_temp = server.nodes['Temperature']['current_value']
        initial_counter = server.nodes['Counter']['current_value']
        
        # 执行数据更新
        server._update_mock_nodes()
        
        # 验证某些值可能已经改变（由于随机性，不是所有值都会改变）
        # 这里主要验证更新函数能正常运行
        assert 'Temperature' in server.nodes
        assert 'Counter' in server.nodes
        
        # 计数器应该递增
        assert server.nodes['Counter']['current_value'] == (initial_counter + 1) % 10000
    
    @pytest.mark.unit
    def test_server_start_stop_mock_mode(self):
        """测试服务器启动停止（模拟模式）"""
        self.start_test_server()
        
        # 检查服务器是否运行
        assert self.server.running
        
        # 检查节点是否创建
        assert len(self.server.nodes) > 0
    
    @pytest.mark.unit
    def test_data_generator_integration(self):
        """测试数据生成器集成"""
        # 添加数据生成器配置
        config_with_generator = self.config.copy()
        config_with_generator['data_generator'] = {
            'type': 'sine',
            'amplitude': 10.0,
            'frequency': 0.5,
            'offset': 25.0,
            'addresses': [0]  # Temperature节点
        }
        
        server = OPCUAServer(config_with_generator)
        server._create_mock_nodes()
        
        # 检查数据生成器是否创建
        assert hasattr(server, 'data_generator')
        assert server.data_generator is not None
        
        # 记录初始温度值
        initial_temp = server.nodes['Temperature']['current_value']
        
        # 模拟数据存储更新
        server.data_store = {0: 30.5}  # 模拟生成的数据
        server._update_mock_nodes_with_generated_data()
        
        # 验证温度值已更新
        assert server.nodes['Temperature']['current_value'] == 30.5
    
    @pytest.mark.unit
    def test_server_status(self):
        """测试服务器状态获取"""
        self.start_test_server()
        
        status = self.server.get_status()
        
        assert status['running'] is True
        assert status['device_id'] == 'test_opcua_001'
        assert 'start_time' in status
        assert 'connection_count' in status
        assert 'data_points' in status
    
    @pytest.mark.unit
    def test_node_data_types(self):
        """测试不同数据类型的节点"""
        config_with_types = {
            'device_id': 'test_types',
            'host': '127.0.0.1',
            'port': 48401,
            'nodes': [
                {'name': 'DoubleNode', 'data_type': 'Double', 'initial_value': 123.45},
                {'name': 'BoolNode', 'data_type': 'Boolean', 'initial_value': True},
                {'name': 'IntNode', 'data_type': 'Int32', 'initial_value': 42},
                {'name': 'FloatNode', 'data_type': 'Float', 'initial_value': 3.14}
            ]
        }
        
        server = OPCUAServer(config_with_types)
        server._create_mock_nodes()
        
        # 验证各种数据类型
        assert server.nodes['DoubleNode']['current_value'] == 123.45
        assert server.nodes['BoolNode']['current_value'] is True
        assert server.nodes['IntNode']['current_value'] == 42
        assert server.nodes['FloatNode']['current_value'] == 3.14
        
        # 验证配置信息
        assert server.nodes['DoubleNode']['config']['data_type'] == 'Double'
        assert server.nodes['BoolNode']['config']['data_type'] == 'Boolean'
        assert server.nodes['IntNode']['config']['data_type'] == 'Int32'
        assert server.nodes['FloatNode']['config']['data_type'] == 'Float'
    
    @pytest.mark.unit
    def test_default_nodes_creation(self):
        """测试默认节点创建（无节点配置时）"""
        config_no_nodes = {
            'device_id': 'test_default',
            'host': '127.0.0.1',
            'port': 48402
        }
        
        server = OPCUAServer(config_no_nodes)
        server._create_mock_nodes()
        
        # 应该创建默认节点
        assert len(server.nodes) == 5  # 默认创建5个节点
        assert 'Temperature' in server.nodes
        assert 'Pressure' in server.nodes
        assert 'Humidity' in server.nodes
        assert 'Status' in server.nodes
        assert 'Counter' in server.nodes


if __name__ == '__main__':
    pytest.main([__file__, '-v']) 