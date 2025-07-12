import asyncio
import psutil
import logging
from typing import List, Optional, Dict
from datetime import datetime, timedelta

from models.process_models import (
    ProcessInfo, ProcessStats, ProcessListResponse, 
    ProcessControlResponse, ProcessLog, ProcessLogResponse,
    ProcessStatus, ProcessType
)
from core.integration import integration
from core.websocket_manager import websocket_manager

logger = logging.getLogger(__name__)

class ProcessService:
    """Service for managing data acquisition processes"""
    
    def __init__(self):
        self.process_manager = integration.get_process_manager()
        
    async def get_all_processes(self) -> ProcessListResponse:
        """Get all processes with their status and statistics"""
        try:
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
            
            # Broadcast process update via WebSocket
            await websocket_manager.broadcast_to_topic("processes", {
                "type": "process_update",
                "timestamp": datetime.now().isoformat(),
                "data": {
                    "total_processes": len(processes),
                    "running_processes": stats.running_processes,
                    "stopped_processes": stats.stopped_processes
                }
            })
            
            return ProcessListResponse(processes=processes, stats=stats)
            
        except Exception as e:
            logger.error(f"Error getting all processes: {e}")
            raise
    
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
            logger.error(f"Error getting process status for {process_name}: {e}")
            raise
    
    async def start_processes(self, process_names: Optional[List[str]] = None) -> ProcessControlResponse:
        """Start specified processes or all processes"""
        try:
            if process_names is None:
                # Start all processes
                processes_data = self.process_manager.get_all_processes()
                process_names = list(processes_data.keys())
            
            success_count = 0
            failed_processes = []
            
            for process_name in process_names:
                try:
                    if self.process_manager.start_process(process_name):
                        success_count += 1
                    else:
                        failed_processes.append(process_name)
                except Exception as e:
                    logger.error(f"Failed to start process {process_name}: {e}")
                    failed_processes.append(process_name)
            
            success = len(failed_processes) == 0
            message = f"Started {success_count} processes successfully"
            if failed_processes:
                message += f", failed to start: {', '.join(failed_processes)}"
            
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
            logger.error(f"Error starting processes: {e}")
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
                    logger.error(f"Failed to stop process {process_name}: {e}")
                    failed_processes.append(process_name)
            
            success = len(failed_processes) == 0
            message = f"Stopped {success_count} processes successfully"
            if failed_processes:
                message += f", failed to stop: {', '.join(failed_processes)}"
            
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
            logger.error(f"Error stopping processes: {e}")
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
                    logger.error(f"Failed to restart process {process_name}: {e}")
                    failed_processes.append(process_name)
            
            success = len(failed_processes) == 0
            message = f"Restarted {success_count} processes successfully"
            if failed_processes:
                message += f", failed to restart: {', '.join(failed_processes)}"
            
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
            logger.error(f"Error restarting processes: {e}")
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
            logger.error(f"Error getting logs for process {process_name}: {e}")
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