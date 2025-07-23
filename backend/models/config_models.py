from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

class ConfigStatus(str, Enum):
    ACTIVE = "active"
    PENDING = "pending"
    INVALID = "invalid"
    BACKUP = "backup"

class ConfigValidationResult(BaseModel):
    is_valid: bool
    errors: List[str] = []
    warnings: List[str] = []
    summary: Dict[str, Any] = {}

class ConfigInfo(BaseModel):
    filename: str
    version: str
    last_updated: datetime
    devices: int
    points: int

class ConfigFile(BaseModel):
    id: str
    filename: str
    upload_time: datetime
    file_size: int
    status: ConfigStatus
    description: Optional[str] = None
    version: Optional[str] = None
    checksum: Optional[str] = None
    
class ConfigUpload(BaseModel):
    filename: str
    description: Optional[str] = None
    apply_immediately: bool = False
    
class ConfigValidation(BaseModel):
    is_valid: bool
    errors: List[str] = []
    warnings: List[str] = []
    summary: Dict[str, Any] = {}
    
class ConfigDiff(BaseModel):
    added: List[Dict[str, Any]] = []
    removed: List[Dict[str, Any]] = []
    modified: List[Dict[str, Any]] = []
    summary: Dict[str, Any] = {}
    
class ConfigApply(BaseModel):
    config_id: str
    force: bool = False
    backup_current: bool = True
    
class ConfigHistory(BaseModel):
    configs: List[ConfigFile]
    total_count: int
    
class ConfigUploadResponse(BaseModel):
    success: bool
    message: str
    config_id: Optional[str] = None
    validation: Optional[ConfigValidation] = None
    
class ConfigApplyResponse(BaseModel):
    success: bool
    message: str
    backup_id: Optional[str] = None
    affected_processes: List[str] = []
    
class ConfigRollback(BaseModel):
    config_id: str
    reason: Optional[str] = None
    
class ConfigRollbackResponse(BaseModel):
    success: bool
    message: str
    restored_config_id: str
    affected_processes: List[str] = []