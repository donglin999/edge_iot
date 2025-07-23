#!/usr/bin/env python3
"""
设备管理器
统一管理所有模拟设备
"""
import threading
import time
import json
import logging
from typing import Dict, Any, List, Optional
from pathlib import Path
import sys
import os

# 添加上级目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from common.base_server import BaseDeviceServer


class DeviceManager:
    """设备管理器"""
    
    def __init__(self, config_file: Optional[str] = None):
        """
        初始化设备管理器
        
        Args:
            config_file: 配置文件路径
        """
        self.devices = {}  # 设备实例字典
        self.device_configs = {}  # 设备配置字典
        self.running = False
        self.manager_thread = None
        
        # 设置日志
        self.logger = self._setup_logger()
        
        # 加载配置
        if config_file:
            self.load_config_from_file(config_file)
    
    def _setup_logger(self) -> logging.Logger:
        """设置日志记录器"""
        logger = logging.getLogger("DeviceManager")
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def add_device(self, device_id: str, device_type: str, config: Dict[str, Any]) -> bool:
        """
        添加设备
        
        Args:
            device_id: 设备ID
            device_type: 设备类型 (modbus_tcp, opcua, mitsubishi_plc)
            config: 设备配置
            
        Returns:
            bool: 添加成功返回True
        """
        try:
            # 创建设备实例
            device = self._create_device_instance(device_type, config)
            if not device:
                self.logger.error(f"无法创建设备类型 {device_type} 的实例")
                return False
            
            # 保存设备
            self.devices[device_id] = device
            self.device_configs[device_id] = {
                'type': device_type,
                'config': config
            }
            
            self.logger.info(f"添加设备: {device_id} ({device_type})")
            return True
            
        except Exception as e:
            self.logger.error(f"添加设备 {device_id} 时出错: {e}")
            return False
    
    def _create_device_instance(self, device_type: str, config: Dict[str, Any]) -> Optional[BaseDeviceServer]:
        """创建设备实例"""
        try:
            if device_type == 'modbus_tcp':
                sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'modbus'))
                from modbus_tcp_server import ModbusTCPServer
                return ModbusTCPServer(config)
            elif device_type == 'opcua':
                sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'opcua'))
                from opcua_server import OPCUAServer
                return OPCUAServer(config)
            elif device_type == 'mitsubishi_plc':
                sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'mitsubishi'))
                from plc_server import MitsubishiPLCServer
                return MitsubishiPLCServer(config)
            else:
                self.logger.error(f"不支持的设备类型: {device_type}")
                return None
        except ImportError as e:
            self.logger.error(f"导入设备类型 {device_type} 时出错: {e}")
            return None
    
    def remove_device(self, device_id: str) -> bool:
        """
        移除设备
        
        Args:
            device_id: 设备ID
            
        Returns:
            bool: 移除成功返回True
        """
        if device_id not in self.devices:
            self.logger.warning(f"设备 {device_id} 不存在")
            return False
        
        try:
            # 停止设备
            device = self.devices[device_id]
            if device.running:
                device.stop()
            
            # 移除设备
            del self.devices[device_id]
            del self.device_configs[device_id]
            
            self.logger.info(f"移除设备: {device_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"移除设备 {device_id} 时出错: {e}")
            return False
    
    def start_device(self, device_id: str) -> bool:
        """
        启动设备
        
        Args:
            device_id: 设备ID
            
        Returns:
            bool: 启动成功返回True
        """
        if device_id not in self.devices:
            self.logger.error(f"设备 {device_id} 不存在")
            return False
        
        try:
            device = self.devices[device_id]
            if not device.running:
                device.start()
                self.logger.info(f"启动设备: {device_id}")
                return True
            else:
                self.logger.warning(f"设备 {device_id} 已经在运行")
                return True
                
        except Exception as e:
            self.logger.error(f"启动设备 {device_id} 时出错: {e}")
            return False
    
    def stop_device(self, device_id: str) -> bool:
        """
        停止设备
        
        Args:
            device_id: 设备ID
            
        Returns:
            bool: 停止成功返回True
        """
        if device_id not in self.devices:
            self.logger.error(f"设备 {device_id} 不存在")
            return False
        
        try:
            device = self.devices[device_id]
            if device.running:
                device.stop()
                self.logger.info(f"停止设备: {device_id}")
                return True
            else:
                self.logger.warning(f"设备 {device_id} 已经停止")
                return True
                
        except Exception as e:
            self.logger.error(f"停止设备 {device_id} 时出错: {e}")
            return False
    
    def start_all_devices(self) -> bool:
        """
        启动所有设备
        
        Returns:
            bool: 全部启动成功返回True
        """
        success = True
        for device_id in self.devices:
            if not self.start_device(device_id):
                success = False
        
        return success
    
    def stop_all_devices(self) -> bool:
        """
        停止所有设备
        
        Returns:
            bool: 全部停止成功返回True
        """
        success = True
        for device_id in self.devices:
            if not self.stop_device(device_id):
                success = False
        
        return success
    
    def get_device_status(self, device_id: str) -> Optional[Dict[str, Any]]:
        """
        获取设备状态
        
        Args:
            device_id: 设备ID
            
        Returns:
            Dict[str, Any]: 设备状态信息
        """
        if device_id not in self.devices:
            return None
        
        try:
            device = self.devices[device_id]
            status = device.get_status()
            status['device_type'] = self.device_configs[device_id]['type']
            return status
        except Exception as e:
            self.logger.error(f"获取设备 {device_id} 状态时出错: {e}")
            return None
    
    def get_all_devices_status(self) -> Dict[str, Any]:
        """
        获取所有设备状态
        
        Returns:
            Dict[str, Any]: 所有设备状态信息
        """
        status = {}
        for device_id in self.devices:
            device_status = self.get_device_status(device_id)
            if device_status:
                status[device_id] = device_status
        
        return status
    
    def get_device_list(self) -> List[str]:
        """
        获取设备列表
        
        Returns:
            List[str]: 设备ID列表
        """
        return list(self.devices.keys())
    
    def start_manager(self) -> None:
        """启动设备管理器"""
        if self.running:
            self.logger.warning("设备管理器已经在运行")
            return
        
        self.running = True
        self.logger.info("启动设备管理器")
        
        # 启动管理器线程
        self.manager_thread = threading.Thread(target=self._manager_loop)
        self.manager_thread.daemon = True
        self.manager_thread.start()
        
        # 启动所有设备
        self.start_all_devices()
    
    def stop_manager(self) -> None:
        """停止设备管理器"""
        if not self.running:
            self.logger.warning("设备管理器未在运行")
            return
        
        self.logger.info("停止设备管理器")
        
        # 停止所有设备
        self.stop_all_devices()
        
        # 停止管理器
        self.running = False
        
        if self.manager_thread and self.manager_thread.is_alive():
            self.manager_thread.join(timeout=5)
        
        self.logger.info("设备管理器已停止")
    
    def _manager_loop(self) -> None:
        """管理器主循环"""
        while self.running:
            try:
                # 检查设备状态
                self._check_devices_health()
                
                # 等待
                time.sleep(5)
                
            except Exception as e:
                self.logger.error(f"管理器循环出错: {e}")
                time.sleep(1)
    
    def _check_devices_health(self) -> None:
        """检查设备健康状态"""
        for device_id, device in self.devices.items():
            try:
                status = device.get_status()
                if not status['running']:
                    self.logger.warning(f"设备 {device_id} 未运行")
            except Exception as e:
                self.logger.error(f"检查设备 {device_id} 状态时出错: {e}")
    
    def load_config_from_file(self, config_file: str) -> bool:
        """
        从文件加载配置
        
        Args:
            config_file: 配置文件路径
            
        Returns:
            bool: 加载成功返回True
        """
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            # 清除现有设备
            self.stop_all_devices()
            self.devices.clear()
            self.device_configs.clear()
            
            # 加载设备配置
            devices_config = config.get('devices', [])
            for device_config in devices_config:
                device_id = device_config.get('device_id')
                device_type = device_config.get('device_type')
                device_settings = device_config.get('settings', {})
                
                if device_id and device_type:
                    self.add_device(device_id, device_type, device_settings)
            
            self.logger.info(f"从文件加载配置: {config_file}")
            return True
            
        except Exception as e:
            self.logger.error(f"加载配置文件失败: {e}")
            return False
    
    def save_config_to_file(self, config_file: str) -> bool:
        """
        保存配置到文件
        
        Args:
            config_file: 配置文件路径
            
        Returns:
            bool: 保存成功返回True
        """
        try:
            devices_config = []
            for device_id, device_info in self.device_configs.items():
                devices_config.append({
                    'device_id': device_id,
                    'device_type': device_info['type'],
                    'settings': device_info['config']
                })
            
            config = {
                'devices': devices_config,
                'manager_settings': {
                    'check_interval': 5,
                    'auto_restart': True
                }
            }
            
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"保存配置到文件: {config_file}")
            return True
            
        except Exception as e:
            self.logger.error(f"保存配置文件失败: {e}")
            return False
    
    def __enter__(self):
        """上下文管理器入口"""
        self.start_manager()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.stop_manager()


def main():
    """主函数 - 用于直接运行设备管理器"""
    # 示例配置
    config = {
        'devices': [
            {
                'device_id': 'modbus_001',
                'device_type': 'modbus_tcp',
                'settings': {
                    'device_id': 'modbus_001',
                    'host': '0.0.0.0',
                    'port': 502,
                    'unit_id': 1,
                    'update_interval': 1.0,
                    'data_generator': {
                        'type': 'sine',
                        'amplitude': 1000,
                        'frequency': 0.1,
                        'offset': 2000,
                        'addresses': [0, 1, 2]
                    }
                }
            },
            {
                'device_id': 'opcua_001',
                'device_type': 'opcua',
                'settings': {
                    'device_id': 'opcua_001',
                    'host': '0.0.0.0',
                    'port': 4840,
                    'update_interval': 1.0
                }
            },
            {
                'device_id': 'plc_001',
                'device_type': 'mitsubishi_plc',
                'settings': {
                    'device_id': 'plc_001',
                    'host': '0.0.0.0',
                    'port': 5001,
                    'update_interval': 1.0
                }
            }
        ]
    }
    
    # 保存示例配置
    with open('device_manager_config.json', 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
    
    # 启动设备管理器
    with DeviceManager('device_manager_config.json') as manager:
        try:
            print("设备管理器已启动，按 Ctrl+C 停止")
            
            while True:
                time.sleep(10)
                
                # 显示状态
                status = manager.get_all_devices_status()
                print("\n=== 设备状态 ===")
                for device_id, device_status in status.items():
                    print(f"{device_id}: 运行={device_status['running']}, "
                          f"类型={device_status['device_type']}, "
                          f"连接数={device_status['connection_count']}")
                    
        except KeyboardInterrupt:
            print("\n正在停止设备管理器...")


if __name__ == '__main__':
    main() 