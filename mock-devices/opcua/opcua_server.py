#!/usr/bin/env python3
"""
OPC UA模拟设备服务器
"""
import time
import json
import asyncio
import threading
from typing import Dict, Any, Optional, List
import sys
import os

# 添加上级目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from common.base_server import BaseDeviceServer
from common.data_generator import create_data_generator

try:
    from asyncua import Server
    from asyncua import ua
    from asyncua.common.node import Node
    OPCUA_AVAILABLE = True
except ImportError:
    print("警告: 未安装asyncua库，OPC UA服务器功能将被模拟")
    OPCUA_AVAILABLE = False
    # 创建Mock Node类型
    class Node:
        pass


class OPCUAServer(BaseDeviceServer):
    """OPC UA模拟设备服务器"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化OPC UA服务器
        
        Args:
            config: 服务器配置
        """
        super().__init__(config)
        
        # OPC UA特定配置
        self.port = config.get('port', 4840)
        self.endpoint = config.get('endpoint', f'opc.tcp://{self.host}:{self.port}/freeopcua/server/')
        
        # OPC UA服务器实例
        self.server = None
        self.nodes = {}  # 节点字典
        self.namespace_idx = None
        
        # 事件循环
        self.loop = None
        self.server_task = None
        
        # 初始化数据生成器
        self._init_data_generator()
        
        # 节点配置
        self.node_configs = config.get('nodes', [])
    
    def _init_data_generator(self):
        """初始化数据生成器"""
        gen_config = self.config.get('data_generator', {})
        if gen_config:
            self.data_generator = create_data_generator(gen_config)
    
    def start_server(self) -> None:
        """启动OPC UA服务器"""
        if not OPCUA_AVAILABLE:
            self._start_mock_server()
            return
        
        try:
            # 创建新的事件循环
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)
            
            # 在事件循环中运行服务器
            self.loop.run_until_complete(self._async_start_server())
            
        except Exception as e:
            self.logger.error(f"启动OPC UA服务器时出错: {e}")
    
    async def _async_start_server(self):
        """异步启动OPC UA服务器"""
        try:
            # 创建服务器
            self.server = Server()
            await self.server.init()
            
            # 设置端点
            self.server.set_endpoint(self.endpoint)
            
            # 设置服务器名称
            server_name = self.config.get('server_name', f'IoT Mock OPC UA Server {self.device_id}')
            await self.server.set_application_uri(f'urn:mock:iot:{self.device_id}')
            
            # 创建命名空间
            namespace_name = self.config.get('namespace', f'http://mock.iot.device/{self.device_id}')
            self.namespace_idx = await self.server.register_namespace(namespace_name)
            
            # 创建节点结构
            await self._create_nodes()
            
            # 启动服务器
            await self.server.start()
            self.logger.info(f"OPC UA服务器启动在 {self.endpoint}")
            
            # 服务器运行循环
            try:
                while self.running:
                    await asyncio.sleep(0.1)
            finally:
                await self.server.stop()
                
        except Exception as e:
            self.logger.error(f"OPC UA服务器运行时出错: {e}")
    
    def _start_mock_server(self):
        """启动模拟OPC UA服务器（不依赖asyncua库）"""
        self.logger.info(f"启动模拟OPC UA服务器在 {self.endpoint}")
        
        # 创建模拟节点
        self._create_mock_nodes()
        
        # 模拟服务器运行
        while self.running:
            time.sleep(1)
            # 更新节点数据
            self._update_mock_nodes()
    
    async def _create_nodes(self):
        """创建OPC UA节点结构"""
        if not self.server:
            return
        
        try:
            # 获取Objects节点
            objects_node = self.server.get_objects_node()
            
            # 创建设备节点
            device_node = await objects_node.add_object(
                self.namespace_idx, 
                self.device_id
            )
            
            # 创建传感器组节点
            sensors_node = await device_node.add_object(
                self.namespace_idx,
                "Sensors"
            )
            
            # 创建具体的数据节点
            for node_config in self.node_configs:
                await self._create_data_node(sensors_node, node_config)
            
            # 如果没有配置节点，创建默认节点
            if not self.node_configs:
                await self._create_default_nodes(sensors_node)
                
        except Exception as e:
            self.logger.error(f"创建OPC UA节点时出错: {e}")
    
    async def _create_data_node(self, parent_node: Node, node_config: Dict[str, Any]):
        """创建数据节点"""
        try:
            node_name = node_config.get('name', 'UnknownNode')
            data_type = node_config.get('data_type', 'Double')
            initial_value = node_config.get('initial_value', 0.0)
            
            # 根据数据类型创建节点
            if data_type.lower() == 'boolean':
                node = await parent_node.add_variable(
                    self.namespace_idx,
                    node_name,
                    initial_value,
                    ua.VariantType.Boolean
                )
            elif data_type.lower() == 'int32':
                node = await parent_node.add_variable(
                    self.namespace_idx,
                    node_name,
                    initial_value,
                    ua.VariantType.Int32
                )
            elif data_type.lower() == 'float':
                node = await parent_node.add_variable(
                    self.namespace_idx,
                    node_name,
                    initial_value,
                    ua.VariantType.Float
                )
            else:  # 默认Double
                node = await parent_node.add_variable(
                    self.namespace_idx,
                    node_name,
                    initial_value,
                    ua.VariantType.Double
                )
            
            # 设置节点为可写
            await node.set_writable()
            
            # 保存节点引用
            self.nodes[node_name] = {
                'node': node,
                'config': node_config,
                'current_value': initial_value
            }
            
            self.logger.info(f"创建OPC UA节点: {node_name}")
            
        except Exception as e:
            self.logger.error(f"创建数据节点 {node_config.get('name', 'Unknown')} 时出错: {e}")
    
    async def _create_default_nodes(self, parent_node: Node):
        """创建默认节点"""
        default_nodes = [
            {'name': 'Temperature', 'data_type': 'Double', 'initial_value': 25.0},
            {'name': 'Pressure', 'data_type': 'Double', 'initial_value': 1013.25},
            {'name': 'Humidity', 'data_type': 'Double', 'initial_value': 60.0},
            {'name': 'Status', 'data_type': 'Boolean', 'initial_value': True},
            {'name': 'Counter', 'data_type': 'Int32', 'initial_value': 0}
        ]
        
        for node_config in default_nodes:
            await self._create_data_node(parent_node, node_config)
    
    def _create_mock_nodes(self):
        """创建模拟节点（不使用asyncua）"""
        # 创建模拟节点结构
        default_nodes = [
            {'name': 'Temperature', 'data_type': 'Double', 'initial_value': 25.0},
            {'name': 'Pressure', 'data_type': 'Double', 'initial_value': 1013.25},
            {'name': 'Humidity', 'data_type': 'Double', 'initial_value': 60.0},
            {'name': 'Status', 'data_type': 'Boolean', 'initial_value': True},
            {'name': 'Counter', 'data_type': 'Int32', 'initial_value': 0}
        ]
        
        node_configs = self.node_configs if self.node_configs else default_nodes
        
        for node_config in node_configs:
            node_name = node_config.get('name', 'UnknownNode')
            initial_value = node_config.get('initial_value', 0.0)
            
            self.nodes[node_name] = {
                'node': None,  # 模拟节点
                'config': node_config,
                'current_value': initial_value
            }
            
            self.logger.info(f"创建模拟OPC UA节点: {node_name}")
    
    def _update_mock_nodes(self):
        """更新模拟节点数据"""
        # 更新节点值（模拟模式）
        for node_name, node_info in self.nodes.items():
            # 简单的数据变化模拟
            current_value = node_info['current_value']
            data_type = node_info['config'].get('data_type', 'Double')
            
            if data_type.lower() == 'boolean':
                # 随机切换布尔值
                import random
                if random.random() < 0.1:  # 10%的概率切换
                    node_info['current_value'] = not current_value
            elif data_type.lower() in ['double', 'float']:
                # 添加小幅度随机变化
                import random
                change = (random.random() - 0.5) * 2  # -1 到 1 的变化
                node_info['current_value'] = current_value + change
            elif data_type.lower() == 'int32':
                # 计数器递增
                node_info['current_value'] = (current_value + 1) % 10000
    
    def stop_server(self) -> None:
        """停止OPC UA服务器"""
        self.logger.info("停止OPC UA服务器")
        # 设置运行标志为False，服务器循环会自动退出
    
    def handle_client_request(self, client_socket, request_data: bytes) -> bytes:
        """处理客户端请求（OPC UA不需要实现此方法）"""
        # OPC UA使用自己的协议栈处理客户端请求
        return b""
    
    def update_data(self) -> None:
        """更新设备数据"""
        super().update_data()
        
        # 使用生成的数据更新OPC UA节点
        if hasattr(self, 'data_store') and self.data_store and self.nodes:
            if OPCUA_AVAILABLE and self.server:
                # 使用asyncua更新节点
                asyncio.run_coroutine_threadsafe(
                    self._async_update_nodes(),
                    self.loop
                )
            else:
                # 模拟模式更新
                self._update_mock_nodes_with_generated_data()
    
    async def _async_update_nodes(self):
        """异步更新节点数据"""
        try:
            for address, value in self.data_store.items():
                # 根据地址映射到节点
                node_name = self._address_to_node_name(address)
                if node_name and node_name in self.nodes:
                    node_info = self.nodes[node_name]
                    node = node_info['node']
                    if node:
                        await node.write_value(value)
                        node_info['current_value'] = value
                        
        except Exception as e:
            self.logger.error(f"更新OPC UA节点数据时出错: {e}")
    
    def _update_mock_nodes_with_generated_data(self):
        """使用生成的数据更新模拟节点"""
        for address, value in self.data_store.items():
            node_name = self._address_to_node_name(address)
            if node_name and node_name in self.nodes:
                self.nodes[node_name]['current_value'] = value
    
    def _address_to_node_name(self, address: int) -> Optional[str]:
        """将地址映射到节点名称"""
        # 简单的地址映射策略
        node_names = list(self.nodes.keys())
        if address < len(node_names):
            return node_names[address]
        return None
    
    def get_node_values(self) -> Dict[str, Any]:
        """获取所有节点的当前值"""
        values = {}
        for node_name, node_info in self.nodes.items():
            values[node_name] = node_info['current_value']
        return values
    
    def set_node_value(self, node_name: str, value: Any) -> bool:
        """设置节点值"""
        if node_name not in self.nodes:
            return False
        
        try:
            if OPCUA_AVAILABLE and self.server and self.loop:
                # 异步设置节点值
                async def _set_value():
                    node = self.nodes[node_name]['node']
                    if node:
                        await node.write_value(value)
                        self.nodes[node_name]['current_value'] = value
                
                asyncio.run_coroutine_threadsafe(_set_value(), self.loop)
            else:
                # 模拟模式直接设置
                self.nodes[node_name]['current_value'] = value
            
            return True
            
        except Exception as e:
            self.logger.error(f"设置节点值时出错: {e}")
            return False


def main():
    """主函数 - 用于直接运行服务器"""
    config = {
        'device_id': 'opcua_device_001',
        'host': '0.0.0.0',
        'port': 4840,
        'update_interval': 1.0,
        'server_name': 'IoT Mock OPC UA Server',
        'namespace': 'http://mock.iot.device/opcua001',
        'nodes': [
            {'name': 'Temperature', 'data_type': 'Double', 'initial_value': 25.0},
            {'name': 'Pressure', 'data_type': 'Double', 'initial_value': 1013.25},
            {'name': 'Humidity', 'data_type': 'Double', 'initial_value': 60.0},
            {'name': 'FlowRate', 'data_type': 'Double', 'initial_value': 100.0},
            {'name': 'Status', 'data_type': 'Boolean', 'initial_value': True},
            {'name': 'Counter', 'data_type': 'Int32', 'initial_value': 0}
        ],
        'data_generator': {
            'type': 'composite',
            'generators': [
                {
                    'type': 'sine',
                    'amplitude': 10.0,
                    'frequency': 0.1,
                    'offset': 25.0,
                    'addresses': [0]  # Temperature
                },
                {
                    'type': 'sine',
                    'amplitude': 50.0,
                    'frequency': 0.05,
                    'offset': 1013.25,
                    'phase': 1.57,
                    'addresses': [1]  # Pressure
                },
                {
                    'type': 'random',
                    'min_value': 40.0,
                    'max_value': 80.0,
                    'data_type': 'float',
                    'addresses': [2]  # Humidity
                },
                {
                    'type': 'linear',
                    'start_value': 50.0,
                    'end_value': 150.0,
                    'duration': 60.0,
                    'repeat': True,
                    'addresses': [3]  # FlowRate
                }
            ]
        }
    }
    
    server = OPCUAServer(config)
    
    try:
        print("启动OPC UA模拟设备服务器...")
        if not OPCUA_AVAILABLE:
            print("注意: 运行在模拟模式（未安装asyncua库）")
        
        server.start()
        
        # 保持服务器运行
        while True:
            time.sleep(5)
            status = server.get_status()
            node_values = server.get_node_values()
            print(f"状态: 运行={status['running']}, 连接数={status['connection_count']}")
            print(f"节点值: {node_values}")
            
    except KeyboardInterrupt:
        print("\n正在停止服务器...")
        server.stop()
        print("服务器已停止")


if __name__ == '__main__':
    main() 