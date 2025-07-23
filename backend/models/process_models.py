from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum
from dataclasses import dataclass

class ProcessState(str, Enum):
    RUNNING = "running"
    STOPPED = "stopped"
    ERROR = "error"
    STARTING = "starting"
    STOPPING = "stopping"
    CRASHED = "crashed"
    UNKNOWN = "unknown"

class ProcessStatus(str, Enum):
    RUNNING = "running"
    STOPPED = "stopped"
    ERROR = "error"
    STARTING = "starting"
    STOPPING = "stopping"

class ProcessType(str, Enum):
    MODBUS_TCP = "modbus_tcp"
    OPC_UA = "opc_ua"
    MELSOFT_A1E = "melsoft_a1e"
    GENERIC_PLC = "generic_plc"

class ConnectionStatus(str, Enum):
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    ERROR = "error"
    UNKNOWN = "unknown"

class HealthStatus(str, Enum):
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"

@dataclass
class ConnectionInfo:
    device_ip: Optional[str] = None
    device_port: Optional[int] = None
    is_connected: bool = False
    last_connect_time: Optional[datetime] = None
    connection_errors: int = 0
    protocol_type: Optional[str] = None
    status: ConnectionStatus = ConnectionStatus.UNKNOWN

@dataclass
class PerformanceMetrics:
    process_name: str
    timestamp: datetime
    cpu_percent: float = 0.0
    memory_mb: float = 0.0
    data_points_per_minute: float = 0.0
    error_rate: float = 0.0
    response_time_ms: float = 0.0

class ProcessInfo(BaseModel):
    pid: Optional[int] = None
    name: str
    type: ProcessType
    status: ProcessStatus
    cpu_percent: Optional[float] = 0.0
    memory_percent: Optional[float] = 0.0
    memory_mb: Optional[float] = 0.0
    start_time: Optional[datetime] = None
    uptime: Optional[int] = 0  # seconds
    config_file: Optional[str] = None
    description: Optional[str] = None
    # Enhanced fields for monitoring optimization
    last_heartbeat: Optional[datetime] = None
    connection_status: ConnectionStatus = ConnectionStatus.UNKNOWN
    data_collection_rate: float = 0.0
    last_data_time: Optional[datetime] = None
    health_score: float = 100.0
    error_count_24h: int = 0
    restart_count: int = 0
    last_error: Optional[str] = None
    command: Optional[List[str]] = None
    
    class Config:
        use_enum_values = True

# Enhanced ProcessInfo for internal use with dataclass
@dataclass
class EnhancedProcessInfo:
    name: str
    type: str
    status: ProcessState
    pid: Optional[int] = None
    cpu_percent: float = 0.0
    memory_mb: float = 0.0
    memory_percent: float = 0.0
    start_time: Optional[datetime] = None
    uptime_seconds: int = 0
    restart_count: int = 0
    last_error: Optional[str] = None
    config_file: Optional[str] = None
    command: List[str] = None
    description: Optional[str] = None
    # Enhanced monitoring fields
    last_heartbeat: Optional[datetime] = None
    connection_info: Optional[ConnectionInfo] = None
    data_collection_rate: float = 0.0
    last_data_time: Optional[datetime] = None
    health_score: float = 100.0
    error_count_24h: int = 0
    auto_restart: bool = True
    max_restarts: int = 5

class ProcessControl(BaseModel):
    action: str = Field(..., description="Action to perform: start, stop, restart")
    process_names: Optional[List[str]] = Field(None, description="List of process names, if None applies to all")
    
class ProcessLog(BaseModel):
    timestamp: datetime
    level: str
    message: str
    process_name: str
    pid: Optional[int] = None

class ProcessStats(BaseModel):
    total_processes: int
    running_processes: int
    stopped_processes: int
    error_processes: int
    total_cpu_percent: float
    total_memory_mb: float
    
class ProcessListResponse(BaseModel):
    processes: List[ProcessInfo]
    stats: ProcessStats
    
class ProcessControlResponse(BaseModel):
    success: bool
    message: str
    affected_processes: List[str]
    
class ProcessLogResponse(BaseModel):
    logs: List[ProcessLog]
    total_count: int
    page: int
    page_size: int