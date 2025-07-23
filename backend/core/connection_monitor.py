#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
连接监控模块 - 监控数采进程与mock设备的连接状态
"""

import os
import sys
import time
import socket
import logging
import asyncio
import threading
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from logs.log_config import get_logger
from models.process_models import ConnectionStatus, ConnectionInfo

logger = get_logger("backend", "core", "connection_monitor")

@dataclass
class ConnectionCheckResult:
    """连接检查结果"""
    success: bool
    status: ConnectionStatus
    message: str
    response_time_ms: float = 0.0
    error_details: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)

class ConnectionMonitor:
    """连接监控类 - 监控数采进程与mock设备的连接状态"""
    
    def __init__(self):
        self.logger = get_logger("backend", "core", "connection_monitor")
        self.connection_info: Dict[str, ConnectionInfo] = {}
        self.check_results: Dict[str, List[ConnectionCheckResult]] = {}
        self.monitoring_active = False
        self.monitoring_thread: Optional[threading.Thread] = None
        self.check_interval = 30  # 默认30秒检查一次
        self.max_history = 100  # 保存最近100次检查结果
        self.callbacks: Dict[str, callable] = {}
    
    def register_connection(self, process_name: str, connection_info: ConnectionInfo) -> bool:
        """注册连接信息"""
        try:
            self.connection_info[process_name] = connection_info
            self.check_results[process_name] = []
            self.logger.info(f"注册连接监控: {process_name} -> {connection_info.device_ip}:{connection_info.device_port}")
            return True
        except Exception as e:
            self.logger.error(f"注册连接监控失败: {e}")
            return False
    
    def unregister_connection(self, process_name: str) -> bool:
        """取消注册连接信息"""
        if process_name in self.connection_info:
            del self.connection_info[process_name]
            if process_name in self.check_results:
                del self.check_results[process_name]
            if process_name in self.callbacks:
                del self.callbacks[process_name]
            self.logger.info(f"取消连接监控: {process_name}")
            return True
        return False
    
    def set_callback(self, process_name: str, callback: callable):
        """设置连接状态变化回调函数"""
        self.callbacks[process_name] = callback
        self.logger.info(f"设置连接状态回调: {process_name}")
    
    def start_monitoring(self, interval: int = 30):
        """启动连接监控"""
        if self.monitoring_active:
            return
        
        self.check_interval = interval
        self.monitoring_active = True
        self.monitoring_thread = threading.Thread(target=self._monitor_connections, daemon=True)
        self.monitoring_thread.start()
        self.logger.info(f"连接监控已启动，检查间隔: {interval}秒")
    
    def stop_monitoring(self):
        """停止连接监控"""
        self.monitoring_active = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=5)
        self.logger.info("连接监控已停止")
    
    def _monitor_connections(self):
        """连接监控线程"""
        while self.monitoring_active:
            try:
                for process_name, conn_info in list(self.connection_info.items()):
                    # 检查连接状态
                    result = self.check_connection(process_name)
                    
                    # 更新连接信息
                    if result.success:
                        conn_info.is_connected = True
                        conn_info.last_connect_time = datetime.now()
                        conn_info.status = ConnectionStatus.CONNECTED
                    else:
                        conn_info.is_connected = False
                        conn_info.connection_errors += 1
                        conn_info.status = result.status
                    
                    # 保存检查结果
                    self.check_results[process_name].append(result)
                    if len(self.check_results[process_name]) > self.max_history:
                        self.check_results[process_name].pop(0)
                    
                    # 调用回调函数
                    if process_name in self.callbacks:
                        try:
                            self.callbacks[process_name](conn_info)
                        except Exception as e:
                            self.logger.error(f"回调函数执行失败: {e}")
                
                # 等待下一次检查
                time.sleep(self.check_interval)
                
            except Exception as e:
                self.logger.error(f"连接监控线程异常: {e}")
                time.sleep(5)  # 发生异常时等待5秒
    
    def check_connection(self, process_name: str) -> ConnectionCheckResult:
        """检查连接状态"""
        if process_name not in self.connection_info:
            return ConnectionCheckResult(
                success=False,
                status=ConnectionStatus.UNKNOWN,
                message=f"未注册的连接: {process_name}"
            )
        
        conn_info = self.connection_info[process_name]
        
        # 如果没有IP或端口，无法检查连接
        if not conn_info.device_ip or not conn_info.device_port:
            return ConnectionCheckResult(
                success=False,
                status=ConnectionStatus.UNKNOWN,
                message=f"连接信息不完整: {process_name}"
            )
        
        start_time = time.time()
        
        try:
            # 根据协议类型选择不同的检查方法
            if conn_info.protocol_type.lower() in ["modbus", "modbus_tcp"]:
                result = self._check_modbus_connection(conn_info)
            elif conn_info.protocol_type.lower() in ["opcua", "opc_ua"]:
                result = self._check_opcua_connection(conn_info)
            elif conn_info.protocol_type.lower() in ["melsec", "melseca1enet", "mc"]:
                result = self._check_melsec_connection(conn_info)
            else:
                # 默认使用TCP连接检查
                result = self._check_tcp_connection(conn_info)
            
            # 计算响应时间
            response_time = (time.time() - start_time) * 1000  # 毫秒
            result.response_time_ms = round(response_time, 2)
            
            return result
            
        except Exception as e:
            end_time = time.time()
            response_time = (end_time - start_time) * 1000  # 毫秒
            
            return ConnectionCheckResult(
                success=False,
                status=ConnectionStatus.ERROR,
                message=f"连接检查异常: {str(e)}",
                response_time_ms=round(response_time, 2),
                error_details=str(e)
            )
    
    def _check_tcp_connection(self, conn_info: ConnectionInfo) -> ConnectionCheckResult:
        """检查TCP连接"""
        try:
            # 创建套接字
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)  # 5秒超时
            
            # 尝试连接
            result = sock.connect_ex((conn_info.device_ip, conn_info.device_port))
            sock.close()
            
            if result == 0:
                return ConnectionCheckResult(
                    success=True,
                    status=ConnectionStatus.CONNECTED,
                    message=f"TCP连接成功: {conn_info.device_ip}:{conn_info.device_port}"
                )
            else:
                return ConnectionCheckResult(
                    success=False,
                    status=ConnectionStatus.DISCONNECTED,
                    message=f"TCP连接失败: {conn_info.device_ip}:{conn_info.device_port}",
                    error_details=f"错误码: {result}"
                )
                
        except Exception as e:
            return ConnectionCheckResult(
                success=False,
                status=ConnectionStatus.ERROR,
                message=f"TCP连接异常: {conn_info.device_ip}:{conn_info.device_port}",
                error_details=str(e)
            )
    
    def _check_modbus_connection(self, conn_info: ConnectionInfo) -> ConnectionCheckResult:
        """检查Modbus连接"""
        # 首先尝试TCP连接
        tcp_result = self._check_tcp_connection(conn_info)
        if not tcp_result.success:
            return tcp_result
        
        try:
            # 尝试导入pymodbus库
            try:
                from pymodbus.client.sync import ModbusTcpClient
                from pymodbus.exceptions import ModbusException
                
                # 创建Modbus客户端
                client = ModbusTcpClient(conn_info.device_ip, port=conn_info.device_port, timeout=5)
                
                # 尝试连接
                if client.connect():
                    # 尝试读取保持寄存器0（测试连接）
                    try:
                        result = client.read_holding_registers(0, 1)
                        if result and not result.isError():
                            message = "Modbus连接成功并读取寄存器"
                        else:
                            message = "Modbus连接成功但读取寄存器失败"
                    except:
                        message = "Modbus连接成功但读取寄存器异常"
                    
                    client.close()
                    return ConnectionCheckResult(
                        success=True,
                        status=ConnectionStatus.CONNECTED,
                        message=message
                    )
                else:
                    client.close()
                    return ConnectionCheckResult(
                        success=False,
                        status=ConnectionStatus.ERROR,
                        message="Modbus连接失败",
                        error_details="无法建立Modbus连接"
                    )
                    
            except ImportError:
                # 如果没有pymodbus库，回退到TCP连接检查
                self.logger.warning("未安装pymodbus库，使用TCP连接检查")
                return ConnectionCheckResult(
                    success=tcp_result.success,
                    status=tcp_result.status,
                    message=f"TCP连接成功（未安装pymodbus库）: {conn_info.device_ip}:{conn_info.device_port}"
                )
                
        except Exception as e:
            return ConnectionCheckResult(
                success=False,
                status=ConnectionStatus.ERROR,
                message=f"Modbus连接异常: {conn_info.device_ip}:{conn_info.device_port}",
                error_details=str(e)
            )
    
    def _check_opcua_connection(self, conn_info: ConnectionInfo) -> ConnectionCheckResult:
        """检查OPC UA连接"""
        # 首先尝试TCP连接
        tcp_result = self._check_tcp_connection(conn_info)
        if not tcp_result.success:
            return tcp_result
        
        try:
            # 尝试导入opcua库
            try:
                from opcua import Client
                
                # 构建OPC UA URL
                url = f"opc.tcp://{conn_info.device_ip}:{conn_info.device_port}"
                
                # 创建客户端
                client = Client(url)
                client.set_security_string("None")  # 不使用安全设置
                
                # 设置超时
                client.session_timeout = 5000  # 5秒
                
                # 尝试连接
                client.connect()
                
                # 尝试获取根节点
                root = client.get_root_node()
                name = root.get_browse_name()
                
                # 断开连接
                client.disconnect()
                
                return ConnectionCheckResult(
                    success=True,
                    status=ConnectionStatus.CONNECTED,
                    message=f"OPC UA连接成功: {url}, 根节点: {name}"
                )
                
            except ImportError:
                # 如果没有opcua库，回退到TCP连接检查
                self.logger.warning("未安装opcua库，使用TCP连接检查")
                return ConnectionCheckResult(
                    success=tcp_result.success,
                    status=tcp_result.status,
                    message=f"TCP连接成功（未安装opcua库）: {conn_info.device_ip}:{conn_info.device_port}"
                )
                
        except Exception as e:
            return ConnectionCheckResult(
                success=False,
                status=ConnectionStatus.ERROR,
                message=f"OPC UA连接异常: {conn_info.device_ip}:{conn_info.device_port}",
                error_details=str(e)
            )
    
    def _check_melsec_connection(self, conn_info: ConnectionInfo) -> ConnectionCheckResult:
        """检查三菱PLC连接"""
        # 首先尝试TCP连接
        tcp_result = self._check_tcp_connection(conn_info)
        if not tcp_result.success:
            return tcp_result
        
        # 由于没有通用的三菱PLC库，我们只能使用TCP连接检查
        return ConnectionCheckResult(
            success=tcp_result.success,
            status=tcp_result.status,
            message=f"TCP连接成功（三菱PLC）: {conn_info.device_ip}:{conn_info.device_port}"
        )
    
    def get_connection_status(self, process_name: str) -> Optional[ConnectionInfo]:
        """获取连接状态"""
        return self.connection_info.get(process_name)
    
    def get_all_connection_status(self) -> Dict[str, ConnectionInfo]:
        """获取所有连接状态"""
        return self.connection_info.copy()
    
    def get_connection_history(self, process_name: str, limit: int = 10) -> List[ConnectionCheckResult]:
        """获取连接历史记录"""
        if process_name not in self.check_results:
            return []
        
        results = self.check_results[process_name]
        return results[-limit:] if limit > 0 else results
    
    def get_connection_statistics(self, process_name: str) -> Dict[str, Any]:
        """获取连接统计信息"""
        if process_name not in self.connection_info or process_name not in self.check_results:
            return {}
        
        conn_info = self.connection_info[process_name]
        results = self.check_results[process_name]
        
        if not results:
            return {
                "process_name": process_name,
                "device_ip": conn_info.device_ip,
                "device_port": conn_info.device_port,
                "protocol_type": conn_info.protocol_type,
                "is_connected": conn_info.is_connected,
                "connection_errors": conn_info.connection_errors,
                "status": conn_info.status.value,
                "last_connect_time": conn_info.last_connect_time.isoformat() if conn_info.last_connect_time else None,
                "check_count": 0,
                "success_rate": 0.0,
                "avg_response_time": 0.0
            }
        
        # 计算成功率
        success_count = sum(1 for r in results if r.success)
        success_rate = success_count / len(results) * 100
        
        # 计算平均响应时间
        avg_response_time = sum(r.response_time_ms for r in results) / len(results)
        
        # 获取最近一次检查结果
        latest = results[-1]
        
        return {
            "process_name": process_name,
            "device_ip": conn_info.device_ip,
            "device_port": conn_info.device_port,
            "protocol_type": conn_info.protocol_type,
            "is_connected": conn_info.is_connected,
            "connection_errors": conn_info.connection_errors,
            "status": conn_info.status.value,
            "last_connect_time": conn_info.last_connect_time.isoformat() if conn_info.last_connect_time else None,
            "check_count": len(results),
            "success_rate": round(success_rate, 2),
            "avg_response_time": round(avg_response_time, 2),
            "latest_check": {
                "timestamp": latest.timestamp.isoformat(),
                "success": latest.success,
                "status": latest.status.value,
                "message": latest.message,
                "response_time_ms": latest.response_time_ms,
                "error_details": latest.error_details
            }
        }

# 全局实例
connection_monitor = ConnectionMonitor()