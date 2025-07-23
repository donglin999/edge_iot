from enum import Enum
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
from datetime import datetime

class WebSocketMessageType(str, Enum):
    PROCESS_STATUS_UPDATE = "process_status_update"
    HEALTH_CHECK_RESULT = "health_check_result"
    LOG_STREAM = "log_stream"
    ERROR_ALERT = "error_alert"
    CONNECTION_STATUS = "connection_status"
    PERFORMANCE_METRICS = "performance_metrics"
    SYSTEM_STATUS = "system_status"
    SUBSCRIPTION_CONFIRMED = "subscription_confirmed"
    UNSUBSCRIPTION_CONFIRMED = "unsubscription_confirmed"
    PONG = "pong"

class SubscriptionTopic(str, Enum):
    PROCESS_STATUS = "process_status"
    HEALTH_CHECKS = "health_checks"
    LOG_STREAMS = "log_streams"
    ERROR_ALERTS = "error_alerts"
    PERFORMANCE = "performance"
    SYSTEM = "system"
    ALL = "all"  # Special topic to subscribe to all messages

class WebSocketMessage(BaseModel):
    type: WebSocketMessageType
    timestamp: datetime = datetime.now()
    data: Dict[str, Any]
    topic: Optional[SubscriptionTopic] = None

class SubscriptionMessage(BaseModel):
    type: str = "subscribe"
    topics: List[str]

class UnsubscriptionMessage(BaseModel):
    type: str = "unsubscribe"
    topics: List[str]

class PingMessage(BaseModel):
    type: str = "ping"

class ProcessStatusUpdateMessage(BaseModel):
    type: WebSocketMessageType = WebSocketMessageType.PROCESS_STATUS_UPDATE
    timestamp: datetime = datetime.now()
    process_name: str
    status: str
    pid: Optional[int] = None
    cpu_percent: Optional[float] = None
    memory_mb: Optional[float] = None
    uptime_seconds: Optional[int] = None
    health_score: Optional[float] = None
    connection_status: Optional[str] = None
    last_error: Optional[str] = None

class HealthCheckResultMessage(BaseModel):
    type: WebSocketMessageType = WebSocketMessageType.HEALTH_CHECK_RESULT
    timestamp: datetime = datetime.now()
    process_name: str
    check_type: str
    status: str
    details: Dict[str, Any]
    score: float
    recommendations: List[str] = []

class PerformanceMetricsMessage(BaseModel):
    type: WebSocketMessageType = WebSocketMessageType.PERFORMANCE_METRICS
    timestamp: datetime = datetime.now()
    process_name: str
    cpu_percent: float
    memory_mb: float
    data_points_per_minute: float
    error_rate: float
    response_time_ms: float