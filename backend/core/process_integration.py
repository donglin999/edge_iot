import os
import sys
import json
import signal
import subprocess
import asyncio
import threading
import time
import logging
import socket
from typing import Dict, List, Optional, Any, AsyncGenerator, Tuple
from dataclasses import dataclass
from pathlib import Path
from datetime import datetime
import psutil

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from logs.log_config import get_logger
from models.process_models import ProcessState, EnhancedProcessInfo, ConnectionStatus, ConnectionInfo
from core.connection_monitor import connection_monitor, ConnectionCheckResult

logger = get_logger("backend", "core", "process_integration")

@dataclass
class ProcessOutput:
    """进程输出数据结构"""
    timestamp: datetime
    stream_type: str  # 'stdout' or 'stderr'
    content: str
    process_name: str

@dataclass
class ProcessSignalResult:
    """进程信号处理结果"""
    success: bool
    message: str
    signal_sent: Optional[int] = None
    process_name: Optional[str] = None

class ProcessIntegration:
    """与project-data-acquisition进程的集成层"""
    
    def __init__(self):
        self.logger = get_logger("backend", "core", "process_integration")
        self.data_acquisition_path = self._find_data_acquisition_path()
        self.process_configs: Dict[str, Dict] = {}
        self.output_monitors: Dict[str, threading.Thread] = {}
        self.output_callbacks: Dict[str, callable] = {}
        self.running_processes: Dict[str, subprocess.Popen] = {}
        self.connection_info: Dict[str, ConnectionInfo] = {}
        
        # 启动连接监控
        connection_monitor.start_monitoring(interval=30)
        
        # 加载进程配置
        self._load_process_configs()
    
    def _find_data_acquisition_path(self) -> Optional[str]:
        """查找project-data-acquisition目录路径"""
        possible_paths = [
            "project-data-acquisition",
            "../project-data-acquisition",
            os.path.join(os.getcwd(), "project-data-acquisition"),
            os.path.join(os.path.dirname(os.getcwd()), "project-data-acquisition")
        ]
        
        for path in possible_paths:
            abs_path = os.path.abspath(path)
            self.logger.info(f"检查数据采集路径: {abs_path}")
            if os.path.exists(abs_path) and os.path.exists(os.path.join(abs_path, "run.py")):
                self.logger.info(f"找到数据采集目录: {abs_path}")
                return abs_path
        
        self.logger.warning("未找到project-data-acquisition目录")
        return None
    
    def _load_process_configs(self):
        """加载进程配置"""
        try:
            if not self.data_acquisition_path:
                self.logger.warning("数据采集路径未找到，使用默认配置")
                self.process_configs = self._get_default_configs()
                return
            
            # 尝试读取Excel配置文件
            excel_path = os.path.join(self.data_acquisition_path, "数据地址清单.xlsx")
            if os.path.exists(excel_path):
                self.logger.info(f"找到Excel配置文件: {excel_path}")
                # 这里可以解析Excel文件获取配置，暂时使用默认配置
                self.process_configs = self._get_default_configs()
            else:
                self.logger.warning(f"Excel配置文件不存在: {excel_path}")
                self.process_configs = self._get_default_configs()
                
        except Exception as e:
            self.logger.error(f"加载进程配置失败: {e}")
            self.process_configs = self._get_default_configs()
    
    def _get_default_configs(self) -> Dict[str, Dict]:
        """获取默认进程配置"""
        return {
            "modbus_collector": {
                "type": "modbus",
                "module": "apps.collector.modbustcp_influx",
                "class": "ModbustcpInflux",
                "method": "modbustcp_influx",
                "config_file": "configs/modbus_config.json",
                "description": "Modbus TCP数据采集进程"
            },
            "opcua_collector": {
                "type": "opcua", 
                "module": "apps.collector.opcua_influx",
                "class": "OpcuaInflux",
                "method": "start_collector",
                "config_file": "configs/opcua_config.json",
                "description": "OPC UA数据采集进程"
            },
            "plc_collector": {
                "type": "plc",
                "module": "apps.collector.plc_influx", 
                "class": "PlcInflux",
                "method": "plc_influx",
                "config_file": "configs/plc_config.json",
                "description": "PLC数据采集进程"
            },
            "melseca1enet_collector": {
                "type": "melseca1enet",
                "module": "apps.collector.melseca1enet_influx",
                "class": "MelsecA1ENetInflux", 
                "method": "melseca1enet_influx",
                "config_file": "configs/melseca1enet_config.json",
                "description": "Melsoft A1E数据采集进程"
            }
        }
    
    def create_process_command(self, process_type: str, config: Dict) -> List[str]:
        """创建进程启动命令"""
        try:
            if process_type not in self.process_configs:
                raise ValueError(f"未知的进程类型: {process_type}")
            
            process_config = self.process_configs[process_type]
            
            # 基础Python命令
            command = ["python", "-c"]
            
            # 创建启动脚本
            startup_script = f"""
import sys
import os
sys.path.insert(0, os.getcwd())

from {process_config['module']} import {process_config['class']}

# 创建配置
config = {json.dumps(config, ensure_ascii=False)}

# 创建实例并启动
collector = {process_config['class']}(config)
collector.{process_config['method']}()
"""
            
            command.append(startup_script)
            
            self.logger.info(f"创建进程命令: {process_type}")
            self.logger.debug(f"启动脚本: {startup_script}")
            
            return command
            
        except Exception as e:
            self.logger.error(f"创建进程命令失败: {e}")
            raise
    
    def start_data_acquisition_process(self, process_name: str, command: List[str], config: Dict) -> Optional[subprocess.Popen]:
        """启动数据采集进程"""
        try:
            if not self.data_acquisition_path:
                raise RuntimeError("数据采集路径未找到")
            
            # 设置工作目录
            cwd = self.data_acquisition_path
            
            # 设置环境变量
            env = os.environ.copy()
            
            # 设置Python路径
            python_path_list = [cwd]
            if "PYTHONPATH" in env:
                existing_paths = env["PYTHONPATH"].split(os.pathsep)
                python_path_list.extend(existing_paths)
            
            env["PYTHONPATH"] = os.pathsep.join(python_path_list)
            
            self.logger.info(f"启动进程: {process_name}")
            self.logger.info(f"工作目录: {cwd}")
            self.logger.info(f"命令: {' '.join(command)}")
            
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
            
            # 存储进程引用
            self.running_processes[process_name] = proc
            
            # 启动输出监控
            self._start_output_monitoring(process_name, proc)
            
            self.logger.info(f"进程 {process_name} 启动成功, PID: {proc.pid}")
            return proc
            
        except Exception as e:
            self.logger.error(f"启动数据采集进程失败: {e}")
            return None
    
    def _start_output_monitoring(self, process_name: str, process: subprocess.Popen):
        """启动进程输出监控"""
        try:
            # 启动stdout监控线程
            stdout_thread = threading.Thread(
                target=self._monitor_process_output,
                args=(process_name, process, "stdout"),
                daemon=True
            )
            stdout_thread.start()
            
            # 启动stderr监控线程  
            stderr_thread = threading.Thread(
                target=self._monitor_process_output,
                args=(process_name, process, "stderr"),
                daemon=True
            )
            stderr_thread.start()
            
            # 存储监控线程引用
            self.output_monitors[f"{process_name}_stdout"] = stdout_thread
            self.output_monitors[f"{process_name}_stderr"] = stderr_thread
            
            self.logger.info(f"进程 {process_name} 输出监控已启动")
            
        except Exception as e:
            self.logger.error(f"启动输出监控失败: {e}")
    
    def _monitor_process_output(self, process_name: str, process: subprocess.Popen, stream_type: str):
        """监控进程输出"""
        try:
            stream = process.stdout if stream_type == "stdout" else process.stderr
            
            while process.poll() is None:
                try:
                    line = stream.readline()
                    if line:
                        output = ProcessOutput(
                            timestamp=datetime.now(),
                            stream_type=stream_type,
                            content=line.strip(),
                            process_name=process_name
                        )
                        
                        # 记录日志
                        if stream_type == "stderr":
                            self.logger.warning(f"[{process_name}] {line.strip()}")
                        else:
                            self.logger.info(f"[{process_name}] {line.strip()}")
                        
                        # 调用回调函数
                        if process_name in self.output_callbacks:
                            try:
                                self.output_callbacks[process_name](output)
                            except Exception as e:
                                self.logger.error(f"输出回调函数执行失败: {e}")
                                
                except Exception as e:
                    if process.poll() is None:  # 进程仍在运行
                        self.logger.error(f"读取进程输出失败: {e}")
                    break
            
            # 进程结束后读取剩余输出
            try:
                remaining_output = stream.read()
                if remaining_output:
                    for line in remaining_output.split('\n'):
                        if line.strip():
                            output = ProcessOutput(
                                timestamp=datetime.now(),
                                stream_type=stream_type,
                                content=line.strip(),
                                process_name=process_name
                            )
                            
                            if stream_type == "stderr":
                                self.logger.warning(f"[{process_name}] {line.strip()}")
                            else:
                                self.logger.info(f"[{process_name}] {line.strip()}")
                            
                            if process_name in self.output_callbacks:
                                try:
                                    self.output_callbacks[process_name](output)
                                except Exception as e:
                                    self.logger.error(f"输出回调函数执行失败: {e}")
            except Exception as e:
                self.logger.error(f"读取剩余输出失败: {e}")
                
        except Exception as e:
            self.logger.error(f"监控进程输出时发生异常: {e}")
    
    async def monitor_process_output_async(self, process_name: str) -> AsyncGenerator[ProcessOutput, None]:
        """异步监控进程输出"""
        if process_name not in self.running_processes:
            return
        
        process = self.running_processes[process_name]
        
        try:
            while process.poll() is None:
                # 检查stdout
                if process.stdout and process.stdout.readable():
                    try:
                        line = await asyncio.get_event_loop().run_in_executor(
                            None, process.stdout.readline
                        )
                        if line:
                            yield ProcessOutput(
                                timestamp=datetime.now(),
                                stream_type="stdout",
                                content=line.strip(),
                                process_name=process_name
                            )
                    except Exception as e:
                        self.logger.error(f"读取stdout失败: {e}")
                
                # 检查stderr
                if process.stderr and process.stderr.readable():
                    try:
                        line = await asyncio.get_event_loop().run_in_executor(
                            None, process.stderr.readline
                        )
                        if line:
                            yield ProcessOutput(
                                timestamp=datetime.now(),
                                stream_type="stderr", 
                                content=line.strip(),
                                process_name=process_name
                            )
                    except Exception as e:
                        self.logger.error(f"读取stderr失败: {e}")
                
                await asyncio.sleep(0.1)  # 避免过度占用CPU
                
        except Exception as e:
            self.logger.error(f"异步监控进程输出失败: {e}")
    
    def set_output_callback(self, process_name: str, callback: callable):
        """设置进程输出回调函数"""
        self.output_callbacks[process_name] = callback
        self.logger.info(f"设置进程 {process_name} 的输出回调函数")
    
    def remove_output_callback(self, process_name: str):
        """移除进程输出回调函数"""
        if process_name in self.output_callbacks:
            del self.output_callbacks[process_name]
            self.logger.info(f"移除进程 {process_name} 的输出回调函数")
    
    def send_process_signal(self, pid: int, signal_type: int, process_name: Optional[str] = None) -> ProcessSignalResult:
        """发送进程信号"""
        try:
            if not psutil.pid_exists(pid):
                return ProcessSignalResult(
                    success=False,
                    message=f"进程 PID {pid} 不存在",
                    process_name=process_name
                )
            
            process = psutil.Process(pid)
            
            # 检查进程是否为我们管理的进程
            if process_name and process_name in self.running_processes:
                managed_process = self.running_processes[process_name]
                if managed_process.pid != pid:
                    return ProcessSignalResult(
                        success=False,
                        message=f"PID {pid} 与管理的进程 {process_name} 不匹配",
                        process_name=process_name
                    )
            
            # 发送信号 - Windows兼容性处理
            if signal_type == signal.SIGTERM:
                process.terminate()
                message = f"发送SIGTERM信号到进程 {pid}"
            elif hasattr(signal, 'SIGKILL') and signal_type == signal.SIGKILL:
                process.kill()
                message = f"发送SIGKILL信号到进程 {pid}"
            elif signal_type == 9:  # SIGKILL的数值，用于Windows兼容
                process.kill()
                message = f"强制终止进程 {pid}"
            elif hasattr(signal, 'SIGINT') and signal_type == signal.SIGINT:
                process.send_signal(signal.SIGINT)
                message = f"发送SIGINT信号到进程 {pid}"
            else:
                # 对于其他信号，尝试使用psutil的方法
                if hasattr(process, 'send_signal'):
                    process.send_signal(signal_type)
                    message = f"发送信号 {signal_type} 到进程 {pid}"
                else:
                    # 如果不支持，则使用terminate作为默认
                    process.terminate()
                    message = f"发送终止信号到进程 {pid}"
            
            self.logger.info(message)
            
            return ProcessSignalResult(
                success=True,
                message=message,
                signal_sent=signal_type,
                process_name=process_name
            )
            
        except psutil.NoSuchProcess:
            return ProcessSignalResult(
                success=False,
                message=f"进程 PID {pid} 不存在",
                process_name=process_name
            )
        except psutil.AccessDenied:
            return ProcessSignalResult(
                success=False,
                message=f"没有权限访问进程 PID {pid}",
                process_name=process_name
            )
        except Exception as e:
            return ProcessSignalResult(
                success=False,
                message=f"发送信号失败: {str(e)}",
                process_name=process_name
            )
    
    def graceful_stop_process(self, process_name: str, timeout: int = 10) -> ProcessSignalResult:
        """优雅停止进程"""
        try:
            if process_name not in self.running_processes:
                return ProcessSignalResult(
                    success=False,
                    message=f"进程 {process_name} 未在运行",
                    process_name=process_name
                )
            
            process = self.running_processes[process_name]
            pid = process.pid
            
            self.logger.info(f"开始优雅停止进程 {process_name} (PID: {pid})")
            
            # 首先尝试SIGTERM
            result = self.send_process_signal(pid, signal.SIGTERM, process_name)
            if not result.success:
                return result
            
            # 等待进程结束
            try:
                process.wait(timeout=timeout)
                self.logger.info(f"进程 {process_name} 已优雅停止")
                
                # 清理进程引用
                self._cleanup_process(process_name)
                
                return ProcessSignalResult(
                    success=True,
                    message=f"进程 {process_name} 已优雅停止",
                    signal_sent=signal.SIGTERM,
                    process_name=process_name
                )
                
            except subprocess.TimeoutExpired:
                # 超时后强制终止
                self.logger.warning(f"进程 {process_name} 优雅停止超时，强制终止")
                return self.force_kill_process(process_name)
                
        except Exception as e:
            return ProcessSignalResult(
                success=False,
                message=f"优雅停止进程失败: {str(e)}",
                process_name=process_name
            )
    
    def force_kill_process(self, process_name: str) -> ProcessSignalResult:
        """强制终止进程"""
        try:
            if process_name not in self.running_processes:
                return ProcessSignalResult(
                    success=False,
                    message=f"进程 {process_name} 未在运行",
                    process_name=process_name
                )
            
            process = self.running_processes[process_name]
            pid = process.pid
            
            self.logger.info(f"强制终止进程 {process_name} (PID: {pid})")
            
            # 发送强制终止信号 - Windows兼容性处理
            kill_signal = 9 if not hasattr(signal, 'SIGKILL') else signal.SIGKILL
            result = self.send_process_signal(pid, kill_signal, process_name)
            if not result.success:
                return result
            
            # 等待进程结束
            try:
                process.wait(timeout=5)
                self.logger.info(f"进程 {process_name} 已强制终止")
                
                # 清理进程引用
                self._cleanup_process(process_name)
                
                return ProcessSignalResult(
                    success=True,
                    message=f"进程 {process_name} 已强制终止",
                    signal_sent=kill_signal,
                    process_name=process_name
                )
                
            except subprocess.TimeoutExpired:
                return ProcessSignalResult(
                    success=False,
                    message=f"强制终止进程 {process_name} 失败",
                    process_name=process_name
                )
                
        except Exception as e:
            return ProcessSignalResult(
                success=False,
                message=f"强制终止进程失败: {str(e)}",
                process_name=process_name
            )
    
    def _cleanup_process(self, process_name: str):
        """清理进程相关资源"""
        try:
            # 移除进程引用
            if process_name in self.running_processes:
                del self.running_processes[process_name]
            
            # 移除输出回调
            if process_name in self.output_callbacks:
                del self.output_callbacks[process_name]
            
            # 清理监控线程引用
            for key in list(self.output_monitors.keys()):
                if key.startswith(process_name):
                    del self.output_monitors[key]
            
            self.logger.info(f"进程 {process_name} 相关资源已清理")
            
        except Exception as e:
            self.logger.error(f"清理进程资源失败: {e}")
    
    def read_process_config(self, config_path: str) -> Dict:
        """读取进程配置文件"""
        try:
            if not os.path.isabs(config_path) and self.data_acquisition_path:
                config_path = os.path.join(self.data_acquisition_path, config_path)
            
            if not os.path.exists(config_path):
                raise FileNotFoundError(f"配置文件不存在: {config_path}")
            
            with open(config_path, 'r', encoding='utf-8') as f:
                if config_path.endswith('.json'):
                    config = json.load(f)
                else:
                    # 对于其他格式的配置文件，可以扩展支持
                    raise ValueError(f"不支持的配置文件格式: {config_path}")
            
            self.logger.info(f"读取配置文件成功: {config_path}")
            return config
            
        except Exception as e:
            self.logger.error(f"读取配置文件失败: {e}")
            raise
    
    def update_process_config(self, config_path: str, config: Dict) -> bool:
        """更新进程配置文件"""
        try:
            if not os.path.isabs(config_path) and self.data_acquisition_path:
                config_path = os.path.join(self.data_acquisition_path, config_path)
            
            # 确保目录存在
            os.makedirs(os.path.dirname(config_path), exist_ok=True)
            
            with open(config_path, 'w', encoding='utf-8') as f:
                if config_path.endswith('.json'):
                    json.dump(config, f, ensure_ascii=False, indent=2)
                else:
                    raise ValueError(f"不支持的配置文件格式: {config_path}")
            
            self.logger.info(f"更新配置文件成功: {config_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"更新配置文件失败: {e}")
            return False
    
    def get_process_status(self, process_name: str) -> Optional[Dict]:
        """获取进程状态"""
        if process_name not in self.running_processes:
            return None
        
        process = self.running_processes[process_name]
        
        try:
            # 获取进程信息
            psutil_process = psutil.Process(process.pid)
            
            return {
                "name": process_name,
                "pid": process.pid,
                "status": "running" if process.poll() is None else "stopped",
                "cpu_percent": psutil_process.cpu_percent(),
                "memory_mb": psutil_process.memory_info().rss / 1024 / 1024,
                "create_time": datetime.fromtimestamp(psutil_process.create_time()),
                "cmdline": psutil_process.cmdline()
            }
            
        except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
            self.logger.warning(f"获取进程状态失败: {e}")
            return {
                "name": process_name,
                "pid": process.pid,
                "status": "unknown",
                "error": str(e)
            }
    
    def get_all_running_processes(self) -> Dict[str, Dict]:
        """获取所有运行中的进程状态"""
        result = {}
        for process_name in self.running_processes:
            status = self.get_process_status(process_name)
            if status:
                result[process_name] = status
        return result
    
    def is_process_running(self, process_name: str) -> bool:
        """检查进程是否在运行"""
        if process_name not in self.running_processes:
            return False
        
        process = self.running_processes[process_name]
        return process.poll() is None
    
    def get_data_acquisition_path(self) -> Optional[str]:
        """获取数据采集系统路径"""
        return self.data_acquisition_path
    
    def get_available_process_types(self) -> List[str]:
        """获取可用的进程类型"""
        return list(self.process_configs.keys())
    
    def get_process_config_template(self, process_type: str) -> Optional[Dict]:
        """获取进程配置模板"""
        if process_type not in self.process_configs:
            return None
        
        return self.process_configs[process_type].copy()
    
    # 连接监控相关方法
    def register_connection_monitoring(self, process_name: str, device_ip: str, device_port: int, protocol_type: str) -> bool:
        """注册连接监控"""
        try:
            # 创建连接信息
            conn_info = ConnectionInfo(
                device_ip=device_ip,
                device_port=device_port,
                protocol_type=protocol_type
            )
            
            # 存储连接信息
            self.connection_info[process_name] = conn_info
            
            # 注册到连接监控
            result = connection_monitor.register_connection(process_name, conn_info)
            
            # 设置回调函数
            if result:
                connection_monitor.set_callback(process_name, self._connection_status_callback)
            
            self.logger.info(f"注册连接监控: {process_name} -> {device_ip}:{device_port} ({protocol_type})")
            return result
            
        except Exception as e:
            self.logger.error(f"注册连接监控失败: {e}")
            return False
    
    def unregister_connection_monitoring(self, process_name: str) -> bool:
        """取消注册连接监控"""
        try:
            # 从连接监控中取消注册
            result = connection_monitor.unregister_connection(process_name)
            
            # 移除连接信息
            if process_name in self.connection_info:
                del self.connection_info[process_name]
            
            self.logger.info(f"取消连接监控: {process_name}")
            return result
            
        except Exception as e:
            self.logger.error(f"取消连接监控失败: {e}")
            return False
    
    def _connection_status_callback(self, conn_info: ConnectionInfo):
        """连接状态变化回调函数"""
        # 这里可以实现连接状态变化的处理逻辑
        # 例如记录日志、发送通知等
        pass
    
    def check_connection(self, process_name: str) -> ConnectionCheckResult:
        """检查连接状态"""
        return connection_monitor.check_connection(process_name)
    
    def get_connection_status(self, process_name: str) -> Optional[ConnectionInfo]:
        """获取连接状态"""
        return connection_monitor.get_connection_status(process_name)
    
    def get_all_connection_status(self) -> Dict[str, ConnectionInfo]:
        """获取所有连接状态"""
        return connection_monitor.get_all_connection_status()
    
    def get_connection_statistics(self, process_name: str) -> Dict[str, Any]:
        """获取连接统计信息"""
        return connection_monitor.get_connection_statistics(process_name)
    
    def get_connection_history(self, process_name: str, limit: int = 10) -> List[ConnectionCheckResult]:
        """获取连接历史记录"""
        return connection_monitor.get_connection_history(process_name, limit)

# 全局实例
process_integration = ProcessIntegration()