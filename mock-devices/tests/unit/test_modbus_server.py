#!/usr/bin/env python3
"""
Modbus TCP服务器测试模块
"""
import pytest
import socket
import struct
import threading
import time
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from modbus.modbus_tcp_server import ModbusTCPServer


class TestModbusTCPServer:
    """Modbus TCP服务器测试类"""
    
    def setup_method(self):
        """每个测试方法前的准备工作"""
        self.config = {
            'device_id': 'test_modbus_001',
            'host': '127.0.0.1',
            'port': 50502,  # 使用不同端口避免冲突
            'unit_id': 1,
            'update_interval': 0.1,  # 快速更新用于测试
            'coil_count': 100,
            'discrete_input_count': 100,
            'input_register_count': 100,
            'holding_register_count': 100
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
        self.server = ModbusTCPServer(self.config)
        self.server_thread = threading.Thread(target=self.server.start)
        self.server_thread.daemon = True
        self.server_thread.start()
        
        # 等待服务器启动
        time.sleep(0.5)
    
    @pytest.mark.unit
    def test_server_initialization(self):
        """测试服务器初始化"""
        server = ModbusTCPServer(self.config)
        
        assert server.device_id == 'test_modbus_001'
        assert server.host == '127.0.0.1'
        assert server.port == 50502
        assert server.unit_id == 1
        assert len(server.holding_registers) == 100
        assert len(server.coils) == 100
    
    @pytest.mark.unit
    def test_data_area_initialization(self):
        """测试数据区域初始化"""
        server = ModbusTCPServer(self.config)
        
        # 检查保持寄存器初始化
        assert all(value == 0 for value in server.holding_registers.values())
        
        # 检查线圈初始化
        assert all(value is False for value in server.coils.values())
        
        # 检查输入寄存器初始化
        assert all(value == 0 for value in server.input_registers.values())
        
        # 检查离散输入初始化
        assert all(value is False for value in server.discrete_inputs.values())
    
    @pytest.mark.unit
    def test_server_start_stop(self):
        """测试服务器启动和停止"""
        self.start_test_server()
        
        # 检查服务器是否运行
        assert self.server.running
        
        # 测试连接
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(2)
            result = sock.connect_ex((self.config['host'], self.config['port']))
            assert result == 0  # 连接成功
    
    @pytest.mark.unit
    def test_modbus_read_holding_registers(self):
        """测试读取保持寄存器"""
        self.start_test_server()
        
        # 设置测试数据
        self.server.holding_registers[0] = 1234
        self.server.holding_registers[1] = 5678
        
        # 构建Modbus读取请求
        transaction_id = 1
        protocol_id = 0
        length = 6
        unit_id = 1
        function_code = 0x03  # 读取保持寄存器
        start_address = 0
        quantity = 2
        
        request = struct.pack('>HHHBBHH', 
                             transaction_id, protocol_id, length, unit_id,
                             function_code, start_address, quantity)
        
        # 发送请求
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(2)
            sock.connect((self.config['host'], self.config['port']))
            sock.send(request)
            response = sock.recv(1024)
        
        # 解析响应
        assert len(response) >= 9  # 最小响应长度
        
        # 验证MBAP头部
        resp_transaction_id, resp_protocol_id, resp_length, resp_unit_id = struct.unpack('>HHHB', response[:7])
        assert resp_transaction_id == transaction_id
        assert resp_protocol_id == 0
        assert resp_unit_id == unit_id
        
        # 验证PDU
        resp_function_code = response[7]
        byte_count = response[8]
        assert resp_function_code == function_code
        assert byte_count == 4  # 2个寄存器 * 2字节
        
        # 验证数据
        value1, value2 = struct.unpack('>HH', response[9:13])
        assert value1 == 1234
        assert value2 == 5678
    
    @pytest.mark.unit
    def test_modbus_write_single_register(self):
        """测试写单个寄存器"""
        self.start_test_server()
        
        # 构建Modbus写请求
        transaction_id = 2
        protocol_id = 0
        length = 6
        unit_id = 1
        function_code = 0x06  # 写单个寄存器
        address = 10
        value = 9999
        
        request = struct.pack('>HHHBBHH',
                             transaction_id, protocol_id, length, unit_id,
                             function_code, address, value)
        
        # 发送请求
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(2)
            sock.connect((self.config['host'], self.config['port']))
            sock.send(request)
            response = sock.recv(1024)
        
        # 验证响应（写操作响应应该回显请求）
        assert len(response) == len(request)
        assert response == request
        
        # 验证数据已写入
        assert self.server.holding_registers[address] == value
    
    @pytest.mark.unit
    def test_modbus_read_coils(self):
        """测试读取线圈"""
        self.start_test_server()
        
        # 设置测试数据
        self.server.coils[0] = True
        self.server.coils[1] = False
        self.server.coils[2] = True
        
        # 构建Modbus读取线圈请求
        transaction_id = 3
        protocol_id = 0
        length = 6
        unit_id = 1
        function_code = 0x01  # 读取线圈
        start_address = 0
        quantity = 3
        
        request = struct.pack('>HHHBBHH',
                             transaction_id, protocol_id, length, unit_id,
                             function_code, start_address, quantity)
        
        # 发送请求
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(2)
            sock.connect((self.config['host'], self.config['port']))
            sock.send(request)
            response = sock.recv(1024)
        
        # 验证响应
        assert len(response) >= 9
        resp_function_code = response[7]
        byte_count = response[8]
        assert resp_function_code == function_code
        assert byte_count == 1  # 3个线圈需要1个字节
        
        # 验证线圈数据（位0=True, 位1=False, 位2=True）
        coil_byte = response[9]
        assert (coil_byte & 0x01) != 0  # 位0为True
        assert (coil_byte & 0x02) == 0  # 位1为False  
        assert (coil_byte & 0x04) != 0  # 位2为True
    
    @pytest.mark.unit
    def test_invalid_function_code(self):
        """测试无效功能码"""
        self.start_test_server()
        
        # 构建无效功能码请求
        transaction_id = 4
        protocol_id = 0
        length = 6
        unit_id = 1
        invalid_function_code = 0xFF  # 无效功能码
        start_address = 0
        quantity = 1
        
        request = struct.pack('>HHHBBHH',
                             transaction_id, protocol_id, length, unit_id,
                             invalid_function_code, start_address, quantity)
        
        # 发送请求
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(2)
            sock.connect((self.config['host'], self.config['port']))
            sock.send(request)
            response = sock.recv(1024)
        
        # 验证错误响应
        assert len(response) >= 9
        error_function_code = response[7]
        error_code = response[8]
        
        # 错误功能码应该是原功能码 | 0x80
        assert error_function_code == (invalid_function_code | 0x80)
        assert error_code == 0x01  # 非法功能码错误
    
    @pytest.mark.unit
    def test_server_status(self):
        """测试服务器状态获取"""
        self.start_test_server()
        
        status = self.server.get_status()
        
        assert status['running'] is True
        assert status['device_id'] == 'test_modbus_001'
        assert 'start_time' in status
        assert 'connection_count' in status
        assert 'data_points' in status
    
    @pytest.mark.unit
    def test_data_generator_integration(self):
        """测试数据生成器集成"""
        # 添加数据生成器配置
        config_with_generator = self.config.copy()
        config_with_generator['data_generator'] = {
            'type': 'sine',
            'amplitude': 100,
            'frequency': 1.0,
            'offset': 500,
            'addresses': [0, 1]
        }
        
        server = ModbusTCPServer(config_with_generator)
        
        # 检查数据生成器是否创建
        assert hasattr(server, 'data_generator')
        assert server.data_generator is not None
        
        # 模拟数据更新
        server.update_data()
        
        # 验证寄存器值已更新（不为初始值0）
        assert server.holding_registers[0] != 0 or server.holding_registers[1] != 0


if __name__ == '__main__':
    pytest.main([__file__, '-v']) 