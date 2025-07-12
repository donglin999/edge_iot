from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

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
    
    class Config:
        use_enum_values = True

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