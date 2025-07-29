import asyncio
import psutil
import logging
from typing import List, Optional, Dict
from datetime import datetime, timedelta
import sys
import os
import time

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from logs.log_config import get_logger

from models.process_models import (
    ProcessInfo, ProcessStats, ProcessListResponse, 
    ProcessControlResponse, ProcessLog, ProcessLogResponse,
    ProcessStatus, ProcessType
)
from core.integration import integration
from core.websocket_manager import websocket_manager

logger = get_logger("backend", "services", "process_service")

class ProcessService:
    """Service for managing data acquisition processes"""
    
    def __init__(self):
        self.process_manager = integration.get_process_manager()
        # 添加缓存机制
        self._cache = {}
        self._cache_timeout = 5  # 缓存5秒
        self._last_cache_time = 0
        
    async def get_all_processes(self) -> ProcessListResponse:
        """Get all processes with their status and statistics"""
        try:
            current_time = time.time()
            
            # 检查缓存是否有效
            if (current_time - self._last_cache_time) < self._cache_timeout and self._cache:
                logger.debug("使用缓存的进程数据")
                return self._cache
            
            # 获取进程数据
            processes_data = self.process_manager.get_all_processes()
            processes = []
            
            for name, data in processes_data.items():
                process_info = ProcessInfo(
                    pid=data.get("pid"),
                    name=name,
                    type=self._get_process_type(name),
                    status=self._get_process_status(data.get("status")),
                    cpu_percent=data.get("cpu_percent", 0.0),
                    memory_percent=data.get("memory_percent", 0.0),
                    memory_mb=data.get("memory_mb", 0.0),
                    start_time=self._parse_datetime(data.get("start_time")),
                    uptime=self._calculate_uptime(data.get("start_time")),
                    config_file=data.get("config_file"),
                    description=data.get("description")
                )
                processes.append(process_info)
            
            stats = self._calculate_stats(processes)
            
            # 创建响应对象
            response = ProcessListResponse(processes=processes, stats=stats)
            
            # 更新缓存
            self._cache = response
            self._last_cache_time = current_time
            
            # 异步广播进程更新（不阻塞响应）
            asyncio.create_task(self._broadcast_process_update(processes, stats))
            
            return response
            
        except Exception as e:
            logger.error(f"获取所有进程信息时出错: {e}")
            raise
    
    async def _broadcast_process_update(self, processes, stats):
        """异步广播进程更新"""
        try:
            await websocket_manager.broadcast_to_topic("processes", {
                "type": "process_update",
                "timestamp": datetime.now().isoformat(),
                "data": {
                    "total_processes": len(processes),
                    "running_processes": stats.running_processes,
                    "stopped_processes": stats.stopped_processes
                }
            })
        except Exception as e:
            logger.error(f"广播进程更新失败: {e}")
    
    def clear_cache(self):
        """清除缓存"""
        self._cache = {}
        self._last_cache_time = 0
        logger.debug("进程数据缓存已清除")
    
    async def get_process_status(self, process_name: str) -> Optional[ProcessInfo]:
        """Get status of a specific process"""
        try:
            processes_data = self.process_manager.get_all_processes()
            
            if process_name not in processes_data:
                return None
            
            data = processes_data[process_name]
            return ProcessInfo(
                pid=data.get("pid"),
                name=process_name,
                type=self._get_process_type(process_name),
                status=self._get_process_status(data.get("status")),
                cpu_percent=data.get("cpu_percent", 0.0),
                memory_percent=data.get("memory_percent", 0.0),
                memory_mb=data.get("memory_mb", 0.0),
                start_time=self._parse_datetime(data.get("start_time")),
                uptime=self._calculate_uptime(data.get("start_time")),
                config_file=data.get("config_file"),
                description=data.get("description")
            )
            
        except Exception as e:
            logger.error(f"获取进程 {process_name} 状态时出错: {e}")
            raise
    
    async def start_processes(self, process_names: Optional[List[str]] = None) -> ProcessControlResponse:
        """Start specified processes or all processes"""
        try:
            # 重新加载配置以确保获取最新的进程定义
            self.process_manager.reload_config()
            
            if process_names is None:
                # Start all processes
                processes_data = self.process_manager.get_all_processes()
                process_names = list(processes_data.keys())
            
            success_count = 0
            failed_processes = []
            error_details = {}
            
            for process_name in process_names:
                try:
                    if self.process_manager.start_process(process_name):
                        success_count += 1
                    else:
                        failed_processes.append(process_name)
                        # 获取详细错误信息
                        process_status = self.process_manager.get_process_status(process_name)
                        if process_status and process_status.get('last_error'):
                            error_details[process_name] = process_status['last_error']
                except Exception as e:
                    logger.error(f"启动进程 {process_name} 失败: {e}")
                    failed_processes.append(process_name)
                    error_details[process_name] = str(e)
            
            success = len(failed_processes) == 0
            message = f"成功启动 {success_count} 个进程"
            if failed_processes:
                message += f"，启动失败: {', '.join(failed_processes)}"
                # 添加错误详情到消息中
                if error_details:
                    message += " | 错误详情："
                    for proc_name, error in error_details.items():
                        # 只显示关键错误信息
                        if "ModuleNotFoundError" in error:
                            module_name = error.split("No module named ")[-1].replace("'", "").strip()
                            message += f" {proc_name}: 缺少Python模块 {module_name};"
                        elif "FileNotFoundError" in error:
                            if "No such file or directory" in error:
                                message += f" {proc_name}: 无法找到启动命令或文件;"
                            else:
                                message += f" {proc_name}: 文件或命令未找到;"
                        elif "PermissionError" in error:
                            message += f" {proc_name}: 权限错误;"
                        else:
                            # 显示错误的关键信息
                            short_error = error.split('\n')[-1] if '\n' in error else error
                            if len(short_error) > 50:
                                short_error = short_error[:50] + "..."
                            message += f" {proc_name}: {short_error};"
            
            # Broadcast process control event
            await websocket_manager.broadcast_to_topic("processes", {
                "type": "process_control",
                "action": "start",
                "timestamp": datetime.now().isoformat(),
                "data": {
                    "success": success,
                    "affected_processes": process_names,
                    "success_count": success_count,
                    "failed_processes": failed_processes
                }
            })
            
            return ProcessControlResponse(
                success=success,
                message=message,
                affected_processes=process_names
            )
            
        except Exception as e:
            logger.error(f"启动进程时出错: {e}")
            raise
    
    async def stop_processes(self, process_names: Optional[List[str]] = None) -> ProcessControlResponse:
        """Stop specified processes or all processes"""
        try:
            if process_names is None:
                # Stop all processes
                processes_data = self.process_manager.get_all_processes()
                process_names = list(processes_data.keys())
            
            success_count = 0
            failed_processes = []
            
            for process_name in process_names:
                try:
                    if self.process_manager.stop_process(process_name):
                        success_count += 1
                    else:
                        failed_processes.append(process_name)
                except Exception as e:
                    logger.error(f"停止进程 {process_name} 失败: {e}")
                    failed_processes.append(process_name)
            
            success = len(failed_processes) == 0
            message = f"成功停止 {success_count} 个进程"
            if failed_processes:
                message += f"，停止失败: {', '.join(failed_processes)}"
            
            # Broadcast process control event
            await websocket_manager.broadcast_to_topic("processes", {
                "type": "process_control",
                "action": "stop",
                "timestamp": datetime.now().isoformat(),
                "data": {
                    "success": success,
                    "affected_processes": process_names,
                    "success_count": success_count,
                    "failed_processes": failed_processes
                }
            })
            
            return ProcessControlResponse(
                success=success,
                message=message,
                affected_processes=process_names
            )
            
        except Exception as e:
            logger.error(f"停止进程时出错: {e}")
            raise
    
    async def restart_processes(self, process_names: Optional[List[str]] = None) -> ProcessControlResponse:
        """Restart specified processes or all processes"""
        try:
            if process_names is None:
                # Restart all processes
                processes_data = self.process_manager.get_all_processes()
                process_names = list(processes_data.keys())
            
            success_count = 0
            failed_processes = []
            
            for process_name in process_names:
                try:
                    if self.process_manager.restart_process(process_name):
                        success_count += 1
                    else:
                        failed_processes.append(process_name)
                except Exception as e:
                    logger.error(f"重启进程 {process_name} 失败: {e}")
                    failed_processes.append(process_name)
            
            success = len(failed_processes) == 0
            message = f"成功重启 {success_count} 个进程"
            if failed_processes:
                message += f"，重启失败: {', '.join(failed_processes)}"
            
            # Broadcast process control event
            await websocket_manager.broadcast_to_topic("processes", {
                "type": "process_control",
                "action": "restart",
                "timestamp": datetime.now().isoformat(),
                "data": {
                    "success": success,
                    "affected_processes": process_names,
                    "success_count": success_count,
                    "failed_processes": failed_processes
                }
            })
            
            return ProcessControlResponse(
                success=success,
                message=message,
                affected_processes=process_names
            )
            
        except Exception as e:
            logger.error(f"重启进程时出错: {e}")
            raise
    
    async def get_process_logs(self, process_name: str, lines: int = 100, page: int = 1) -> ProcessLogResponse:
        """Get logs for a specific process"""
        try:
            log_lines = self.process_manager.get_process_logs(process_name, lines * page)
            
            # Parse log lines into structured format
            logs = []
            for line in log_lines[-lines:]:  # Get last 'lines' entries for the page
                log_entry = ProcessLog(
                    timestamp=datetime.now(),  # Should parse from log line
                    level="INFO",  # Should parse from log line
                    message=line,
                    process_name=process_name
                )
                logs.append(log_entry)
            
            return ProcessLogResponse(
                logs=logs,
                total_count=len(log_lines),
                page=page,
                page_size=lines
            )
            
        except Exception as e:
            logger.error(f"获取进程 {process_name} 日志时出错: {e}")
            raise
    
    def _get_process_type(self, process_name: str) -> ProcessType:
        """Determine process type from name"""
        if "modbus" in process_name.lower():
            return ProcessType.MODBUS_TCP
        elif "opc" in process_name.lower():
            return ProcessType.OPC_UA
        elif "melsoft" in process_name.lower() or "a1e" in process_name.lower():
            return ProcessType.MELSOFT_A1E
        else:
            return ProcessType.GENERIC_PLC
    
    def _get_process_status(self, status_str: str) -> ProcessStatus:
        """Convert status string to ProcessStatus enum"""
        if not status_str:
            return ProcessStatus.STOPPED
        
        status_lower = status_str.lower()
        if status_lower == "running":
            return ProcessStatus.RUNNING
        elif status_lower == "stopped":
            return ProcessStatus.STOPPED
        elif status_lower == "error":
            return ProcessStatus.ERROR
        elif status_lower == "starting":
            return ProcessStatus.STARTING
        elif status_lower == "stopping":
            return ProcessStatus.STOPPING
        else:
            return ProcessStatus.STOPPED
    
    def _parse_datetime(self, date_str: Optional[str]) -> Optional[datetime]:
        """Parse datetime string"""
        if not date_str:
            return None
        
        try:
            return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        except:
            try:
                return datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
            except:
                return None
    
    def _calculate_uptime(self, start_time_str: Optional[str]) -> int:
        """Calculate uptime in seconds"""
        if not start_time_str:
            return 0
        
        start_time = self._parse_datetime(start_time_str)
        if not start_time:
            return 0
        
        return int((datetime.now() - start_time).total_seconds())
    
    def _calculate_stats(self, processes: List[ProcessInfo]) -> ProcessStats:
        """Calculate process statistics"""
        total_processes = len(processes)
        running_processes = sum(1 for p in processes if p.status == ProcessStatus.RUNNING)
        stopped_processes = sum(1 for p in processes if p.status == ProcessStatus.STOPPED)
        error_processes = sum(1 for p in processes if p.status == ProcessStatus.ERROR)
        
        total_cpu_percent = sum(p.cpu_percent or 0 for p in processes)
        total_memory_mb = sum(p.memory_mb or 0 for p in processes)
        
        return ProcessStats(
            total_processes=total_processes,
            running_processes=running_processes,
            stopped_processes=stopped_processes,
            error_processes=error_processes,
            total_cpu_percent=total_cpu_percent,
            total_memory_mb=total_memory_mb
        )