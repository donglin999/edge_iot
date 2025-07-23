#!/usr/bin/env python3
"""
三菱PLC模拟设备服务器
支持A1E协议通信
"""
import socket
import struct
import threading
import time
import json
from typing import Dict, Any, Optional, List
import sys
import os

# 添加上级目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from common.base_server import BaseDeviceServer
from common.data_generator import create_data_generator


class MitsubishiPLCServer(BaseDeviceServer):
    """三菱PLC模拟设备服务器"""
    
    # A1E协议命令
    READ_COMMAND = 0x0401
    WRITE_COMMAND = 0x1401
    
    # 设备类型
    DEVICE_TYPES = {
        'D': 0x4420,   # D寄存器
        'M': 0x4D20,   # M寄存器（中间继电器）
        'X': 0x5820,   # X输入点
        'Y': 0x5920,   # Y输出点
        'B': 0x4220,   # B寄存器（链接继电器）
        'F': 0x4620,   # F寄存器（文件寄存器）
        'T': 0x5420,   # T定时器
        'C': 0x4320,   # C计数器
    }
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化三菱PLC服务器
        
        Args:
            config: 服务器配置
        """
        super().__init__(config)
        
        # PLC特定配置
        self.port = config.get('port', 5001)
        self.plc_type = config.get('plc_type', 'FX3U')
        self.station_number = config.get('station_number', 0xFF)
        
        # 数据存储区域
        self.d_registers = {}   # D寄存器
        self.m_relays = {}     # M中间继电器
        self.x_inputs = {}     # X输入点
        self.y_outputs = {}    # Y输出点
        self.b_registers = {}  # B链接继电器
        self.t_timers = {}     # T定时器
        self.c_counters = {}   # C计数器
        
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
        # 初始化D寄存器
        d_count = self.config.get('d_register_count', 1000)
        for i in range(d_count):
            self.d_registers[i] = 0
        
        # 初始化M继电器
        m_count = self.config.get('m_relay_count', 1000)
        for i in range(m_count):
            self.m_relays[i] = False
        
        # 初始化X输入点
        x_count = self.config.get('x_input_count', 64)
        for i in range(x_count):
            self.x_inputs[i] = False
        
        # 初始化Y输出点
        y_count = self.config.get('y_output_count', 64)
        for i in range(y_count):
            self.y_outputs[i] = False
        
        # 初始化其他区域
        for i in range(100):
            self.b_registers[i] = False
            self.t_timers[i] = 0
            self.c_counters[i] = 0
    
    def start_server(self) -> None:
        """启动三菱PLC服务器"""
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(5)
            
            self.logger.info(f"三菱PLC服务器启动在 {self.host}:{self.port}")
            
            while self.running:
                try:
                    self.server_socket.settimeout(1.0)
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
            self.logger.error(f"启动PLC服务器时出错: {e}")
    
    def stop_server(self) -> None:
        """停止三菱PLC服务器"""
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
        """处理客户端A1E协议请求"""
        try:
            if len(request_data) < 12:  # A1E最小请求长度
                return self._create_error_response(0x55)
            
            # 解析A1E协议头
            header = struct.unpack('<HHHH', request_data[:8])
            frame_type = header[0]
            monitoring_timer = header[1]
            command = header[2]
            subcommand = header[3]
            
            # 解析请求数据部分
            request_length = struct.unpack('<H', request_data[8:10])[0]
            cpu_monitoring_timer = struct.unpack('<H', request_data[10:12])[0]
            
            if command == self.READ_COMMAND:
                return self._handle_read_request(request_data[12:])
            elif command == self.WRITE_COMMAND:
                return self._handle_write_request(request_data[12:])
            else:
                return self._create_error_response(0xC055)  # 不支持的命令
                
        except Exception as e:
            self.logger.error(f"处理PLC请求时出错: {e}")
            return self._create_error_response(0xC055)
    
    def _handle_read_request(self, data: bytes) -> bytes:
        """处理读取请求"""
        try:
            if len(data) < 6:
                return self._create_error_response(0xC056)
            
            # 解析读取参数
            device_code = struct.unpack('<H', data[0:2])[0]
            start_address = struct.unpack('<L', data[2:6])[0] & 0xFFFFFF  # 24位地址
            read_count = struct.unpack('<H', data[6:8])[0]
            
            # 根据设备代码读取数据
            device_type = self._get_device_type_from_code(device_code)
            if not device_type:
                return self._create_error_response(0xC058)  # 不支持的设备
            
            data_values = self._read_device_data(device_type, start_address, read_count)
            
            # 构建响应
            response_data = b''
            for value in data_values:
                if device_type in ['M', 'X', 'Y', 'B']:
                    # 位设备返回字节
                    response_data += struct.pack('<B', 1 if value else 0)
                else:
                    # 字设备返回16位数据
                    response_data += struct.pack('<H', value)
            
            return self._create_success_response(response_data)
            
        except Exception as e:
            self.logger.error(f"处理读取请求时出错: {e}")
            return self._create_error_response(0xC056)
    
    def _handle_write_request(self, data: bytes) -> bytes:
        """处理写入请求"""
        try:
            if len(data) < 8:
                return self._create_error_response(0xC056)
            
            # 解析写入参数
            device_code = struct.unpack('<H', data[0:2])[0]
            start_address = struct.unpack('<L', data[2:6])[0] & 0xFFFFFF
            write_count = struct.unpack('<H', data[6:8])[0]
            
            # 解析写入数据
            write_data = data[8:]
            device_type = self._get_device_type_from_code(device_code)
            if not device_type:
                return self._create_error_response(0xC058)
            
            # 写入数据
            values = []
            if device_type in ['M', 'X', 'Y', 'B']:
                # 位设备
                for i in range(write_count):
                    if i < len(write_data):
                        values.append(write_data[i] != 0)
                    else:
                        values.append(False)
            else:
                # 字设备
                for i in range(write_count):
                    if i * 2 + 1 < len(write_data):
                        value = struct.unpack('<H', write_data[i*2:i*2+2])[0]
                        values.append(value)
                    else:
                        values.append(0)
            
            self._write_device_data(device_type, start_address, values)
            
            return self._create_success_response(b'')
            
        except Exception as e:
            self.logger.error(f"处理写入请求时出错: {e}")
            return self._create_error_response(0xC056)
    
    def _get_device_type_from_code(self, code: int) -> Optional[str]:
        """根据设备代码获取设备类型"""
        for device_type, device_code in self.DEVICE_TYPES.items():
            if code == device_code:
                return device_type
        return None
    
    def _read_device_data(self, device_type: str, start_address: int, count: int) -> List[Any]:
        """读取设备数据"""
        values = []
        
        if device_type == 'D':
            for i in range(count):
                address = start_address + i
                values.append(self.d_registers.get(address, 0))
        elif device_type == 'M':
            for i in range(count):
                address = start_address + i
                values.append(self.m_relays.get(address, False))
        elif device_type == 'X':
            for i in range(count):
                address = start_address + i
                values.append(self.x_inputs.get(address, False))
        elif device_type == 'Y':
            for i in range(count):
                address = start_address + i
                values.append(self.y_outputs.get(address, False))
        elif device_type == 'B':
            for i in range(count):
                address = start_address + i
                values.append(self.b_registers.get(address, False))
        elif device_type == 'T':
            for i in range(count):
                address = start_address + i
                values.append(self.t_timers.get(address, 0))
        elif device_type == 'C':
            for i in range(count):
                address = start_address + i
                values.append(self.c_counters.get(address, 0))
        else:
            # 未知设备类型，返回0
            values = [0] * count
        
        return values
    
    def _write_device_data(self, device_type: str, start_address: int, values: List[Any]) -> None:
        """写入设备数据"""
        if device_type == 'D':
            for i, value in enumerate(values):
                address = start_address + i
                self.d_registers[address] = int(value) & 0xFFFF
        elif device_type == 'M':
            for i, value in enumerate(values):
                address = start_address + i
                self.m_relays[address] = bool(value)
        elif device_type == 'X':
            for i, value in enumerate(values):
                address = start_address + i
                self.x_inputs[address] = bool(value)
        elif device_type == 'Y':
            for i, value in enumerate(values):
                address = start_address + i
                self.y_outputs[address] = bool(value)
        elif device_type == 'B':
            for i, value in enumerate(values):
                address = start_address + i
                self.b_registers[address] = bool(value)
        elif device_type == 'T':
            for i, value in enumerate(values):
                address = start_address + i
                self.t_timers[address] = int(value) & 0xFFFF
        elif device_type == 'C':
            for i, value in enumerate(values):
                address = start_address + i
                self.c_counters[address] = int(value) & 0xFFFF
    
    def _create_success_response(self, response_data: bytes) -> bytes:
        """创建成功响应"""
        # A1E协议响应头
        header = struct.pack('<HHHH', 0xD000, 0x00, 0x00, 0x00)
        
        # 响应长度
        data_length = len(response_data) + 2  # +2 for error code
        length_field = struct.pack('<H', data_length)
        
        # 错误代码（0表示成功）
        error_code = struct.pack('<H', 0x00)
        
        return header + length_field + error_code + response_data
    
    def _create_error_response(self, error_code: int) -> bytes:
        """创建错误响应"""
        # A1E协议错误响应头
        header = struct.pack('<HHHH', 0xD000, 0x00, 0x00, 0x00)
        
        # 响应长度（只有错误代码）
        length_field = struct.pack('<H', 2)
        
        # 错误代码
        error_field = struct.pack('<H', error_code)
        
        return header + length_field + error_field
    
    def update_data(self) -> None:
        """更新设备数据"""
        super().update_data()
        
        # 使用生成的数据更新PLC寄存器
        if hasattr(self, 'data_store') and self.data_store:
            for address, value in self.data_store.items():
                if isinstance(value, bool):
                    # 布尔值写入M继电器或X输入
                    if address < 1000:
                        self.m_relays[address] = value
                    else:
                        self.x_inputs[address - 1000] = value
                elif isinstance(value, (int, float)):
                    # 数值写入D寄存器
                    int_value = int(value) & 0xFFFF
                    self.d_registers[address] = int_value
    
    def get_device_status(self) -> Dict[str, Any]:
        """获取设备状态"""
        status = super().get_status()
        status.update({
            'plc_type': self.plc_type,
            'station_number': self.station_number,
            'd_registers_count': len(self.d_registers),
            'm_relays_count': len(self.m_relays),
            'x_inputs_count': len(self.x_inputs),
            'y_outputs_count': len(self.y_outputs)
        })
        return status
    
    def get_register_values(self, device_type: str, start: int, count: int) -> Dict[str, Any]:
        """获取指定寄存器的值"""
        values = {}
        
        if device_type.upper() == 'D':
            for i in range(count):
                address = start + i
                values[f'D{address}'] = self.d_registers.get(address, 0)
        elif device_type.upper() == 'M':
            for i in range(count):
                address = start + i
                values[f'M{address}'] = self.m_relays.get(address, False)
        elif device_type.upper() == 'X':
            for i in range(count):
                address = start + i
                values[f'X{address:02X}'] = self.x_inputs.get(address, False)
        elif device_type.upper() == 'Y':
            for i in range(count):
                address = start + i
                values[f'Y{address:02X}'] = self.y_outputs.get(address, False)
        
        return values


def main():
    """主函数 - 用于直接运行服务器"""
    config = {
        'device_id': 'mitsubishi_plc_001',
        'host': '0.0.0.0',
        'port': 5001,
        'plc_type': 'FX3U',
        'station_number': 0xFF,
        'update_interval': 1.0,
        'd_register_count': 1000,
        'm_relay_count': 1000,
        'x_input_count': 64,
        'y_output_count': 64,
        'data_generator': {
            'type': 'composite',
            'generators': [
                {
                    'type': 'sine',
                    'amplitude': 2000,
                    'frequency': 0.1,
                    'offset': 2000,
                    'addresses': [0, 1, 2, 3, 4]  # D0-D4
                },
                {
                    'type': 'random',
                    'min_value': 0,
                    'max_value': 65535,
                    'data_type': 'int',
                    'addresses': [10, 11, 12, 13, 14, 15]  # D10-D15
                },
                {
                    'type': 'step',
                    'values': [True, False, True, True, False],
                    'step_interval': 3.0,
                    'addresses': [1000, 1001, 1002]  # M0-M2 (1000+ mapping)
                },
                {
                    'type': 'linear',
                    'start_value': 0,
                    'end_value': 32767,
                    'duration': 60.0,
                    'repeat': True,
                    'addresses': [20, 21]  # D20-D21
                }
            ]
        }
    }
    
    server = MitsubishiPLCServer(config)
    
    try:
        print("启动三菱PLC模拟设备服务器...")
        server.start()
        
        # 保持服务器运行
        while True:
            time.sleep(5)
            status = server.get_device_status()
            d_values = server.get_register_values('D', 0, 10)
            m_values = server.get_register_values('M', 0, 5)
            
            print(f"状态: 运行={status['running']}, 连接数={status['connection_count']}")
            print(f"D寄存器: {d_values}")
            print(f"M继电器: {m_values}")
            
    except KeyboardInterrupt:
        print("\n正在停止服务器...")
        server.stop()
        print("服务器已停止")


if __name__ == '__main__':
    main() 