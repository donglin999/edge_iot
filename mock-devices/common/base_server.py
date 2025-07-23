#!/usr/bin/env python3
"""
基础设备服务器类
"""
import threading
import time
import json
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional


class BaseDeviceServer(ABC):
    """基础设备服务器抽象类"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化基础设备服务器
        
        Args:
            config: 设备配置字典
        """
        self.config = config
        self.device_id = config.get('device_id', 'unknown_device')
        self.host = config.get('host', '0.0.0.0')
        self.port = config.get('port', 502)
        self.running = False
        self.server_thread = None
        self.data_update_thread = None
        self.logger = self._setup_logger()
        
        # 数据存储
        self.data_store = {}
        self.client_connections = []
        
        # 数据更新配置
        self.update_interval = config.get('update_interval', 1.0)  # 秒
        self.data_generator = None
        
    def _setup_logger(self) -> logging.Logger:
        """设置日志记录器"""
        logger = logging.getLogger(f"{self.__class__.__name__}_{self.device_id}")
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    @abstractmethod
    def start_server(self) -> None:
        """启动服务器 - 子类必须实现"""
        pass
    
    @abstractmethod
    def stop_server(self) -> None:
        """停止服务器 - 子类必须实现"""
        pass
    
    @abstractmethod
    def handle_client_request(self, client_socket, request_data: bytes) -> bytes:
        """处理客户端请求 - 子类必须实现"""
        pass
    
    def start(self) -> None:
        """启动设备服务器"""
        if self.running:
            self.logger.warning(f"设备 {self.device_id} 已经在运行中")
            return
        
        self.running = True
        self.logger.info(f"启动设备服务器 {self.device_id} 在 {self.host}:{self.port}")
        
        # 启动服务器线程
        self.server_thread = threading.Thread(target=self.start_server)
        self.server_thread.daemon = True
        self.server_thread.start()
        
        # 启动数据更新线程
        self.data_update_thread = threading.Thread(target=self._data_update_loop)
        self.data_update_thread.daemon = True
        self.data_update_thread.start()
        
        self.logger.info(f"设备服务器 {self.device_id} 启动成功")
    
    def stop(self) -> None:
        """停止设备服务器"""
        if not self.running:
            self.logger.warning(f"设备 {self.device_id} 未在运行中")
            return
        
        self.logger.info(f"停止设备服务器 {self.device_id}")
        self.running = False
        
        # 停止服务器
        self.stop_server()
        
        # 等待线程结束
        if self.server_thread and self.server_thread.is_alive():
            self.server_thread.join(timeout=5)
        
        if self.data_update_thread and self.data_update_thread.is_alive():
            self.data_update_thread.join(timeout=5)
        
        self.logger.info(f"设备服务器 {self.device_id} 已停止")
    
    def _data_update_loop(self) -> None:
        """数据更新循环"""
        while self.running:
            try:
                self.update_data()
                time.sleep(self.update_interval)
            except Exception as e:
                self.logger.error(f"数据更新时发生错误: {e}")
                time.sleep(self.update_interval)
    
    def update_data(self) -> None:
        """更新设备数据 - 子类可以重写"""
        if self.data_generator:
            new_data = self.data_generator.generate_data()
            self.data_store.update(new_data)
    
    def get_data(self, address: int) -> Any:
        """获取指定地址的数据"""
        return self.data_store.get(address, 0)
    
    def set_data(self, address: int, value: Any) -> None:
        """设置指定地址的数据"""
        self.data_store[address] = value
    
    def get_connection_count(self) -> int:
        """获取当前连接数"""
        return len(self.client_connections)
    
    def add_client_connection(self, client_info: Dict[str, Any]) -> None:
        """添加客户端连接"""
        self.client_connections.append(client_info)
        self.logger.info(f"新客户端连接: {client_info}")
    
    def remove_client_connection(self, client_info: Dict[str, Any]) -> None:
        """移除客户端连接"""
        if client_info in self.client_connections:
            self.client_connections.remove(client_info)
            self.logger.info(f"客户端断开连接: {client_info}")
    
    def get_status(self) -> Dict[str, Any]:
        """获取设备状态"""
        return {
            'device_id': self.device_id,
            'device_type': self.__class__.__name__,
            'running': self.running,
            'host': self.host,
            'port': self.port,
            'connection_count': self.get_connection_count(),
            'data_points': len(self.data_store),
            'update_interval': self.update_interval
        }
    
    def load_config_from_file(self, config_file: str) -> None:
        """从文件加载配置"""
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            self.config.update(config)
            self.logger.info(f"从文件加载配置: {config_file}")
        except Exception as e:
            self.logger.error(f"加载配置文件失败: {e}")
    
    def save_config_to_file(self, config_file: str) -> None:
        """保存配置到文件"""
        try:
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            self.logger.info(f"保存配置到文件: {config_file}")
        except Exception as e:
            self.logger.error(f"保存配置文件失败: {e}")
    
    def __enter__(self):
        """上下文管理器入口"""
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.stop() 