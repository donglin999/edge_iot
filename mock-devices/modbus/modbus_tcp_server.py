#!/usr/bin/env python3
"""
Modbus TCP模拟设备服务器
"""
import socket
import struct
import threading
import time
import json
from typing import Dict, Any, Optional
import sys
import os

# 添加上级目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from common.base_server import BaseDeviceServer
from common.data_generator import create_data_generator


class ModbusTCPServer(BaseDeviceServer):
    """Modbus TCP模拟设备服务器"""
    
    # Modbus功能码
    READ_COILS = 0x01
    READ_DISCRETE_INPUTS = 0x02
    READ_HOLDING_REGISTERS = 0x03
    READ_INPUT_REGISTERS = 0x04
    WRITE_SINGLE_COIL = 0x05
    WRITE_SINGLE_REGISTER = 0x06
    WRITE_MULTIPLE_COILS = 0x0F
    WRITE_MULTIPLE_REGISTERS = 0x10
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化Modbus TCP服务器
        
        Args:
            config: 服务器配置
        """
        super().__init__(config)
        
        # Modbus特定配置
        self.unit_id = config.get('unit_id', 1)
        self.port = config.get('port', 502)
        
        # 数据存储区域
        self.coils = {}  # 线圈 (0x区)
        self.discrete_inputs = {}  # 离散输入 (1x区)
        self.input_registers = {}  # 输入寄存器 (3x区)
        self.holding_registers = {}  # 保持寄存器 (4x区)
        
        # 服务器socket
        self.server_socket = None
        
        # 初始化数据生成器
        self._init_data_generator()
        
        # 初始化数据区域
        self._init_data_areas()
    
    def _init_data_generator(self):
        """初始化数据生成器"""
        gen_config = self.config.get('data_generator', {})
        if gen_config:
            self.data_generator = create_data_generator(gen_config)
    
    def _init_data_areas(self):
        """初始化数据区域"""
        # 初始化线圈
        coil_count = self.config.get('coil_count', 100)
        for i in range(coil_count):
            self.coils[i] = False
        
        # 初始化离散输入
        discrete_count = self.config.get('discrete_input_count', 100)
        for i in range(discrete_count):
            self.discrete_inputs[i] = False
        
        # 初始化输入寄存器
        input_reg_count = self.config.get('input_register_count', 100)
        for i in range(input_reg_count):
            self.input_registers[i] = 0
        
        # 初始化保持寄存器
        holding_reg_count = self.config.get('holding_register_count', 100)
        for i in range(holding_reg_count):
            self.holding_registers[i] = 0
    
    def start_server(self) -> None:
        """启动Modbus TCP服务器"""
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(5)
            
            self.logger.info(f"Modbus TCP服务器启动在 {self.host}:{self.port}")
            
            while self.running:
                try:
                    self.server_socket.settimeout(1.0)  # 设置超时以便检查running状态
                    client_socket, client_address = self.server_socket.accept()
                    
                    client_info = {
                        'socket': client_socket,
                        'address': client_address,
                        'connected_at': time.time()
                    }
                    
                    self.add_client_connection(client_info)
                    
                    # 创建客户端处理线程
                    client_thread = threading.Thread(
                        target=self._handle_client,
                        args=(client_socket, client_address)
                    )
                    client_thread.daemon = True
                    client_thread.start()
                    
                except socket.timeout:
                    continue
                except Exception as e:
                    if self.running:
                        self.logger.error(f"接受客户端连接时出错: {e}")
                    break
                    
        except Exception as e:
            self.logger.error(f"启动服务器时出错: {e}")
    
    def stop_server(self) -> None:
        """停止Modbus TCP服务器"""
        if self.server_socket:
            try:
                self.server_socket.close()
            except Exception as e:
                self.logger.error(f"关闭服务器socket时出错: {e}")
    
    def _handle_client(self, client_socket: socket.socket, client_address):
        """处理客户端连接"""
        try:
            while self.running:
                # 接收请求
                request_data = client_socket.recv(1024)
                if not request_data:
                    break
                
                # 处理请求
                response_data = self.handle_client_request(client_socket, request_data)
                
                # 发送响应
                if response_data:
                    client_socket.send(response_data)
                    
        except Exception as e:
            self.logger.error(f"处理客户端 {client_address} 时出错: {e}")
        finally:
            try:
                client_socket.close()
                client_info = {
                    'socket': client_socket,
                    'address': client_address
                }
                self.remove_client_connection(client_info)
            except Exception as e:
                self.logger.error(f"关闭客户端连接时出错: {e}")
    
    def handle_client_request(self, client_socket, request_data: bytes) -> bytes:
        """处理客户端Modbus请求"""
        try:
            if len(request_data) < 8:  # Modbus TCP最小长度
                return self._create_error_response(0, 0, 0x01)  # 非法功能码
            
            # 解析MBAP头部
            transaction_id, protocol_id, length, unit_id = struct.unpack('>HHHB', request_data[:7])
            
            if protocol_id != 0:  # Modbus协议标识符应该为0
                return self._create_error_response(transaction_id, 0, 0x01)
            
            if unit_id != self.unit_id:  # 检查单元标识符
                return self._create_error_response(transaction_id, 0, 0x01)
            
            # 解析PDU
            function_code = request_data[7]
            pdu_data = request_data[8:]
            
            # 根据功能码处理请求
            if function_code == self.READ_HOLDING_REGISTERS:
                return self._handle_read_holding_registers(transaction_id, pdu_data)
            elif function_code == self.READ_INPUT_REGISTERS:
                return self._handle_read_input_registers(transaction_id, pdu_data)
            elif function_code == self.READ_COILS:
                return self._handle_read_coils(transaction_id, pdu_data)
            elif function_code == self.READ_DISCRETE_INPUTS:
                return self._handle_read_discrete_inputs(transaction_id, pdu_data)
            elif function_code == self.WRITE_SINGLE_REGISTER:
                return self._handle_write_single_register(transaction_id, pdu_data)
            elif function_code == self.WRITE_SINGLE_COIL:
                return self._handle_write_single_coil(transaction_id, pdu_data)
            elif function_code == self.WRITE_MULTIPLE_REGISTERS:
                return self._handle_write_multiple_registers(transaction_id, pdu_data)
            elif function_code == self.WRITE_MULTIPLE_COILS:
                return self._handle_write_multiple_coils(transaction_id, pdu_data)
            else:
                return self._create_error_response(transaction_id, function_code, 0x01)  # 非法功能码
                
        except Exception as e:
            self.logger.error(f"处理Modbus请求时出错: {e}")
            return self._create_error_response(0, 0, 0x04)  # 服务器设备故障
    
    def _handle_read_holding_registers(self, transaction_id: int, data: bytes) -> bytes:
        """处理读取保持寄存器请求"""
        if len(data) < 4:
            return self._create_error_response(transaction_id, self.READ_HOLDING_REGISTERS, 0x03)
        
        start_address, quantity = struct.unpack('>HH', data[:4])
        
        if quantity == 0 or quantity > 125:
            return self._create_error_response(transaction_id, self.READ_HOLDING_REGISTERS, 0x03)
        
        # 读取数据
        register_data = []
        for i in range(quantity):
            address = start_address + i
            value = self.holding_registers.get(address, 0)
            register_data.append(value)
        
        # 构建响应
        byte_count = quantity * 2
        response_data = struct.pack('>BB', self.READ_HOLDING_REGISTERS, byte_count)
        for value in register_data:
            response_data += struct.pack('>H', value)
        
        return self._create_response(transaction_id, response_data)
    
    def _handle_read_input_registers(self, transaction_id: int, data: bytes) -> bytes:
        """处理读取输入寄存器请求"""
        if len(data) < 4:
            return self._create_error_response(transaction_id, self.READ_INPUT_REGISTERS, 0x03)
        
        start_address, quantity = struct.unpack('>HH', data[:4])
        
        if quantity == 0 or quantity > 125:
            return self._create_error_response(transaction_id, self.READ_INPUT_REGISTERS, 0x03)
        
        # 读取数据
        register_data = []
        for i in range(quantity):
            address = start_address + i
            value = self.input_registers.get(address, 0)
            register_data.append(value)
        
        # 构建响应
        byte_count = quantity * 2
        response_data = struct.pack('>BB', self.READ_INPUT_REGISTERS, byte_count)
        for value in register_data:
            response_data += struct.pack('>H', value)
        
        return self._create_response(transaction_id, response_data)
    
    def _handle_read_coils(self, transaction_id: int, data: bytes) -> bytes:
        """处理读取线圈请求"""
        if len(data) < 4:
            return self._create_error_response(transaction_id, self.READ_COILS, 0x03)
        
        start_address, quantity = struct.unpack('>HH', data[:4])
        
        if quantity == 0 or quantity > 2000:
            return self._create_error_response(transaction_id, self.READ_COILS, 0x03)
        
        # 读取线圈数据
        coil_data = []
        for i in range(quantity):
            address = start_address + i
            value = self.coils.get(address, False)
            coil_data.append(value)
        
        # 打包成字节
        byte_count = (quantity + 7) // 8
        packed_bytes = []
        for byte_idx in range(byte_count):
            byte_value = 0
            for bit_idx in range(8):
                coil_idx = byte_idx * 8 + bit_idx
                if coil_idx < len(coil_data) and coil_data[coil_idx]:
                    byte_value |= (1 << bit_idx)
            packed_bytes.append(byte_value)
        
        # 构建响应
        response_data = struct.pack('>BB', self.READ_COILS, byte_count)
        for byte_val in packed_bytes:
            response_data += struct.pack('>B', byte_val)
        
        return self._create_response(transaction_id, response_data)
    
    def _handle_read_discrete_inputs(self, transaction_id: int, data: bytes) -> bytes:
        """处理读取离散输入请求"""
        if len(data) < 4:
            return self._create_error_response(transaction_id, self.READ_DISCRETE_INPUTS, 0x03)
        
        start_address, quantity = struct.unpack('>HH', data[:4])
        
        if quantity == 0 or quantity > 2000:
            return self._create_error_response(transaction_id, self.READ_DISCRETE_INPUTS, 0x03)
        
        # 读取离散输入数据
        input_data = []
        for i in range(quantity):
            address = start_address + i
            value = self.discrete_inputs.get(address, False)
            input_data.append(value)
        
        # 打包成字节
        byte_count = (quantity + 7) // 8
        packed_bytes = []
        for byte_idx in range(byte_count):
            byte_value = 0
            for bit_idx in range(8):
                input_idx = byte_idx * 8 + bit_idx
                if input_idx < len(input_data) and input_data[input_idx]:
                    byte_value |= (1 << bit_idx)
            packed_bytes.append(byte_value)
        
        # 构建响应
        response_data = struct.pack('>BB', self.READ_DISCRETE_INPUTS, byte_count)
        for byte_val in packed_bytes:
            response_data += struct.pack('>B', byte_val)
        
        return self._create_response(transaction_id, response_data)
    
    def _handle_write_single_register(self, transaction_id: int, data: bytes) -> bytes:
        """处理写单个寄存器请求"""
        if len(data) < 4:
            return self._create_error_response(transaction_id, self.WRITE_SINGLE_REGISTER, 0x03)
        
        address, value = struct.unpack('>HH', data[:4])
        
        # 写入数据
        self.holding_registers[address] = value
        
        # 构建响应（回显请求）
        response_data = struct.pack('>BHH', self.WRITE_SINGLE_REGISTER, address, value)
        return self._create_response(transaction_id, response_data)
    
    def _handle_write_single_coil(self, transaction_id: int, data: bytes) -> bytes:
        """处理写单个线圈请求"""
        if len(data) < 4:
            return self._create_error_response(transaction_id, self.WRITE_SINGLE_COIL, 0x03)
        
        address, value = struct.unpack('>HH', data[:4])
        
        # 写入数据
        self.coils[address] = (value == 0xFF00)
        
        # 构建响应（回显请求）
        response_data = struct.pack('>BHH', self.WRITE_SINGLE_COIL, address, value)
        return self._create_response(transaction_id, response_data)
    
    def _handle_write_multiple_registers(self, transaction_id: int, data: bytes) -> bytes:
        """处理写多个寄存器请求"""
        if len(data) < 5:
            return self._create_error_response(transaction_id, self.WRITE_MULTIPLE_REGISTERS, 0x03)
        
        start_address, quantity, byte_count = struct.unpack('>HHB', data[:5])
        
        if quantity == 0 or quantity > 123 or byte_count != quantity * 2:
            return self._create_error_response(transaction_id, self.WRITE_MULTIPLE_REGISTERS, 0x03)
        
        # 写入数据
        for i in range(quantity):
            address = start_address + i
            value = struct.unpack('>H', data[5 + i * 2:7 + i * 2])[0]
            self.holding_registers[address] = value
        
        # 构建响应
        response_data = struct.pack('>BHH', self.WRITE_MULTIPLE_REGISTERS, start_address, quantity)
        return self._create_response(transaction_id, response_data)
    
    def _handle_write_multiple_coils(self, transaction_id: int, data: bytes) -> bytes:
        """处理写多个线圈请求"""
        if len(data) < 5:
            return self._create_error_response(transaction_id, self.WRITE_MULTIPLE_COILS, 0x03)
        
        start_address, quantity, byte_count = struct.unpack('>HHB', data[:5])
        
        if quantity == 0 or quantity > 1968 or byte_count != (quantity + 7) // 8:
            return self._create_error_response(transaction_id, self.WRITE_MULTIPLE_COILS, 0x03)
        
        # 写入数据
        for i in range(quantity):
            address = start_address + i
            byte_idx = i // 8
            bit_idx = i % 8
            byte_value = data[5 + byte_idx]
            coil_value = bool(byte_value & (1 << bit_idx))
            self.coils[address] = coil_value
        
        # 构建响应
        response_data = struct.pack('>BHH', self.WRITE_MULTIPLE_COILS, start_address, quantity)
        return self._create_response(transaction_id, response_data)
    
    def _create_response(self, transaction_id: int, pdu_data: bytes) -> bytes:
        """创建Modbus TCP响应"""
        length = len(pdu_data) + 1  # PDU长度 + 单元标识符
        mbap_header = struct.pack('>HHHB', transaction_id, 0, length, self.unit_id)
        return mbap_header + pdu_data
    
    def _create_error_response(self, transaction_id: int, function_code: int, error_code: int) -> bytes:
        """创建Modbus TCP错误响应"""
        error_function_code = function_code | 0x80
        pdu_data = struct.pack('>BB', error_function_code, error_code)
        return self._create_response(transaction_id, pdu_data)
    
    def update_data(self) -> None:
        """更新设备数据"""
        super().update_data()
        
        # 使用生成的数据更新寄存器
        if hasattr(self, 'data_store') and self.data_store:
            for address, value in self.data_store.items():
                if isinstance(value, bool):
                    # 布尔值写入线圈和离散输入
                    if address < 10000:
                        self.coils[address] = value
                    else:
                        self.discrete_inputs[address - 10000] = value
                elif isinstance(value, (int, float)):
                    # 数值写入寄存器
                    int_value = int(value) & 0xFFFF  # 限制为16位
                    if address < 30000:
                        self.input_registers[address] = int_value
                    else:
                        self.holding_registers[address - 40000] = int_value


def main():
    """主函数 - 用于直接运行服务器"""
    config = {
        'device_id': 'modbus_tcp_001',
        'host': '0.0.0.0',
        'port': 502,
        'unit_id': 1,
        'update_interval': 1.0,
        'coil_count': 100,
        'discrete_input_count': 100,
        'input_register_count': 100,
        'holding_register_count': 100,
        'data_generator': {
            'type': 'composite',
            'generators': [
                {
                    'type': 'sine',
                    'amplitude': 1000,
                    'frequency': 0.1,
                    'offset': 2000,
                    'addresses': [0, 1, 2]
                },
                {
                    'type': 'random',
                    'min_value': 0,
                    'max_value': 4095,
                    'data_type': 'int',
                    'addresses': [10, 11, 12]
                },
                {
                    'type': 'step',
                    'values': [True, False],
                    'step_interval': 5.0,
                    'addresses': [20]
                }
            ]
        }
    }
    
    server = ModbusTCPServer(config)
    
    try:
        print("启动Modbus TCP模拟设备服务器...")
        server.start()
        
        # 保持服务器运行
        while True:
            time.sleep(1)
            status = server.get_status()
            print(f"状态: 运行={status['running']}, 连接数={status['connection_count']}, 数据点={status['data_points']}")
            
    except KeyboardInterrupt:
        print("\n正在停止服务器...")
        server.stop()
        print("服务器已停止")


if __name__ == '__main__':
    main() 