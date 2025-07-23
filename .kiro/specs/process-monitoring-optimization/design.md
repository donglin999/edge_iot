# Design Document

## Overview

本设计文档描述了IoT数采系统进程监控优化的技术方案。当前系统架构为：frontend → backend → project-data-acquisition → mock-devices，存在进程状态监控不准确、实时性差、错误处理不完善等问题。

本优化方案将在现有架构基础上，增强backend对project-data-acquisition进程的监控能力，改进WebSocket实时通信机制，并提供更准确的进程状态反馈和健康检查功能。

## Architecture

### Current System Architecture
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend       │    │  project-data-acquisition │    │  mock-devices   │
│   (Vue.js)      │◄──►│   (FastAPI)     │◄──►│  (数采进程管理)           │◄──►│  (模拟设备)      │
└─────────────────┘    └─────────────────┘    └─────────────────────────┘    └─────────────────┘
        │                       │                           │                           │
        │                       │                           │                           │
        ▼                       ▼                           ▼                           ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────────────┐    ┌─────────────────┐
│   WebSocket     │    │   SQLite        │    │   InfluxDB              │    │   TCP/UDP       │
│   (实时通信)     │    │   (系统状态)     │    │   (时序数据)             │    │   (协议通信)     │
└─────────────────┘    └─────────────────┘    └─────────────────────────┘    └─────────────────┘
```

### Enhanced Monitoring Architecture
```
┌─────────────────┐    ┌─────────────────────────────────────────────────┐    ┌─────────────────────────┐
│   Frontend      │    │              Backend                            │    │  project-data-acquisition │
│                 │    │  ┌─────────────────┐  ┌─────────────────────┐  │    │                         │
│  - 实时仪表板    │◄──►│  │  Enhanced       │  │  Health Check       │  │◄──►│  - ModbusTCP Collector  │
│  - 进程控制面板  │    │  │  Process        │  │  Service            │  │    │  - OPC UA Collector     │
│  - 日志查看器    │    │  │  Manager        │  │                     │  │    │  - Mitsubishi Collector │
│  - 性能监控图表  │    │  └─────────────────┘  └─────────────────────┘  │    │  - Process Manager      │
└─────────────────┘    │  ┌─────────────────┐  ┌─────────────────────┐  │    └─────────────────────────┘
        │               │  │  WebSocket      │  │  Log Stream         │  │                    │
        │               │  │  Manager        │  │  Service            │  │                    │
        ▼               │  └─────────────────┘  └─────────────────────┘  │                    ▼
┌─────────────────┐    └─────────────────────────────────────────────────┘    ┌─────────────────┐
│   Real-time     │                           │                                │  mock-devices   │
│   Updates       │                           │                                │                 │
└─────────────────┘                           ▼                                │  - Modbus TCP   │
                                    ┌─────────────────┐                        │  - OPC UA       │
                                    │   SQLite +      │                        │  - Mitsubishi   │
                                    │   InfluxDB      │                        │  - Device Mgr   │
                                    │   (监控数据)     │                        └─────────────────┘
                                    └─────────────────┘
```

## Components and Interfaces

### 1. Enhanced Process Manager (backend/core/enhanced_process_manager.py)

#### Core Responsibilities
- 管理project-data-acquisition中的数采进程
- 提供进程启动、停止、重启功能
- 实时监控进程状态和性能指标
- 处理进程崩溃和自动恢复

#### Key Interfaces
```python
class EnhancedProcessManager:
    async def start_process(self, process_name: str, config: dict) -> ProcessResult
    async def stop_process(self, process_name: str) -> ProcessResult
    async def restart_process(self, process_name: str) -> ProcessResult
    async def get_process_status(self, process_name: str) -> ProcessStatus
    async def get_all_processes_status() -> List[ProcessStatus]
    async def monitor_process_health() -> None
    async def handle_process_crash(self, process_name: str) -> None
```

#### Process Status Model
```python
@dataclass
class ProcessStatus:
    name: str
    type: str  # modbus, opcua, mitsubishi
    status: ProcessState  # RUNNING, STOPPED, CRASHED, STARTING, STOPPING
    pid: Optional[int]
    cpu_percent: float
    memory_mb: float
    start_time: Optional[datetime]
    last_heartbeat: Optional[datetime]
    restart_count: int
    last_error: Optional[str]
    connection_status: ConnectionStatus
    data_collection_rate: float
    last_data_time: Optional[datetime]
```

### 2. Health Check Service (backend/services/health_check_service.py)

#### Core Responsibilities
- 定期检查数采进程健康状态
- 监控进程与mock设备的连接状态
- 检测数据采集是否正常
- 提供健康检查报告

#### Health Check Types
```python
class HealthCheckType(Enum):
    PROCESS_ALIVE = "process_alive"      # 进程是否存活
    RESOURCE_USAGE = "resource_usage"    # 资源使用情况
    CONNECTION_STATUS = "connection"     # 设备连接状态
    DATA_FLOW = "data_flow"             # 数据流状态
    LOG_ERRORS = "log_errors"           # 日志错误检查
```

#### Health Check Configuration
```python
@dataclass
class HealthCheckConfig:
    check_interval: int = 30  # 检查间隔(秒)
    cpu_threshold: float = 80.0  # CPU使用率阈值
    memory_threshold: float = 500.0  # 内存使用阈值(MB)
    data_timeout: int = 120  # 数据超时时间(秒)
    connection_timeout: int = 60  # 连接超时时间(秒)
    max_restart_attempts: int = 3  # 最大重启尝试次数
```

### 3. WebSocket Manager Enhancement (backend/core/websocket_manager.py)

#### Enhanced Features
- 支持主题订阅机制
- 实时推送进程状态变化
- 推送健康检查结果
- 推送日志流和错误信息

#### Message Types
```python
class WebSocketMessageType(Enum):
    PROCESS_STATUS_UPDATE = "process_status_update"
    HEALTH_CHECK_RESULT = "health_check_result"
    LOG_STREAM = "log_stream"
    ERROR_ALERT = "error_alert"
    CONNECTION_STATUS = "connection_status"
    PERFORMANCE_METRICS = "performance_metrics"
```

#### Subscription Topics
```python
class SubscriptionTopic(Enum):
    PROCESS_STATUS = "process_status"
    HEALTH_CHECKS = "health_checks"
    LOG_STREAMS = "log_streams"
    ERROR_ALERTS = "error_alerts"
    PERFORMANCE = "performance"
```

### 4. Log Stream Service (backend/services/log_stream_service.py)

#### Core Responsibilities
- 实时读取project-data-acquisition进程日志
- 解析日志内容，提取关键信息
- 通过WebSocket推送日志流
- 提供日志搜索和过滤功能

#### Log Processing Pipeline
```python
class LogProcessor:
    def parse_log_entry(self, log_line: str) -> LogEntry
    def extract_error_info(self, log_entry: LogEntry) -> Optional[ErrorInfo]
    def filter_logs(self, logs: List[LogEntry], filters: LogFilter) -> List[LogEntry]
    def stream_logs(self, process_name: str, websocket_manager: WebSocketManager)
```

### 5. Process Integration Layer (backend/core/process_integration.py)

#### Core Responsibilities
- 与project-data-acquisition进程通信
- 管理进程配置文件
- 处理进程启动参数
- 监控进程输出和错误

#### Integration Methods
```python
class ProcessIntegration:
    def create_process_command(self, process_type: str, config: dict) -> List[str]
    def start_data_acquisition_process(self, command: List[str]) -> subprocess.Popen
    def monitor_process_output(self, process: subprocess.Popen) -> AsyncGenerator[str]
    def send_process_signal(self, pid: int, signal: int) -> bool
    def read_process_config(self, config_path: str) -> dict
    def update_process_config(self, config_path: str, config: dict) -> bool
```

## Data Models

### 1. Process Models Enhancement

```python
# backend/models/process_models.py

@dataclass
class ProcessInfo:
    name: str
    type: str
    status: ProcessState
    pid: Optional[int] = None
    cpu_percent: float = 0.0
    memory_mb: float = 0.0
    start_time: Optional[datetime] = None
    uptime_seconds: int = 0
    restart_count: int = 0
    last_error: Optional[str] = None
    config_file: Optional[str] = None
    command: List[str] = field(default_factory=list)
    # 新增字段
    last_heartbeat: Optional[datetime] = None
    connection_status: ConnectionStatus = ConnectionStatus.UNKNOWN
    data_collection_rate: float = 0.0
    last_data_time: Optional[datetime] = None
    health_score: float = 100.0
    error_count_24h: int = 0

@dataclass
class ConnectionStatus:
    device_ip: str
    device_port: int
    is_connected: bool
    last_connect_time: Optional[datetime]
    connection_errors: int
    protocol_type: str  # modbus, opcua, mitsubishi

@dataclass
class PerformanceMetrics:
    process_name: str
    timestamp: datetime
    cpu_percent: float
    memory_mb: float
    data_points_per_minute: float
    error_rate: float
    response_time_ms: float
```

### 2. Health Check Models

```python
# backend/models/health_models.py

@dataclass
class HealthCheckResult:
    process_name: str
    check_type: HealthCheckType
    status: HealthStatus
    timestamp: datetime
    details: dict
    score: float  # 0-100
    recommendations: List[str]

@dataclass
class SystemHealthSummary:
    overall_status: HealthStatus
    total_processes: int
    healthy_processes: int
    warning_processes: int
    critical_processes: int
    last_check_time: datetime
    issues: List[HealthIssue]
```

### 3. Log Models

```python
# backend/models/log_models.py

@dataclass
class LogEntry:
    timestamp: datetime
    level: LogLevel
    process_name: str
    message: str
    source_file: Optional[str]
    line_number: Optional[int]
    exception_info: Optional[str]

@dataclass
class ErrorInfo:
    error_type: str
    error_message: str
    timestamp: datetime
    process_name: str
    severity: ErrorSeverity
    context: dict
    suggested_action: Optional[str]
```

## Error Handling

### 1. Process Error Categories

```python
class ProcessErrorType(Enum):
    STARTUP_FAILURE = "startup_failure"
    CONNECTION_ERROR = "connection_error"
    DATA_COLLECTION_ERROR = "data_collection_error"
    RESOURCE_EXHAUSTION = "resource_exhaustion"
    CONFIGURATION_ERROR = "configuration_error"
    UNEXPECTED_TERMINATION = "unexpected_termination"
```

### 2. Error Recovery Strategies

```python
class ErrorRecoveryStrategy:
    def handle_startup_failure(self, process_name: str, error: Exception) -> RecoveryAction
    def handle_connection_error(self, process_name: str, connection_info: dict) -> RecoveryAction
    def handle_data_collection_error(self, process_name: str, error_details: dict) -> RecoveryAction
    def handle_resource_exhaustion(self, process_name: str, resource_info: dict) -> RecoveryAction
```

### 3. Automatic Recovery Actions

```python
class RecoveryAction(Enum):
    RESTART_PROCESS = "restart_process"
    RESET_CONNECTION = "reset_connection"
    CLEAR_CACHE = "clear_cache"
    REDUCE_FREQUENCY = "reduce_frequency"
    ALERT_OPERATOR = "alert_operator"
    NO_ACTION = "no_action"
```

## Testing Strategy

### 1. Unit Testing

#### Process Manager Tests
- 进程启动/停止/重启功能测试
- 进程状态监控测试
- 错误处理和恢复测试
- 配置管理测试

#### Health Check Tests
- 各种健康检查类型测试
- 阈值检测测试
- 健康评分计算测试
- 恢复策略测试

#### WebSocket Tests
- 连接管理测试
- 消息推送测试
- 订阅机制测试
- 错误处理测试

### 2. Integration Testing

#### Process Integration Tests
- backend与project-data-acquisition集成测试
- 进程通信测试
- 配置文件管理测试
- 日志流处理测试

#### End-to-End Tests
- 完整数据流测试：frontend → backend → project-data-acquisition → mock-devices
- 进程故障恢复测试
- 实时监控功能测试
- 用户操作流程测试

### 3. Performance Testing

#### Load Testing
- 多进程并发监控测试
- WebSocket连接压力测试
- 日志流处理性能测试
- 数据库查询性能测试

#### Stress Testing
- 进程频繁重启测试
- 大量错误日志处理测试
- 长时间运行稳定性测试
- 资源使用极限测试

## Implementation Plan

### Phase 1: Core Infrastructure (Week 1-2)
1. 实现EnhancedProcessManager基础功能
2. 创建进程状态数据模型
3. 建立与project-data-acquisition的通信机制
4. 实现基础的进程启动/停止功能

### Phase 2: Health Monitoring (Week 3-4)
1. 实现HealthCheckService
2. 添加各种健康检查类型
3. 实现健康评分算法
4. 创建健康检查报告功能

### Phase 3: Real-time Communication (Week 5-6)
1. 增强WebSocketManager功能
2. 实现主题订阅机制
3. 添加实时状态推送
4. 实现日志流服务

### Phase 4: Frontend Integration (Week 7-8)
1. 更新前端进程监控界面
2. 实现实时状态显示
3. 添加进程控制功能
4. 创建健康监控仪表板

### Phase 5: Testing and Optimization (Week 9-10)
1. 完成单元测试和集成测试
2. 进行性能优化
3. 修复发现的问题
4. 完善文档和部署指南

## Security Considerations

### 1. Process Control Security
- 进程操作权限验证
- 命令注入防护
- 配置文件访问控制
- 操作日志记录

### 2. WebSocket Security
- 连接认证机制
- 消息内容验证
- 频率限制
- 异常连接检测

### 3. Log Security
- 敏感信息过滤
- 日志访问权限
- 日志完整性保护
- 审计跟踪

## Performance Optimization

### 1. Process Monitoring Optimization
- 批量状态查询
- 缓存机制
- 异步处理
- 资源使用优化

### 2. WebSocket Optimization
- 连接池管理
- 消息压缩
- 批量推送
- 断线重连优化

### 3. Database Optimization
- 索引优化
- 查询优化
- 数据分区
- 定期清理

## Monitoring and Alerting

### 1. System Monitoring
- 进程监控服务自身的监控
- 资源使用监控
- 性能指标监控
- 错误率监控

### 2. Alert Configuration
- 进程状态告警
- 性能阈值告警
- 连接状态告警
- 数据流异常告警

### 3. Notification Channels
- WebSocket实时通知
- 邮件告警
- 日志记录
- 外部系统集成