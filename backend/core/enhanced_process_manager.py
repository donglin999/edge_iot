import asyncio
import subprocess
import psutil
import time
import os
import signal
import logging
import json
import sqlite3
import socket
from typing import Dict, List, Optional, Any, AsyncGenerator
from dataclasses import dataclass, asdict, field
from enum import Enum
from pathlib import Path
import threading
from datetime import datetime, timedelta
import sys
import concurrent.futures

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from logs.log_config import get_logger
from backend.models.process_models import ProcessState, EnhancedProcessInfo, ConnectionInfo, ConnectionStatus, PerformanceMetrics, HealthStatus
from core.connection_monitor import connection_monitor, ConnectionCheckResult
from core.data_acquisition_monitor import data_acquisition_monitor, DataFlowStatus, DataAcquisitionAlert

logger = get_logger("backend", "core", "enhanced_process_manager")

@dataclass
class ProcessResult:
    success: bool
    message: str
    process_name: str
    error_details: Optional[str] = None

class EnhancedProcessManager:
    """增强版进程管理器 - 支持与project-data-acquisition进程的通信和监控"""
    
    def __init__(self, config_file: str = "backend/configs/process_config.json"):
        self.processes: Dict[str, EnhancedProcessInfo] = {}
        self.subprocesses: Dict[str, subprocess.Popen] = {}
        self.monitoring_active = False
        self.monitoring_thread: Optional[threading.Thread] = None
        self.config_file = config_file
        self.logger = get_logger("backend", "core", "enhanced_process_manager")
        self.websocket_manager = None
        self.db_path = "backend/data/process_monitoring.db"
        
        # 初始化数据库
        self._init_database()
        
        # 加载进程配置
        self.load_process_configs()
        
        # 启动监控线程
        self.start_monitoring()
    
    def set_websocket_manager(self, websocket_manager):
        """设置WebSocket管理器用于实时推送"""
        self.websocket_manager = websocket_manager
    
    def _init_database(self):
        """初始化数据库存储"""
        try:
            # 确保数据目录存在
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 创建进程状态表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS process_status (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    process_name TEXT NOT NULL,
                    status TEXT NOT NULL,
                    pid INTEGER,
                    cpu_percent REAL DEFAULT 0.0,
                    memory_mb REAL DEFAULT 0.0,
                    start_time TEXT,
                    last_heartbeat TEXT,
                    connection_status TEXT DEFAULT 'unknown',
                    data_collection_rate REAL DEFAULT 0.0,
                    last_data_time TEXT,
                    health_score REAL DEFAULT 100.0,
                    error_count_24h INTEGER DEFAULT 0,
                    restart_count INTEGER DEFAULT 0,
                    last_error TEXT,
                    timestamp TEXT NOT NULL,
                    UNIQUE(process_name, timestamp)
                )
            ''')
            
            # 创建性能指标表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS performance_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    process_name TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    cpu_percent REAL DEFAULT 0.0,
                    memory_mb REAL DEFAULT 0.0,
                    data_points_per_minute REAL DEFAULT 0.0,
                    error_rate REAL DEFAULT 0.0,
                    response_time_ms REAL DEFAULT 0.0
                )
            ''')
            
            # 创建连接状态表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS connection_status (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    process_name TEXT NOT NULL,
                    device_ip TEXT,
                    device_port INTEGER,
                    is_connected BOOLEAN DEFAULT 0,
                    last_connect_time TEXT,
                    connection_errors INTEGER DEFAULT 0,
                    protocol_type TEXT,
                    status TEXT DEFAULT 'unknown',
                    timestamp TEXT NOT NULL
                )
            ''')
            
            conn.commit()
            conn.close()
            self.logger.info("数据库初始化完成")
            
        except Exception as e:
            self.logger.error(f"初始化数据库失败: {e}")

    def load_process_configs(self):
        """从配置文件加载进程定义"""
        try:
            # 尝试多个可能的配置文件路径
            possible_paths = [
                self.config_file,
                os.path.join(os.getcwd(), self.config_file),
                os.path.join(os.path.dirname(__file__), "..", "..", self.config_file),
                "backend/configs/process_config.json",
                os.path.join(os.path.dirname(__file__), "..", "configs", "process_config.json")
            ]
            
            config_path = None
            for path in possible_paths:
                self.logger.info(f"尝试配置文件路径: {path}")
                if os.path.exists(path):
                    config_path = path
                    self.logger.info(f"找到配置文件: {config_path}")
                    break
            
            if config_path and os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                
                # 清空当前进程配置，只保留配置文件中的进程
                self.processes.clear()
                
                # 加载进程定义
                for name, cfg in config.get("processes", {}).items():
                    # 创建连接信息
                    connection_info = ConnectionInfo(
                        device_ip=cfg.get("device_ip"),
                        device_port=cfg.get("device_port"),
                        protocol_type=cfg.get("type", "unknown")
                    )
                    
                    self.processes[name] = EnhancedProcessInfo(
                        name=name,
                        type=cfg.get("type", "unknown"),
                        status=ProcessState.STOPPED,
                        config_file=cfg.get("config_file"),
                        command=cfg.get("command", []),
                        description=cfg.get("description"),
                        auto_restart=cfg.get("auto_restart", True),
                        max_restarts=cfg.get("max_restarts", 5),
                        connection_info=connection_info
                    )
                
                self.logger.info(f"加载了 {len(self.processes)} 个进程配置")
            else:
                # 如果配置文件不存在，创建空配置
                self.processes.clear()
                self.logger.warning(f"配置文件不存在，尝试的路径: {possible_paths}")
                self.logger.warning("使用空配置")
                
        except Exception as e:
            self.logger.error(f"加载进程配置失败: {e}")
            # 发生错误时清空配置，不使用默认配置
            self.processes.clear()
    
    def get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        return {
            "processes": {
                "modbus_collector": {
                    "type": "modbus",
                    "command": ["python", "-m", "apps.collector.modbustcp_influx"],
                    "config_file": "configs/modbus_config.json",
                    "description": "Modbus TCP数据采集进程",
                    "auto_restart": True,
                    "max_restarts": 5,
                    "working_directory": "project-data-acquisition_backend"
                },
                "opcua_collector": {
                    "type": "opcua",
                    "command": ["python", "-m", "apps.collector.opcua_influx"],
                    "config_file": "configs/opcua_config.json",
                    "description": "OPC UA数据采集进程",
                    "auto_restart": True,
                    "max_restarts": 5,
                    "working_directory": "project-data-acquisition_backend"
                },
                "melsoft_collector": {
                    "type": "melsoft",
                    "command": ["python", "-m", "apps.collector.melseca1enet_influx"],
                    "config_file": "configs/melsoft_config.json",
                    "description": "Melsoft A1E数据采集进程",
                    "auto_restart": False,
                    "max_restarts": 3,
                    "working_directory": "project-data-acquisition_backend"
                },
                "plc_collector": {
                    "type": "plc",
                    "command": ["python", "-m", "apps.collector.plc_influx"],
                    "config_file": "configs/plc_config.json",
                    "description": "通用PLC数据采集进程",
                    "auto_restart": True,
                    "max_restarts": 5,
                    "working_directory": "project-data-acquisition_backend"
                }
            }
        }
    
    def get_default_processes(self) -> Dict[str, EnhancedProcessInfo]:
        """获取默认进程配置"""
        config = self.get_default_config()
        processes = {}
        
        for name, cfg in config.get("processes", {}).items():
            connection_info = ConnectionInfo(
                protocol_type=cfg.get("type", "unknown")
            )
            
            processes[name] = EnhancedProcessInfo(
                name=name,
                type=cfg.get("type", "unknown"),
                status=ProcessState.STOPPED,
                config_file=cfg.get("config_file"),
                command=cfg.get("command", []),
                description=cfg.get("description"),
                auto_restart=cfg.get("auto_restart", True),
                max_restarts=cfg.get("max_restarts", 5),
                connection_info=connection_info
            )
        
        return processes
    
    def reload_config(self):
        """重新加载进程配置"""
        self.logger.info("重新加载进程配置...")
        old_processes = set(self.processes.keys())
        self.load_process_configs()
        new_processes = set(self.processes.keys())
        
        added = new_processes - old_processes
        removed = old_processes - new_processes
        
        if added:
            self.logger.info(f"新增进程: {list(added)}")
        if removed:
            self.logger.info(f"移除进程: {list(removed)}")
            # 停止已移除的进程
            for process_name in removed:
                if process_name in self.subprocesses:
                    self.stop_process(process_name)
    
    def start_process(self, process_name: str) -> bool:
        """启动指定进程"""
        if process_name not in self.processes:
            self.logger.error(f"进程 {process_name} 不存在")
            return False
        
        process_info = self.processes[process_name]
        
        if process_info.status == ProcessState.RUNNING:
            self.logger.warning(f"进程 {process_name} 已在运行")
            return True
        
        try:
            process_info.status = ProcessState.STARTING
            process_info.last_error = None
            
            self.logger.info(f"开始启动进程: {process_name}")
            
            # 通知状态变化
            self._notify_process_status_change(process_name, process_info)
            
            # 设置工作目录
            cwd = os.getcwd()
            self.logger.info(f"当前工作目录: {cwd}")
            
            # 检查是否是数据采集进程，需要特殊处理
            if process_name in ["modbus_collector_设备1", "opcua_collector_设备2", "melsoft_collector_plc设备"]:
                # 查找数据采集后端目录
                backend_path = os.path.join(os.path.dirname(os.getcwd()), "project-data-acquisition")
                self.logger.info(f"尝试路径1: {backend_path}")
                if os.path.exists(backend_path):
                    cwd = backend_path
                    self.logger.info(f"使用数据采集目录: {cwd}")
                else:
                    # 尝试其他可能的路径
                    alt_path = os.path.join(os.getcwd(), "project-data-acquisition")
                    self.logger.info(f"尝试路径2: {alt_path}")
                    if os.path.exists(alt_path):
                        cwd = os.path.abspath(alt_path)
                        self.logger.info(f"使用数据采集目录: {cwd}")
                    else:
                        self.logger.warning(f"数据采集后端目录未找到，使用当前目录: {cwd}")
            
            # 设置环境变量
            env = os.environ.copy()
            
            # 检查并设置Python模块路径
            python_path_list = [cwd]
            
            # 添加用户的site-packages路径
            import site
            user_site = site.getusersitepackages()
            self.logger.info(f"检查用户site-packages: {user_site}")
            if user_site and os.path.exists(user_site):
                python_path_list.append(user_site)
                self.logger.info(f"添加用户site-packages: {user_site}")
            else:
                # 强制添加标准用户路径
                user_home = os.path.expanduser("~")
                fallback_user_site = os.path.join(user_home, ".local", "lib", "python3.10", "site-packages")
                if os.path.exists(fallback_user_site):
                    python_path_list.append(fallback_user_site)
                    self.logger.info(f"强制添加用户site-packages: {fallback_user_site}")
            
            # 添加系统site-packages路径
            for path in site.getsitepackages():
                if os.path.exists(path):
                    python_path_list.append(path)
                    self.logger.info(f"添加系统site-packages: {path}")
            
            # 如果原来有PYTHONPATH，也要保留
            if "PYTHONPATH" in env:
                existing_paths = env["PYTHONPATH"].split(os.pathsep)
                python_path_list.extend(existing_paths)
            
            env["PYTHONPATH"] = os.pathsep.join(python_path_list)
            
            # 创建单个进程启动命令，而不是启动所有进程
            command = self._create_single_process_command(process_name, process_info)
            
            self.logger.info(f"设置PYTHONPATH: {env['PYTHONPATH']}")
            self.logger.info(f"启动命令: {' '.join(command)}")
            
            # 启动子进程
            proc = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=cwd,
                env=env,
                bufsize=1,
                universal_newlines=True
            )
            
            self.logger.info(f"子进程已启动，PID: {proc.pid}")
            
            # 等待一段时间检查进程是否成功启动
            time.sleep(2)
            
            if proc.poll() is None:  # 进程仍在运行
                self.subprocesses[process_name] = proc
                process_info.pid = proc.pid
                process_info.status = ProcessState.RUNNING
                process_info.start_time = datetime.now()
                
                # 通知状态变化
                self._notify_process_status_change(process_name, process_info)
                
                self.logger.info(f"进程 {process_name} 启动成功, PID: {proc.pid}")
                return True
            else:
                # 进程启动失败
                stdout, stderr = proc.communicate()
                error_msg = stderr or stdout or "未知错误"
                process_info.status = ProcessState.ERROR
                process_info.last_error = error_msg[:1000]  # 限制错误信息长度
                
                self.logger.error(f"进程 {process_name} 启动失败")
                self.logger.error(f"返回码: {proc.returncode}")
                self.logger.error(f"标准输出: {stdout}")
                self.logger.error(f"标准错误: {stderr}")
                
                # 通知状态变化
                self._notify_process_status_change(process_name, process_info)
                
                self.logger.error(f"进程 {process_name} 启动失败: {error_msg}")
                return False
        
        except Exception as e:
            process_info.status = ProcessState.ERROR
            process_info.last_error = str(e)
            
            # 通知状态变化
            self._notify_process_status_change(process_name, process_info)
            
            self.logger.error(f"启动进程 {process_name} 时发生异常: {e}")
            return False

    def _create_single_process_command(self, process_name: str, process_info: EnhancedProcessInfo) -> List[str]:
        """创建单个进程启动命令，避免启动所有进程"""
        try:
            # 根据进程类型创建特定的启动命令
            if process_name == "modbus_collector_设备1":
                return [
                    "python", "-c",
                    f"""
import sys
import os
sys.path.insert(0, os.getcwd())

from apps.collector.modbustcp_influx import ModbustcpInflux
import json

# 加载配置文件
config_path = '{process_info.config_file}'
if os.path.exists(config_path):
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
else:
    # 使用默认配置
    config = {{
        "device_ip": "192.168.1.100",
        "device_port": 502,
        "protocol": "modbus"
    }}

# 启动单个Modbus采集器
collector = ModbustcpInflux(config)
collector.modbustcp_influx()
"""
                ]
            elif process_name == "opcua_collector_设备2":
                return [
                    "python", "-c",
                    f"""
import sys
import os
sys.path.insert(0, os.getcwd())

from apps.collector.opcua_influx import OpcuaInflux
import json

# 加载配置文件
config_path = '{process_info.config_file}'
if os.path.exists(config_path):
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
else:
    # 使用默认配置
    config = {{
        "device_ip": "192.168.1.101",
        "device_port": 4840,
        "protocol": "opcua"
    }}

# 启动单个OPC UA采集器
collector = OpcuaInflux(config)
collector.start_collector()
"""
                ]
            elif process_name == "melsoft_collector_plc设备":
                return [
                    "python", "-c",
                    f"""
import sys
import os
sys.path.insert(0, os.getcwd())

from apps.collector.melseca1enet_influx import MelsecA1ENetInflux
import json

# 加载配置文件
config_path = '{process_info.config_file}'
if os.path.exists(config_path):
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
else:
    # 使用默认配置
    config = {{
        "device_ip": "192.168.1.102",
        "device_port": 5007,
        "protocol": "melsoft"
    }}

# 启动单个Melsoft采集器
collector = MelsecA1ENetInflux(config)
collector.melseca1enet_influx()
"""
                ]
            else:
                # 对于其他进程，使用原始命令
                return process_info.command
                
        except Exception as e:
            self.logger.error(f"创建进程命令失败: {e}")
            # 返回原始命令作为后备
            return process_info.command
    
    def stop_process(self, process_name: str) -> bool:
        """停止指定进程"""
        if process_name not in self.processes:
            return False
        
        process_info = self.processes[process_name]
        
        if process_info.status != ProcessState.RUNNING:
            process_info.status = ProcessState.STOPPED
            self._notify_process_status_change(process_name, process_info)
            return True
        
        try:
            process_info.status = ProcessState.STOPPING
            self._notify_process_status_change(process_name, process_info)
            
            if process_name in self.subprocesses:
                proc = self.subprocesses[process_name]
                
                # 优雅停止
                proc.terminate()
                
                # 等待进程结束，最多等待10秒
                try:
                    proc.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    # 强制杀死
                    proc.kill()
                    proc.wait()
                
                del self.subprocesses[process_name]
            
            process_info.status = ProcessState.STOPPED
            process_info.pid = None
            process_info.start_time = None
            
            # 通知状态变化
            self._notify_process_status_change(process_name, process_info)
            
            self.logger.info(f"进程 {process_name} 已停止")
            return True
        
        except Exception as e:
            self.logger.error(f"停止进程 {process_name} 时发生异常: {e}")
            return False
    
    def restart_process(self, process_name: str) -> bool:
        """重启指定进程"""
        self.stop_process(process_name)
        time.sleep(2)  # 等待2秒确保进程完全停止
        
        if process_name in self.processes:
            self.processes[process_name].restart_count += 1
        
        return self.start_process(process_name)
    
    def get_process_status(self, process_name: str) -> Optional[Dict[str, Any]]:
        """获取进程状态"""
        if process_name not in self.processes:
            return None
        
        process_info = self.processes[process_name]
        return {
            "pid": process_info.pid,
            "name": process_info.name,
            "type": process_info.type,
            "status": process_info.status.value,
            "cpu_percent": process_info.cpu_percent,
            "memory_mb": process_info.memory_mb,
            "memory_percent": process_info.memory_percent,
            "start_time": process_info.start_time.isoformat() if process_info.start_time else None,
            "restart_count": process_info.restart_count,
            "last_error": process_info.last_error,
            "config_file": process_info.config_file,
            "description": process_info.description
        }
    
    def get_all_processes(self) -> Dict[str, Dict[str, Any]]:
        """获取所有进程状态"""
        result = {}
        for name, process_info in self.processes.items():
            # 计算运行时间
            uptime_seconds = 0
            if process_info.start_time:
                uptime_seconds = int((datetime.now() - process_info.start_time).total_seconds())
            
            result[name] = {
                "pid": process_info.pid,
                "name": process_info.name,
                "type": process_info.type,
                "status": process_info.status.value,
                "cpu_percent": process_info.cpu_percent,
                "memory_mb": process_info.memory_mb,
                "memory_percent": process_info.memory_percent,
                "start_time": process_info.start_time.isoformat() if process_info.start_time else None,
                "uptime_seconds": uptime_seconds,
                "uptime_formatted": self._format_uptime(uptime_seconds),
                "restart_count": process_info.restart_count,
                "last_error": process_info.last_error,
                "config_file": process_info.config_file,
                "description": process_info.description,
                # Enhanced monitoring fields
                "health_score": process_info.health_score,
                "last_heartbeat": process_info.last_heartbeat.isoformat() if process_info.last_heartbeat else None,
                "error_count_24h": process_info.error_count_24h,
                "data_collection_rate": process_info.data_collection_rate,
                "last_data_time": process_info.last_data_time.isoformat() if process_info.last_data_time else None,
                "connection_status": process_info.connection_info.status.value if process_info.connection_info else "unknown",
                "connection_ip": process_info.connection_info.device_ip if process_info.connection_info else None,
                "connection_port": process_info.connection_info.device_port if process_info.connection_info else None,
                "is_connected": process_info.connection_info.is_connected if process_info.connection_info else False
            }
        return result
    
    def get_process_logs(self, process_name: str, lines: int = 100) -> List[str]:
        """获取进程日志"""
        # 这里可以实现读取进程日志文件的逻辑
        # 目前返回模拟数据
        return [
            f"2024-01-15 14:30:00 INFO: 进程 {process_name} 启动",
            f"2024-01-15 14:30:01 INFO: 正在连接设备...",
            f"2024-01-15 14:30:02 INFO: 设备连接成功",
            f"2024-01-15 14:30:03 INFO: 开始数据采集",
            f"2024-01-15 14:30:04 INFO: 数据采集正常运行"
        ]
    
    def start_monitoring(self):
        """启动进程监控"""
        if self.monitoring_active:
            return
        
        self.monitoring_active = True
        self.monitoring_thread = threading.Thread(target=self._monitor_processes, daemon=True)
        self.monitoring_thread.start()
        self.logger.info("进程监控已启动")
    
    def stop_monitoring(self):
        """停止进程监控"""
        self.monitoring_active = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=5)
        self.logger.info("进程监控已停止")
    
    def _monitor_processes(self):
        """监控进程状态"""
        while self.monitoring_active:
            try:
                # 扫描系统中的进程，检测与配置匹配的进程
                self._scan_existing_processes()
                
                for process_name, process_info in self.processes.items():
                    if process_info.status == ProcessState.RUNNING:
                        self._update_process_stats(process_name, process_info)
                        self._check_process_health(process_name, process_info)
                        
                        # 如果有连接信息，注册连接监控
                        if process_info.connection_info and process_info.connection_info.device_ip and process_info.connection_info.device_port:
                            self._register_connection_monitoring(process_name, process_info)
                
                # 定期推送进程状态
                self._broadcast_process_status()
                
                time.sleep(5)  # 每5秒检查一次
                
            except Exception as e:
                self.logger.error(f"监控进程时发生异常: {e}")
                time.sleep(5)
                
    def _register_connection_monitoring(self, process_name: str, process_info: EnhancedProcessInfo):
        """注册连接监控"""
        try:
            # 检查是否已注册
            if not connection_monitor.get_connection_status(process_name):
                # 注册连接监控
                connection_monitor.register_connection(process_name, process_info.connection_info)
                self.logger.info(f"注册连接监控: {process_name} -> {process_info.connection_info.device_ip}:{process_info.connection_info.device_port}")
        except Exception as e:
            self.logger.error(f"注册连接监控失败: {e}")
    
    def _check_connection_status(self, process_name: str, process_info: EnhancedProcessInfo):
        """检查连接状态"""
        try:
            # 检查连接状态
            result = connection_monitor.check_connection(process_name)
            
            # 更新连接信息
            if process_info.connection_info:
                process_info.connection_info.is_connected = result.success
                process_info.connection_info.status = result.status
                
                if result.success:
                    process_info.connection_info.last_connect_time = datetime.now()
                else:
                    process_info.connection_info.connection_errors += 1
                
                # 存储连接状态到数据库
                self._store_connection_status(process_name, process_info.connection_info)
                
                self.logger.debug(f"进程 {process_name} 连接状态: {result.status.value}")
        except Exception as e:
            self.logger.error(f"检查连接状态失败: {e}")
    
    def _store_connection_status(self, process_name: str, connection_info: ConnectionInfo):
        """存储连接状态到数据库"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO connection_status 
                (process_name, device_ip, device_port, is_connected, last_connect_time, 
                connection_errors, protocol_type, status, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                process_name,
                connection_info.device_ip,
                connection_info.device_port,
                1 if connection_info.is_connected else 0,
                connection_info.last_connect_time.isoformat() if connection_info.last_connect_time else None,
                connection_info.connection_errors,
                connection_info.protocol_type,
                connection_info.status.value,
                datetime.now().isoformat()
            ))
            
            conn.commit()
            conn.close()
        except Exception as e:
            self.logger.error(f"存储连接状态失败: {e}")
    
    def update_connection_status(self, process_name: str, status: ConnectionStatus, device_ip: Optional[str] = None, device_port: Optional[int] = None):
        """更新连接状态"""
        if process_name not in self.processes:
            return False
        
        process_info = self.processes[process_name]
        
        # 如果没有连接信息，创建一个
        if not process_info.connection_info:
            process_info.connection_info = ConnectionInfo(
                device_ip=device_ip,
                device_port=device_port,
                protocol_type=process_info.type
            )
        
        # 更新连接状态
        process_info.connection_info.status = status
        process_info.connection_info.is_connected = (status == ConnectionStatus.CONNECTED)
        
        if status == ConnectionStatus.CONNECTED:
            process_info.connection_info.last_connect_time = datetime.now()
        
        # 如果提供了IP和端口，更新它们
        if device_ip:
            process_info.connection_info.device_ip = device_ip
        if device_port:
            process_info.connection_info.device_port = device_port
        
        # 存储连接状态到数据库
        self._store_connection_status(process_name, process_info.connection_info)
        
        # 通知状态变化
        self._notify_process_status_change(process_name, process_info)
        
        return True
    
    def get_connection_status(self, process_name: str) -> Optional[Dict[str, Any]]:
        """获取连接状态"""
        if process_name not in self.processes:
            return None
        
        process_info = self.processes[process_name]
        
        if not process_info.connection_info:
            return {
                "status": "unknown",
                "is_connected": False,
                "device_ip": None,
                "device_port": None,
                "protocol_type": None,
                "last_connect_time": None,
                "connection_errors": 0
            }
        
        return {
            "status": process_info.connection_info.status.value,
            "is_connected": process_info.connection_info.is_connected,
            "device_ip": process_info.connection_info.device_ip,
            "device_port": process_info.connection_info.device_port,
            "protocol_type": process_info.connection_info.protocol_type,
            "last_connect_time": process_info.connection_info.last_connect_time.isoformat() if process_info.connection_info.last_connect_time else None,
            "connection_errors": process_info.connection_info.connection_errors
        }
    
    def get_connection_history(self, process_name: str, limit: int = 10) -> List[Dict[str, Any]]:
        """获取连接历史记录"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM connection_status
                WHERE process_name = ?
                ORDER BY timestamp DESC
                LIMIT ?
            ''', (process_name, limit))
            
            rows = cursor.fetchall()
            conn.close()
            
            return [dict(row) for row in rows]
        except Exception as e:
            self.logger.error(f"获取连接历史记录失败: {e}")
            return []
            
    # 数据采集性能监控相关方法
    def update_process_data_collection_rate(self, process_name: str, data_points_per_minute: float) -> bool:
        """更新进程数据采集速率"""
        if process_name not in self.processes:
            return False
            
        process_info = self.processes[process_name]
        process_info.data_collection_rate = data_points_per_minute
        
        # 更新最后数据时间
        process_info.last_data_time = datetime.now()
        
        # 注册并更新数据采集监控
        data_acquisition_monitor.register_process(process_name)
        data_acquisition_monitor.update_data_point(
            process_name=process_name,
            data_points=int(data_points_per_minute / 60),  # 转换为每秒数据点数
            errors=0,
            response_time_ms=0.0
        )
        
        # 通知状态变化
        self._notify_process_status_change(process_name, process_info)
        
        self.logger.debug(f"更新进程 {process_name} 数据采集速率: {data_points_per_minute} 点/分钟")
        return True
    
    def update_process_data_point(self, process_name: str, data_points: int = 1, errors: int = 0, response_time_ms: float = 0.0) -> bool:
        """更新进程数据点信息"""
        if process_name not in self.processes:
            return False
            
        process_info = self.processes[process_name]
        
        # 更新最后数据时间
        process_info.last_data_time = datetime.now()
        
        # 注册并更新数据采集监控
        data_acquisition_monitor.register_process(process_name)
        data_acquisition_monitor.update_data_point(
            process_name=process_name,
            data_points=data_points,
            errors=errors,
            response_time_ms=response_time_ms
        )
        
        # 获取更新后的数据流状态
        status = data_acquisition_monitor.get_data_flow_status(process_name)
        if status:
            process_info.data_collection_rate = status["data_points_per_minute"]
            
            # 更新健康评分
            process_info.health_score = max(0, min(100, process_info.health_score * 0.7 + status["data_quality_score"] * 0.3))
            
            # 如果有错误，增加错误计数
            if errors > 0:
                process_info.error_count_24h += errors
        
        # 通知状态变化
        self._notify_process_status_change(process_name, process_info)
        
        return True
    
    def increment_process_error_count(self, process_name: str, error_message: str = None) -> bool:
        """增加进程错误计数"""
        if process_name not in self.processes:
            return False
            
        process_info = self.processes[process_name]
        process_info.error_count_24h += 1
        
        if error_message:
            process_info.last_error = error_message
            
        # 降低健康评分
        process_info.health_score = max(0, process_info.health_score - 5)
        
        # 通知状态变化
        self._notify_process_status_change(process_name, process_info)
        
        self.logger.warning(f"进程 {process_name} 错误计数增加: {process_info.error_count_24h}")
        return True
    
    def get_process_statistics(self, process_name: str) -> Dict[str, Any]:
        """获取进程统计信息"""
        if process_name not in self.processes:
            return {"error": "进程不存在"}
            
        process_info = self.processes[process_name]
        
        # 计算运行时间
        uptime_seconds = 0
        if process_info.start_time:
            uptime_seconds = int((datetime.now() - process_info.start_time).total_seconds())
        
        # 获取数据流状态
        data_flow_status = data_acquisition_monitor.get_data_flow_status(process_name)
        
        # 获取连接状态
        connection_status = self.get_connection_status(process_name)
        
        return {
            "name": process_info.name,
            "type": process_info.type,
            "status": process_info.status.value,
            "pid": process_info.pid,
            "cpu_percent": process_info.cpu_percent,
            "memory_mb": process_info.memory_mb,
            "memory_percent": process_info.memory_percent,
            "start_time": process_info.start_time.isoformat() if process_info.start_time else None,
            "uptime_seconds": uptime_seconds,
            "uptime_formatted": self._format_uptime(uptime_seconds),
            "restart_count": process_info.restart_count,
            "last_error": process_info.last_error,
            "health_score": process_info.health_score,
            "error_count_24h": process_info.error_count_24h,
            "data_collection_rate": process_info.data_collection_rate,
            "last_data_time": process_info.last_data_time.isoformat() if process_info.last_data_time else None,
            "connection_status": connection_status["status"] if connection_status else "unknown",
            "is_connected": connection_status["is_connected"] if connection_status else False,
            "data_flow": data_flow_status if data_flow_status else {
                "status": "unknown",
                "data_points_per_minute": 0.0,
                "error_rate": 0.0,
                "data_quality_score": 0.0
            }
        }
    
    def get_all_process_statistics(self) -> Dict[str, Any]:
        """获取所有进程统计信息"""
        result = {
            "processes": {},
            "summary": {
                "total_processes": len(self.processes),
                "running_processes": 0,
                "stopped_processes": 0,
                "error_processes": 0,
                "crashed_processes": 0,
                "total_cpu_percent": 0.0,
                "total_memory_mb": 0.0,
                "average_health_score": 0.0,
                "total_data_points_per_minute": 0.0,
                "total_errors_24h": 0
            }
        }
        
        # 收集每个进程的统计信息
        for process_name in self.processes:
            stats = self.get_process_statistics(process_name)
            result["processes"][process_name] = stats
            
            # 更新汇总信息
            if stats["status"] == ProcessState.RUNNING.value:
                result["summary"]["running_processes"] += 1
                result["summary"]["total_cpu_percent"] += stats["cpu_percent"]
                result["summary"]["total_memory_mb"] += stats["memory_mb"]
            elif stats["status"] == ProcessState.STOPPED.value:
                result["summary"]["stopped_processes"] += 1
            elif stats["status"] == ProcessState.ERROR.value:
                result["summary"]["error_processes"] += 1
            elif stats["status"] == ProcessState.CRASHED.value:
                result["summary"]["crashed_processes"] += 1
                
            result["summary"]["average_health_score"] += stats["health_score"]
            result["summary"]["total_data_points_per_minute"] += stats.get("data_collection_rate", 0)
            result["summary"]["total_errors_24h"] += stats["error_count_24h"]
        
        # 计算平均健康评分
        if len(self.processes) > 0:
            result["summary"]["average_health_score"] /= len(self.processes)
            
        # 获取所有未解决的告警
        result["alerts"] = data_acquisition_monitor.get_all_alerts(include_resolved=False)
            
        return result
    
    def get_process_health_report(self, process_name: str) -> Optional[Dict[str, Any]]:
        """获取进程健康报告"""
        if process_name not in self.processes:
            return None
            
        process_info = self.processes[process_name]
        
        # 获取数据流状态
        data_flow_status = data_acquisition_monitor.get_data_flow_status(process_name)
        
        # 获取连接状态
        connection_status = self.get_connection_status(process_name)
        
        # 获取告警
        alerts = data_acquisition_monitor.get_alerts(process_name, limit=5)
        
        # 计算总体状态
        overall_status = HealthStatus.HEALTHY
        if process_info.status in [ProcessState.ERROR, ProcessState.CRASHED]:
            overall_status = HealthStatus.CRITICAL
        elif process_info.health_score < 60:
            overall_status = HealthStatus.CRITICAL
        elif process_info.health_score < 80:
            overall_status = HealthStatus.WARNING
        elif data_flow_status and data_flow_status["status"] in ["warning", "critical"]:
            overall_status = HealthStatus(data_flow_status["status"])
        elif connection_status and not connection_status["is_connected"]:
            overall_status = HealthStatus.WARNING
            
        # 创建健康检查项目
        health_checks = [
            {
                "check": "进程状态",
                "status": "healthy" if process_info.status == ProcessState.RUNNING else "critical",
                "score": 100 if process_info.status == ProcessState.RUNNING else 0,
                "details": f"进程当前状态: {process_info.status.value}"
            },
            {
                "check": "资源使用",
                "status": "healthy" if process_info.cpu_percent < 80 else "warning",
                "score": 100 - min(100, process_info.cpu_percent),
                "details": f"CPU: {process_info.cpu_percent}%, 内存: {process_info.memory_mb}MB"
            }
        ]
        
        # 添加连接状态检查
        if connection_status:
            health_checks.append({
                "check": "连接状态",
                "status": "healthy" if connection_status["is_connected"] else "warning",
                "score": 100 if connection_status["is_connected"] else 50,
                "details": f"连接状态: {connection_status['status']}"
            })
            
        # 添加数据流状态检查
        if data_flow_status:
            health_checks.append({
                "check": "数据流状态",
                "status": data_flow_status["status"],
                "score": data_flow_status["data_quality_score"],
                "details": f"数据点/分钟: {data_flow_status['data_points_per_minute']}, 错误率: {data_flow_status['error_rate']:.1%}"
            })
            
        # 生成建议
        recommendations = []
        if process_info.status in [ProcessState.ERROR, ProcessState.CRASHED]:
            recommendations.append("重启进程")
        if connection_status and not connection_status["is_connected"]:
            recommendations.append("检查网络连接")
        if data_flow_status and data_flow_status["error_rate"] > 0.05:
            recommendations.append("检查数据采集配置")
        if process_info.error_count_24h > 10:
            recommendations.append("检查错误日志")
            
        return {
            "process_name": process_name,
            "timestamp": datetime.now().isoformat(),
            "overall_score": process_info.health_score,
            "overall_status": overall_status.value,
            "health_checks": health_checks,
            "recommendations": recommendations,
            "alerts": alerts
        }
    
    def get_process_performance_history(self, process_name: str, hours: int = 24) -> List[Dict[str, Any]]:
        """获取进程性能历史数据"""
        # 获取数据流历史记录
        return data_acquisition_monitor.get_data_flow_history(process_name, hours=hours)
    
    def check_process_heartbeat(self, process_name: str) -> bool:
        """检查进程心跳"""
        if process_name not in self.processes:
            return False
            
        process_info = self.processes[process_name]
        
        # 如果进程不在运行状态，返回False
        if process_info.status != ProcessState.RUNNING:
            return False
            
        # 更新心跳时间
        process_info.last_heartbeat = datetime.now()
        
        # 检查进程是否存在
        if process_info.pid and psutil.pid_exists(process_info.pid):
            try:
                # 检查进程是否响应
                proc = psutil.Process(process_info.pid)
                if proc.status() in [psutil.STATUS_RUNNING, psutil.STATUS_SLEEPING]:
                    return True
            except:
                pass
                
        return False
    
    def _scan_existing_processes(self):
        """扫描系统中的进程，检测与配置匹配的进程"""
        try:
            for process_name, process_info in self.processes.items():
                if process_info.status == ProcessState.RUNNING:
                    continue  # 已经在运行，跳过
                    
                # 根据进程名称和命令行参数匹配进程
                for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                    try:
                        cmdline = proc.info['cmdline']
                        if not cmdline:
                            continue
                            
                        # 对于海天注塑机数采进程，检查是否包含 run.py 和 config_haitian_test.json
                        if process_name == "haitian_data_collector":
                            if any("run.py" in arg for arg in cmdline) and any("config_haitian_test.json" in arg for arg in cmdline):
                                process_info.pid = proc.info['pid']
                                process_info.status = ProcessState.RUNNING
                                process_info.start_time = datetime.fromtimestamp(proc.create_time())
                                self.logger.info(f"检测到运行中的进程: {process_name} (PID: {process_info.pid})")
                                break
                        # 对于其他进程，可以根据命令行参数匹配
                        elif process_info.command:
                            if all(cmd_part in " ".join(cmdline) for cmd_part in process_info.command):
                                process_info.pid = proc.info['pid']
                                process_info.status = ProcessState.RUNNING
                                process_info.start_time = datetime.fromtimestamp(proc.create_time())
                                self.logger.info(f"检测到运行中的进程: {process_name} (PID: {process_info.pid})")
                                break
                                
                    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                        continue
                        
        except Exception as e:
            self.logger.error(f"扫描进程时发生异常: {e}")

    def _update_process_stats(self, process_name: str, process_info: EnhancedProcessInfo):
        """更新进程资源使用统计"""
        try:
            if process_info.pid:
                proc = psutil.Process(process_info.pid)
                
                # 优化CPU使用率检查 - 减少检查频率
                current_time = time.time()
                if not hasattr(process_info, '_last_cpu_check') or (current_time - getattr(process_info, '_last_cpu_check', 0)) > 10:
                    # 每10秒才检查一次CPU使用率
                    cpu_percent = proc.cpu_percent(interval=0.1)  # 减少等待时间
                    process_info.cpu_percent = round(cpu_percent, 2)
                    process_info._last_cpu_check = current_time
                
                # 获取内存使用情况
                memory_info = proc.memory_info()
                process_info.memory_mb = round(memory_info.rss / 1024 / 1024, 2)
                process_info.memory_percent = round(proc.memory_percent(), 2)
                
                # 更新运行时间
                if process_info.start_time:
                    process_info.uptime_seconds = int((datetime.now() - process_info.start_time).total_seconds())
                
                # 更新最后心跳时间
                process_info.last_heartbeat = datetime.now()
                
                # 减少数据库存储频率 - 只在重要变化时存储
                if not hasattr(process_info, '_last_db_store') or (current_time - getattr(process_info, '_last_db_store', 0)) > 30:
                    # 每30秒才存储一次到数据库
                    metrics = PerformanceMetrics(
                        process_name=process_name,
                        timestamp=datetime.now(),
                        cpu_percent=process_info.cpu_percent,
                        memory_mb=process_info.memory_mb,
                        data_points_per_minute=process_info.data_collection_rate,
                        error_rate=0.0,
                        response_time_ms=0.0
                    )
                    self._store_performance_metrics(metrics)
                    self._store_process_status(process_name, process_info)
                    process_info._last_db_store = current_time
                
                self.logger.debug(f"进程 {process_name} 状态更新: CPU={process_info.cpu_percent}%, 内存={process_info.memory_mb}MB")
                
        except (psutil.NoProcess, psutil.AccessDenied) as e:
            # 进程不存在或无权限访问
            self.logger.warning(f"无法访问进程 {process_name} (PID: {process_info.pid}): {e}")
            self._handle_process_crashed(process_name, process_info)
        except Exception as e:
            self.logger.error(f"更新进程 {process_name} 统计信息时发生异常: {e}")

    def _check_process_health(self, process_name: str, process_info: EnhancedProcessInfo):
        """检查进程健康状态"""
        try:
            health_score = 100.0
            health_issues = []
            
            # 检查进程是否存在
            if process_name in self.subprocesses:
                proc = self.subprocesses[process_name]
                if proc.poll() is not None:
                    # 进程已退出
                    self._handle_process_crashed(process_name, process_info)
                    return
            
            # 检查进程是否响应（通过PID检查）
            if process_info.pid:
                try:
                    proc = psutil.Process(process_info.pid)
                    if not proc.is_running():
                        health_score -= 50
                        health_issues.append("进程未运行")
                        self._handle_process_crashed(process_name, process_info)
                        return
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    health_score -= 50
                    health_issues.append("进程不存在或无权限访问")
                    self._handle_process_crashed(process_name, process_info)
                    return
            
            # 检查CPU使用率
            if process_info.cpu_percent > 80:
                health_score -= 20
                health_issues.append(f"CPU使用率过高: {process_info.cpu_percent}%")
            elif process_info.cpu_percent > 60:
                health_score -= 10
                health_issues.append(f"CPU使用率较高: {process_info.cpu_percent}%")
            
            # 检查内存使用率
            if process_info.memory_mb > 1000:  # 超过1GB
                health_score -= 20
                health_issues.append(f"内存使用过高: {process_info.memory_mb}MB")
            elif process_info.memory_mb > 500:  # 超过500MB
                health_score -= 10
                health_issues.append(f"内存使用较高: {process_info.memory_mb}MB")
            
            # 检查心跳时间
            if process_info.last_heartbeat:
                time_since_heartbeat = (datetime.now() - process_info.last_heartbeat).total_seconds()
                if time_since_heartbeat > 60:  # 超过1分钟没有心跳
                    health_score -= 30
                    health_issues.append(f"心跳超时: {time_since_heartbeat:.0f}秒")
                elif time_since_heartbeat > 30:  # 超过30秒没有心跳
                    health_score -= 15
                    health_issues.append(f"心跳延迟: {time_since_heartbeat:.0f}秒")
            
            # 检查重启次数
            if process_info.restart_count > 3:
                health_score -= 25
                health_issues.append(f"重启次数过多: {process_info.restart_count}次")
            elif process_info.restart_count > 1:
                health_score -= 10
                health_issues.append(f"有重启记录: {process_info.restart_count}次")
                
            # 检查连接状态
            if process_info.connection_info:
                # 检查连接状态
                self._check_connection_status(process_name, process_info)
                
                if process_info.connection_info.status == ConnectionStatus.ERROR:
                    health_score -= 30
                    health_issues.append("设备连接错误")
                elif process_info.connection_info.status == ConnectionStatus.DISCONNECTED:
                    health_score -= 20
                    health_issues.append("设备连接断开")
                elif process_info.connection_info.status == ConnectionStatus.UNKNOWN:
                    health_score -= 10
                    health_issues.append("设备连接状态未知")
                
                # 检查连接错误次数
                if process_info.connection_info.connection_errors > 5:
                    health_score -= 20
                    health_issues.append(f"连接错误次数过多: {process_info.connection_info.connection_errors}次")
                elif process_info.connection_info.connection_errors > 2:
                    health_score -= 10
                    health_issues.append(f"有连接错误记录: {process_info.connection_info.connection_errors}次")
            
            # 检查错误计数
            if process_info.error_count_24h > 10:
                health_score -= 20
                health_issues.append(f"24小时内错误过多: {process_info.error_count_24h}次")
            elif process_info.error_count_24h > 5:
                health_score -= 10
                health_issues.append(f"24小时内有错误: {process_info.error_count_24h}次")
            
            # 更新健康分数
            process_info.health_score = max(health_score, 0.0)
            
            # 记录健康问题
            if health_issues:
                self.logger.debug(f"进程 {process_name} 健康问题: {', '.join(health_issues)}")
                
        except Exception as e:
            self.logger.error(f"检查进程 {process_name} 健康状态时发生异常: {e}")
            process_info.health_score = 0.0

    def _handle_process_crashed(self, process_name: str, process_info: EnhancedProcessInfo):
        """处理进程崩溃"""
        self.logger.warning(f"检测到进程 {process_name} 崩溃")
        
        process_info.status = ProcessState.CRASHED
        process_info.pid = None
        process_info.health_score = 0.0
        process_info.error_count_24h += 1
        
        # 清理子进程引用
        if process_name in self.subprocesses:
            del self.subprocesses[process_name]
        
        # 通知状态变化
        self._notify_process_status_change(process_name, process_info)
        
        # 自动重启逻辑
        if process_info.auto_restart and process_info.restart_count < process_info.max_restarts:
            self.logger.info(f"尝试自动重启进程 {process_name} (第{process_info.restart_count + 1}次)")
            time.sleep(5)  # 等待5秒后重启
            self.restart_process(process_name)
        else:
            self.logger.error(f"进程 {process_name} 达到最大重启次数或禁用自动重启")

    def _notify_process_status_change(self, process_name: str, process_info: EnhancedProcessInfo):
        """通知进程状态变化"""
        try:
            if self.websocket_manager:
                # 在新线程中运行异步代码
                import concurrent.futures
                
                def run_async():
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    try:
                        loop.run_until_complete(self.websocket_manager.broadcast_message({
                            "type": "process_status_update",
                            "data": {
                                "process_name": process_name,
                                "status": process_info.status.value,
                                "pid": process_info.pid,
                                "cpu_percent": process_info.cpu_percent,
                                "memory_mb": process_info.memory_mb,
                                "health_score": process_info.health_score,
                                "timestamp": datetime.now().isoformat()
                            }
                        }))
                    finally:
                        loop.close()
                
                # 使用线程池执行异步任务
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    executor.submit(run_async)
                    
        except Exception as e:
            self.logger.error(f"通知进程状态变化失败: {e}")

    def _broadcast_process_status(self):
        """广播进程状态"""
        try:
            if self.websocket_manager:
                # 在新线程中运行异步代码
                import concurrent.futures
                
                def run_async():
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    try:
                        all_processes = self.get_all_processes()
                        loop.run_until_complete(self.websocket_manager.broadcast_message({
                            "type": "all_processes_status",
                            "data": {
                                "processes": all_processes,
                                "timestamp": datetime.now().isoformat()
                            }
                        }))
                    finally:
                        loop.close()
                
                # 使用线程池执行异步任务
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    executor.submit(run_async)
                    
        except Exception as e:
            self.logger.error(f"广播进程状态失败: {e}")

    def _store_process_status(self, process_name: str, process_info: EnhancedProcessInfo):
        """存储进程状态到数据库"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO process_status (
                    process_name, status, pid, cpu_percent, memory_mb,
                    start_time, last_heartbeat, connection_status,
                    data_collection_rate, last_data_time, health_score,
                    error_count_24h, restart_count, last_error, timestamp
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                process_name,
                process_info.status.value,
                process_info.pid,
                process_info.cpu_percent,
                process_info.memory_mb,
                process_info.start_time.isoformat() if process_info.start_time else None,
                process_info.last_heartbeat.isoformat() if process_info.last_heartbeat else None,
                process_info.connection_info.status.value if process_info.connection_info else "unknown",
                process_info.data_collection_rate,
                process_info.last_data_time.isoformat() if process_info.last_data_time else None,
                process_info.health_score,
                process_info.error_count_24h,
                process_info.restart_count,
                process_info.last_error,
                datetime.now().isoformat()
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            self.logger.error(f"存储进程状态失败: {e}")

    def _store_performance_metrics(self, metrics: PerformanceMetrics):
        """存储性能指标到数据库"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO performance_metrics (
                    process_name, timestamp, cpu_percent, memory_mb,
                    data_points_per_minute, error_rate, response_time_ms
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                metrics.process_name,
                metrics.timestamp.isoformat(),
                metrics.cpu_percent,
                metrics.memory_mb,
                metrics.data_points_per_minute,
                metrics.error_rate,
                metrics.response_time_ms
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            self.logger.error(f"存储性能指标失败: {e}")

    def get_process_performance_history(self, process_name: str, hours: int = 24) -> List[Dict[str, Any]]:
        """获取进程性能历史数据"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            start_time = datetime.now() - timedelta(hours=hours)
            
            cursor.execute('''
                SELECT timestamp, cpu_percent, memory_mb, data_points_per_minute, error_rate, response_time_ms
                FROM performance_metrics
                WHERE process_name = ? AND timestamp >= ?
                ORDER BY timestamp DESC
            ''', (process_name, start_time.isoformat()))
            
            results = []
            for row in cursor.fetchall():
                results.append({
                    "timestamp": row[0],
                    "cpu_percent": row[1],
                    "memory_mb": row[2],
                    "data_points_per_minute": row[3],
                    "error_rate": row[4],
                    "response_time_ms": row[5]
                })
            
            conn.close()
            return results
            
        except Exception as e:
            self.logger.error(f"获取进程性能历史数据失败: {e}")
            return []

    def get_process_health_score(self, process_name: str) -> float:
        """计算进程健康分数"""
        if process_name not in self.processes:
            return 0.0
        
        process_info = self.processes[process_name]
        health_score = 100.0
        
        # 进程状态检查
        if process_info.status != ProcessState.RUNNING:
            health_score -= 50
        
        # CPU使用率检查
        if process_info.cpu_percent > 80:
            health_score -= 20
        elif process_info.cpu_percent > 60:
            health_score -= 10
        
        # 内存使用检查
        if process_info.memory_mb > 1000:
            health_score -= 20
        elif process_info.memory_mb > 500:
            health_score -= 10
        
        # 重启次数检查
        if process_info.restart_count > 3:
            health_score -= 15
        elif process_info.restart_count > 1:
            health_score -= 5
        
        return max(health_score, 0.0)

    def check_process_heartbeat(self, process_name: str) -> bool:
        """检查进程心跳"""
        if process_name not in self.processes:
            return False
        
        process_info = self.processes[process_name]
        
        # 如果进程不在运行状态，心跳检查失败
        if process_info.status != ProcessState.RUNNING:
            return False
        
        # 检查最后心跳时间
        if process_info.last_heartbeat:
            time_since_heartbeat = (datetime.now() - process_info.last_heartbeat).total_seconds()
            return time_since_heartbeat <= 60  # 1分钟内有心跳认为正常
        
        return False

    async def get_real_time_metrics(self, process_name: str) -> AsyncGenerator[Dict[str, Any], None]:
        """获取实时进程指标流"""
        while self.monitoring_active and process_name in self.processes:
            process_info = self.processes[process_name]
            
            yield {
                "process_name": process_name,
                "timestamp": datetime.now().isoformat(),
                "status": process_info.status.value,
                "cpu_percent": process_info.cpu_percent,
                "memory_mb": process_info.memory_mb,
                "health_score": process_info.health_score,
                "data_collection_rate": process_info.data_collection_rate,
                "connection_status": process_info.connection_info.status.value if process_info.connection_info else "unknown"
            }
            
            await asyncio.sleep(1)  # 每秒更新一次

    def shutdown(self):
        """关闭进程管理器"""
        self.logger.info("正在关闭进程管理器...")
        
        # 停止监控
        self.stop_monitoring()
        
        # 停止所有进程
        for process_name in list(self.processes.keys()):
            self.stop_process(process_name)
        
        self.logger.info("进程管理器已关闭")

    def get_process_statistics(self, process_name: str) -> Dict[str, Any]:
        """获取进程统计信息"""
        if process_name not in self.processes:
            return {}
        
        process_info = self.processes[process_name]
        
        # 计算运行时间
        uptime_seconds = 0
        if process_info.start_time:
            uptime_seconds = int((datetime.now() - process_info.start_time).total_seconds())
        
        return {
            "name": process_info.name,
            "type": process_info.type,
            "status": process_info.status.value,
            "pid": process_info.pid,
            "cpu_percent": process_info.cpu_percent,
            "memory_mb": process_info.memory_mb,
            "memory_percent": process_info.memory_percent,
            "uptime_seconds": uptime_seconds,
            "uptime_formatted": self._format_uptime(uptime_seconds),
            "restart_count": process_info.restart_count,
            "health_score": process_info.health_score,
            "last_heartbeat": process_info.last_heartbeat.isoformat() if process_info.last_heartbeat else None,
            "last_error": process_info.last_error,
            "error_count_24h": process_info.error_count_24h,
            "data_collection_rate": process_info.data_collection_rate,
            "last_data_time": process_info.last_data_time.isoformat() if process_info.last_data_time else None,
            "connection_status": process_info.connection_info.status.value if process_info.connection_info else "unknown"
        }
    
    def _format_uptime(self, seconds: int) -> str:
        """格式化运行时间"""
        if seconds < 60:
            return f"{seconds}秒"
        elif seconds < 3600:
            minutes = seconds // 60
            return f"{minutes}分钟"
        elif seconds < 86400:
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            return f"{hours}小时{minutes}分钟"
        else:
            days = seconds // 86400
            hours = (seconds % 86400) // 3600
            return f"{days}天{hours}小时"
    
    def get_all_process_statistics(self) -> Dict[str, Any]:
        """获取所有进程的统计信息"""
        stats = {
            "processes": {},
            "summary": {
                "total_processes": len(self.processes),
                "running_processes": 0,
                "stopped_processes": 0,
                "error_processes": 0,
                "crashed_processes": 0,
                "total_cpu_percent": 0.0,
                "total_memory_mb": 0.0,
                "average_health_score": 0.0
            }
        }
        
        total_health_score = 0.0
        
        for process_name, process_info in self.processes.items():
            process_stats = self.get_process_statistics(process_name)
            stats["processes"][process_name] = process_stats
            
            # 更新汇总统计
            if process_info.status == ProcessState.RUNNING:
                stats["summary"]["running_processes"] += 1
                stats["summary"]["total_cpu_percent"] += process_info.cpu_percent
                stats["summary"]["total_memory_mb"] += process_info.memory_mb
            elif process_info.status == ProcessState.STOPPED:
                stats["summary"]["stopped_processes"] += 1
            elif process_info.status == ProcessState.ERROR:
                stats["summary"]["error_processes"] += 1
            elif process_info.status == ProcessState.CRASHED:
                stats["summary"]["crashed_processes"] += 1
            
            total_health_score += process_info.health_score
        
        # 计算平均健康分数
        if len(self.processes) > 0:
            stats["summary"]["average_health_score"] = round(total_health_score / len(self.processes), 2)
        
        return stats
    
    def update_process_data_collection_rate(self, process_name: str, rate: float):
        """更新进程数据采集速率"""
        if process_name in self.processes:
            self.processes[process_name].data_collection_rate = rate
            self.processes[process_name].last_data_time = datetime.now()
    
    def increment_process_error_count(self, process_name: str, error_message: str = None):
        """增加进程错误计数"""
        if process_name in self.processes:
            process_info = self.processes[process_name]
            process_info.error_count_24h += 1
            if error_message:
                process_info.last_error = error_message[:1000]  # 限制错误信息长度
    
    def reset_process_error_count(self, process_name: str):
        """重置进程错误计数"""
        if process_name in self.processes:
            self.processes[process_name].error_count_24h = 0
    
    def update_connection_status(self, process_name: str, status: ConnectionStatus, 
                               device_ip: str = None, device_port: int = None):
        """更新进程连接状态"""
        if process_name in self.processes:
            process_info = self.processes[process_name]
            if not process_info.connection_info:
                process_info.connection_info = ConnectionInfo()
            
            process_info.connection_info.status = status
            process_info.connection_info.is_connected = (status == ConnectionStatus.CONNECTED)
            
            if device_ip:
                process_info.connection_info.device_ip = device_ip
            if device_port:
                process_info.connection_info.device_port = device_port
            
            if status == ConnectionStatus.CONNECTED:
                process_info.connection_info.last_connect_time = datetime.now()
            elif status in [ConnectionStatus.DISCONNECTED, ConnectionStatus.ERROR]:
                process_info.connection_info.connection_errors += 1
    
    def get_process_health_report(self, process_name: str) -> Dict[str, Any]:
        """获取进程健康报告"""
        if process_name not in self.processes:
            return {}
        
        process_info = self.processes[process_name]
        
        # 生成健康检查项目
        health_checks = []
        
        # 进程状态检查
        if process_info.status == ProcessState.RUNNING:
            health_checks.append({
                "check": "进程状态",
                "status": "正常",
                "score": 25,
                "details": "进程正在运行"
            })
        else:
            health_checks.append({
                "check": "进程状态",
                "status": "异常",
                "score": 0,
                "details": f"进程状态: {process_info.status.value}"
            })
        
        # 资源使用检查
        cpu_score = 25
        if process_info.cpu_percent > 80:
            cpu_score = 5
        elif process_info.cpu_percent > 60:
            cpu_score = 15
        
        health_checks.append({
            "check": "CPU使用率",
            "status": "正常" if cpu_score > 15 else "警告" if cpu_score > 5 else "异常",
            "score": cpu_score,
            "details": f"CPU使用率: {process_info.cpu_percent}%"
        })
        
        # 内存使用检查
        memory_score = 25
        if process_info.memory_mb > 1000:
            memory_score = 5
        elif process_info.memory_mb > 500:
            memory_score = 15
        
        health_checks.append({
            "check": "内存使用",
            "status": "正常" if memory_score > 15 else "警告" if memory_score > 5 else "异常",
            "score": memory_score,
            "details": f"内存使用: {process_info.memory_mb}MB"
        })
        
        # 稳定性检查
        stability_score = 25
        if process_info.restart_count > 3:
            stability_score = 5
        elif process_info.restart_count > 1:
            stability_score = 15
        
        health_checks.append({
            "check": "运行稳定性",
            "status": "正常" if stability_score > 15 else "警告" if stability_score > 5 else "异常",
            "score": stability_score,
            "details": f"重启次数: {process_info.restart_count}次"
        })
        
        total_score = sum(check["score"] for check in health_checks)
        
        return {
            "process_name": process_name,
            "overall_score": total_score,
            "overall_status": "健康" if total_score > 80 else "警告" if total_score > 50 else "异常",
            "health_checks": health_checks,
            "recommendations": self._generate_health_recommendations(process_info),
            "last_check_time": datetime.now().isoformat()
        }
    
    def _generate_health_recommendations(self, process_info: EnhancedProcessInfo) -> List[str]:
        """生成健康建议"""
        recommendations = []
        
        if process_info.status != ProcessState.RUNNING:
            recommendations.append("检查进程配置和启动参数")
        
        if process_info.cpu_percent > 80:
            recommendations.append("检查进程是否存在死循环或性能问题")
        
        if process_info.memory_mb > 1000:
            recommendations.append("检查内存泄漏问题")
        
        if process_info.restart_count > 3:
            recommendations.append("分析进程崩溃原因，检查日志文件")
        
        if process_info.error_count_24h > 10:
            recommendations.append("检查错误日志，修复频繁出现的错误")
        
        if process_info.connection_info and process_info.connection_info.status != ConnectionStatus.CONNECTED:
            recommendations.append("检查设备连接和网络状态")
        
        if not recommendations:
            recommendations.append("进程运行状态良好")
        
        return recommendations
    
    def cleanup_old_data(self, days: int = 7):
        """清理旧的监控数据"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cutoff_time = datetime.now() - timedelta(days=days)
            
            # 清理旧的性能指标数据
            cursor.execute('''
                DELETE FROM performance_metrics 
                WHERE timestamp < ?
            ''', (cutoff_time.isoformat(),))
            
            # 清理旧的进程状态数据
            cursor.execute('''
                DELETE FROM process_status 
                WHERE timestamp < ?
            ''', (cutoff_time.isoformat(),))
            
            # 清理旧的连接状态数据
            cursor.execute('''
                DELETE FROM connection_status 
                WHERE timestamp < ?
            ''', (cutoff_time.isoformat(),))
            
            conn.commit()
            deleted_rows = cursor.rowcount
            conn.close()
            
            self.logger.info(f"清理了 {deleted_rows} 条旧监控数据")
            
        except Exception as e:
            self.logger.error(f"清理旧数据失败: {e}")

# 全局实例
enhanced_process_manager = EnhancedProcessManager()

