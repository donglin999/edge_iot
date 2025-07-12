from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Union
from datetime import datetime
from enum import Enum

class DataPoint(BaseModel):
    timestamp: datetime
    measurement: str
    field: str
    value: Union[float, int, str, bool]
    tags: Optional[Dict[str, str]] = {}
    
class DeviceInfo(BaseModel):
    device_id: str
    device_name: str
    device_type: str
    status: str
    last_seen: Optional[datetime] = None
    measurements_count: int = 0
    tags: Optional[Dict[str, str]] = {}
    
class MeasurementInfo(BaseModel):
    measurement: str
    device_id: str
    fields: List[str]
    tags: Optional[Dict[str, str]] = {}
    last_update: Optional[datetime] = None
    data_points_count: int = 0
    
class DataQuery(BaseModel):
    start_time: Optional[datetime] = Field(None, description="Start time for data query")
    end_time: Optional[datetime] = Field(None, description="End time for data query")
    devices: Optional[List[str]] = Field(None, description="List of device IDs to filter")
    measurements: Optional[List[str]] = Field(None, description="List of measurements to filter")
    fields: Optional[List[str]] = Field(None, description="List of fields to include")
    tags: Optional[Dict[str, str]] = Field(None, description="Tag filters")
    limit: Optional[int] = Field(1000, description="Maximum number of records to return")
    offset: Optional[int] = Field(0, description="Offset for pagination")
    
class DataStats(BaseModel):
    total_devices: int
    active_devices: int
    total_measurements: int
    total_data_points: int
    data_rate_per_second: float
    storage_size_mb: float
    oldest_data: Optional[datetime] = None
    newest_data: Optional[datetime] = None
    
class RealTimeData(BaseModel):
    data_points: List[DataPoint]
    timestamp: datetime
    total_count: int
    
class HistoricalData(BaseModel):
    data_points: List[DataPoint]
    query: DataQuery
    total_count: int
    has_more: bool
    
class DataExport(BaseModel):
    format: str = Field(..., description="Export format: csv, json, xlsx")
    query: DataQuery
    filename: Optional[str] = None
    
class DataExportResponse(BaseModel):
    success: bool
    message: str
    download_url: Optional[str] = None
    file_size: Optional[int] = None
    
class DeviceListResponse(BaseModel):
    devices: List[DeviceInfo]
    total_count: int
    
class MeasurementListResponse(BaseModel):
    measurements: List[MeasurementInfo]
    total_count: int