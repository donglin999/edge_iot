# IoT数采系统界面方案设计

## 项目概述

### 背景
现有的IoT数采系统是一个基于Excel配置驱动的纯脚本执行软件，支持多种工业协议（Modbus TCP、OPC UA、三菱PLC等）的数据采集。现需要为此系统设计一个Web界面，用于：
- 监控所有数据采集进程状态
- 实时查看数据库测点数据
- 管理Excel配置文件
- 提供数据查看和分析功能

### 技术栈选择
- **部署方式**: docker-compose和docker打包
- **后端框架**: FastAPI
- **前端框架**: Vue.js 3 + Element Plus
- **数据库**: InfluxDB (时序数据) + SQLite (系统状态)
- **实时通信**: WebSocket
- **反向代理**: nginx
- **部署**: Docker + Docker Compose
- **测试框架**: pytest (后端) + Vitest (前端)
- **代码覆盖率**: coverage.py (后端) + c8 (前端)
- **API测试**: httpx + pytest-asyncio
- **E2E测试**: Playwright

## 系统架构设计

### 整体架构
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Vue.js前端    │    │   FastAPI后端   │    │   现有数采系统   │
│   (用户界面)    │◄──►│   (API服务)     │◄──►│   (进程管理)     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
        │                       │                       │
        │                       │                       │
        ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   WebSocket     │    │   InfluxDB   │    │   InfluxDB      │
│   (实时通信)    │    │   (时序数据)     │    │   (时序数据)     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### 网络架构
```
用户浏览器 → nginx (80/443) → FastAPI (8000) → 现有数采系统
                ↓
           静态文件服务 (Vue.js构建文件)
```

## 后端架构设计

### 目录结构
```
api/
├── main.py                 # FastAPI应用入口
├── routers/               # 路由模块
│   ├── __init__.py
│   ├── processes.py       # 进程管理API
│   ├── data.py           # 数据查询API
│   ├── config.py         # 配置管理API
│   ├── system.py         # 系统监控API
│   └── websocket.py      # WebSocket实时通信
├── services/             # 业务逻辑服务
│   ├── __init__.py
│   ├── process_service.py    # 进程管理服务
│   ├── data_service.py      # 数据查询服务
│   ├── config_service.py    # 配置管理服务
│   └── monitor_service.py   # 系统监控服务
├── models/               # 数据模型
│   ├── __init__.py
│   ├── process_models.py    # 进程相关模型
│   ├── data_models.py      # 数据相关模型
│   └── config_models.py    # 配置相关模型
├── core/                 # 核心功能
│   ├── __init__.py
│   ├── database.py         # 数据库连接
│   ├── websocket_manager.py # WebSocket管理
│   └── integration.py      # 与现有系统集成
├── tests/                # 测试目录
│   ├── __init__.py
│   ├── conftest.py         # pytest配置文件
│   ├── fixtures/           # 测试数据夹具
│   │   ├── __init__.py
│   │   ├── process_fixtures.py
│   │   ├── data_fixtures.py
│   │   └── config_fixtures.py
│   ├── unit/              # 单元测试
│   │   ├── __init__.py
│   │   ├── test_services/    # 服务层测试
│   │   │   ├── __init__.py
│   │   │   ├── test_process_service.py
│   │   │   ├── test_data_service.py
│   │   │   ├── test_config_service.py
│   │   │   └── test_monitor_service.py
│   │   ├── test_models/      # 模型测试
│   │   │   ├── __init__.py
│   │   │   ├── test_process_models.py
│   │   │   ├── test_data_models.py
│   │   │   └── test_config_models.py
│   │   └── test_core/        # 核心功能测试
│   │       ├── __init__.py
│   │       ├── test_database.py
│   │       ├── test_websocket_manager.py
│   │       └── test_integration.py
│   ├── integration/        # 集成测试
│   │   ├── __init__.py
│   │   ├── test_api_endpoints.py
│   │   ├── test_websocket_integration.py
│   │   ├── test_database_integration.py
│   │   └── test_process_integration.py
│   ├── e2e/               # 端到端测试
│   │   ├── __init__.py
│   │   ├── test_user_workflows.py
│   │   ├── test_system_scenarios.py
│   │   └── test_performance.py
│   └── utils/             # 测试工具
│       ├── __init__.py
│       ├── test_helpers.py
│       ├── mock_data.py
│       └── test_client.py
├── static/               # 静态文件
│   └── frontend/         # Vue.js构建文件
├── pytest.ini           # pytest配置
├── requirements-test.txt # 测试依赖
└── .coveragerc          # 覆盖率配置
```

### 核心API接口

#### 进程管理API
```python
GET    /api/processes              # 获取所有进程状态
POST   /api/processes/start        # 启动进程
POST   /api/processes/stop         # 停止进程
POST   /api/processes/restart      # 重启进程
GET    /api/processes/{pid}/status # 获取特定进程状态
GET    /api/processes/{pid}/logs   # 获取进程日志
```

#### 数据查询API
```python
GET    /api/data/realtime         # 获取实时数据
GET    /api/data/history          # 获取历史数据
GET    /api/data/statistics       # 获取数据统计
GET    /api/data/devices          # 获取设备列表
GET    /api/data/measurements     # 获取测量点列表
```

#### 配置管理API
```python
POST   /api/config/upload         # 上传Excel配置
GET    /api/config/current        # 获取当前配置
GET    /api/config/history        # 获取配置历史
POST   /api/config/apply          # 应用新配置
GET    /api/config/validate       # 验证配置文件
```

#### 系统监控API
```python
GET    /api/system/status         # 获取系统状态
GET    /api/system/health         # 健康检查
GET    /api/system/metrics        # 获取系统指标
GET    /api/system/logs           # 获取系统日志
```

### 与现有系统集成

#### 进程管理集成
- **扩展ProcessManager**: 在现有进程管理器基础上添加API接口
- **状态监控**: 获取进程PID、类型、运行状态、资源使用情况
- **进程控制**: 提供启动、停止、重启进程的API接口
- **性能监控**: 集成CPU、内存使用率监控
- **日志管理**: 统一进程日志收集和查看

#### 数据查询集成
- **InfluxDB连接**: 复用现有的数据库连接配置
- **实时数据获取**: 构建Flux查询语句获取最新数据
- **历史数据查询**: 支持时间范围、设备过滤的数据查询
- **数据格式化**: 统一数据返回格式，便于前端展示
- **查询优化**: 支持数据分页、缓存机制

#### WebSocket实时通信
- **连接管理**: 管理多个客户端连接，支持连接池
- **数据推送**: 定时推送进程状态和实时数据
- **消息分发**: 根据客户端订阅内容分发相应数据
- **异常处理**: 连接断开重连、推送失败处理
- **性能优化**: 避免重复数据推送，减少网络开销

## 前端架构设计

### 目录结构
```
frontend/
├── src/
│   ├── main.js              # 应用入口
│   ├── App.vue              # 根组件
│   ├── router/              # 路由配置
│   │   └── index.js
│   ├── store/               # Vuex状态管理
│   │   ├── index.js
│   │   ├── modules/
│   │   │   ├── processes.js    # 进程状态管理
│   │   │   ├── data.js        # 数据状态管理
│   │   │   └── config.js      # 配置状态管理
│   ├── components/          # 公共组件
│   │   ├── charts/          # 图表组件
│   │   ├── process/         # 进程相关组件
│   │   ├── data/           # 数据展示组件
│   │   └── config/         # 配置管理组件
│   ├── views/              # 页面组件
│   │   ├── Dashboard.vue      # 仪表盘
│   │   ├── ProcessMonitor.vue # 进程监控
│   │   ├── DataViewer.vue     # 数据查看
│   │   ├── ConfigManager.vue  # 配置管理
│   │   └── SystemMonitor.vue  # 系统监控
│   ├── services/           # API服务
│   │   ├── api.js            # API基础配置
│   │   ├── processApi.js     # 进程API
│   │   ├── dataApi.js       # 数据API
│   │   └── configApi.js     # 配置API
│   └── utils/              # 工具函数
│       ├── websocket.js      # WebSocket管理
│       ├── charts.js        # 图表工具
│       └── formatter.js     # 数据格式化
├── tests/                  # 测试目录
│   ├── setup.js            # 测试设置文件
│   ├── __mocks__/          # 模拟对象
│   │   ├── api.js
│   │   ├── websocket.js
│   │   └── localStorage.js
│   ├── unit/               # 单元测试
│   │   ├── components/     # 组件测试
│   │   │   ├── charts/
│   │   │   │   ├── RealTimeChart.test.js
│   │   │   │   ├── ProcessStatusChart.test.js
│   │   │   │   └── DataTable.test.js
│   │   │   ├── process/
│   │   │   │   ├── ProcessCard.test.js
│   │   │   │   └── ProcessList.test.js
│   │   │   ├── data/
│   │   │   │   ├── DataFilter.test.js
│   │   │   │   └── DataExport.test.js
│   │   │   └── config/
│   │   │       ├── ConfigUpload.test.js
│   │   │       └── ConfigValidator.test.js
│   │   ├── views/          # 页面测试
│   │   │   ├── Dashboard.test.js
│   │   │   ├── ProcessMonitor.test.js
│   │   │   ├── DataViewer.test.js
│   │   │   ├── ConfigManager.test.js
│   │   │   └── SystemMonitor.test.js
│   │   ├── store/          # 状态管理测试
│   │   │   ├── processes.test.js
│   │   │   ├── data.test.js
│   │   │   └── config.test.js
│   │   ├── services/       # API服务测试
│   │   │   ├── processApi.test.js
│   │   │   ├── dataApi.test.js
│   │   │   └── configApi.test.js
│   │   └── utils/          # 工具函数测试
│   │       ├── websocket.test.js
│   │       ├── charts.test.js
│   │       └── formatter.test.js
│   ├── integration/        # 集成测试
│   │   ├── api-integration.test.js
│   │   ├── websocket-integration.test.js
│   │   └── router-integration.test.js
│   ├── e2e/               # 端到端测试
│   │   ├── dashboard.e2e.js
│   │   ├── process-monitor.e2e.js
│   │   ├── data-viewer.e2e.js
│   │   ├── config-manager.e2e.js
│   │   └── user-workflows.e2e.js
│   └── utils/             # 测试工具
│       ├── test-helpers.js
│       ├── mock-data.js
│       └── test-utils.js
├── public/
│   └── index.html
├── package.json
├── vite.config.js
├── vitest.config.js       # Vitest配置
└── playwright.config.js   # Playwright配置
```

### 核心组件设计

#### 仪表盘组件
- **系统状态概览**: 展示运行进程数、数据测点、数据速率、系统状态
- **实时数据图表**: 集成ECharts显示实时数据趋势和进程状态
- **最新数据表格**: 展示最新采集的数据记录
- **WebSocket集成**: 实时接收后端推送的状态和数据更新
- **响应式设计**: 适配不同屏幕尺寸，提供良好的用户体验

#### 进程监控组件
- **进程控制面板**: 提供批量启动、停止、重启所有进程的操作
- **进程状态列表**: 表格形式展示进程详细信息（PID、类型、状态、资源使用）
- **单进程操作**: 支持对单个进程的启动、停止、重启操作
- **状态标识**: 使用颜色和图标清晰显示进程运行状态
- **定时刷新**: 自动刷新进程状态，保持数据同步

#### WebSocket管理
- **连接管理**: 自动建立和维护WebSocket连接
- **消息处理**: 根据消息类型分发到相应的处理函数
- **重连机制**: 连接断开时自动重连，提高系统稳定性
- **事件订阅**: 支持组件订阅特定类型的实时消息
- **错误处理**: 完善的错误处理和日志记录机制

## 功能模块设计

### 1. 进程监控模块
- **实时进程状态显示**：PID、类型、状态、CPU使用率、内存使用率
- **进程控制**：启动、停止、重启单个或所有进程
- **进程日志查看**：实时日志流和历史日志查询
- **进程性能监控**：CPU、内存使用趋势图

### 2. 数据监控模块
- **实时数据展示**：支持折线图、柱状图、仪表盘等多种图表
- **历史数据查询**：时间范围选择、设备过滤、数据导出
- **测点管理**：测点列表、状态监控、异常报警
- **数据统计**：数据量统计、采集频率分析

### 3. 配置管理模块
- **Excel文件上传**：支持拖拽上传、文件预览
- **配置验证**：数据格式检查、字段完整性验证
- **配置对比**：新旧配置差异对比
- **配置应用**：一键应用新配置、回滚功能

### 4. 系统管理模块
- **系统状态监控**：CPU、内存、磁盘使用情况
- **服务状态监控**：InfluxDB连接状态、数据库健康检查
- **日志管理**：系统日志查看、日志级别设置
- **用户权限管理**：用户登录、权限控制

## 单测架构设计

### 测试策略

#### 测试金字塔
```
        E2E 测试
      ┌─────────────┐
      │   少量      │  - 用户工作流测试
      │  复杂场景   │  - 系统集成测试
      └─────────────┘
    
    集成测试
  ┌─────────────────┐
  │   中等数量      │  - API集成测试
  │  接口交互测试   │  - 数据库集成测试
  └─────────────────┘

单元测试
┌─────────────────────┐
│    大量            │  - 组件测试
│ 快速、独立、可靠   │  - 服务测试
└─────────────────────┘
```

#### 测试覆盖率目标
- **单元测试覆盖率**: ≥ 80%
- **集成测试覆盖率**: ≥ 60%
- **E2E测试覆盖率**: ≥ 40%
- **总体代码覆盖率**: ≥ 85%

### 后端测试架构

#### 测试工具选择
- **测试框架**: pytest
- **异步测试**: pytest-asyncio
- **HTTP客户端**: httpx
- **Mock框架**: unittest.mock + pytest-mock
- **覆盖率工具**: coverage.py
- **测试数据库**: SQLite (内存)
- **测试数据生成**: factory_boy

#### 测试配置

**核心配置要点**：
- **测试路径**: 统一测试文件路径和命名规范
- **覆盖率要求**: 设置最低覆盖率阈值（80%）
- **测试标记**: 使用标记区分不同类型测试
- **异步支持**: 配置异步测试环境
- **报告生成**: HTML和控制台覆盖率报告

**依赖管理**：
- **核心框架**: pytest作为主要测试框架
- **异步测试**: pytest-asyncio支持异步操作
- **HTTP测试**: httpx作为异步HTTP客户端
- **Mock功能**: pytest-mock提供Mock能力
- **数据生成**: factory-boy和faker生成测试数据

#### 测试设计要点

**测试夹具管理**：
- **数据库夹具**: 使用内存SQLite创建独立测试环境
- **客户端夹具**: 提供同步和异步HTTP测试客户端
- **Mock对象**: 模拟外部依赖（进程管理器、数据库、WebSocket）
- **作用域控制**: 合理设置夹具作用域，优化测试性能

**服务层测试策略**：
- **隔离测试**: 使用Mock隔离外部依赖
- **AAA模式**: Arrange-Act-Assert测试结构
- **异步测试**: 支持异步服务方法测试
- **集成测试**: 测试服务间交互
- **边界测试**: 覆盖异常情况和边界条件

**API端点测试**：
- **HTTP接口**: 测试所有REST API端点
- **参数验证**: 验证请求参数和响应格式
- **状态码**: 确保正确的HTTP状态码返回
- **WebSocket**: 测试实时通信功能
- **认证授权**: 验证安全机制

### 前端测试架构

#### 测试工具选择
- **测试框架**: Vitest
- **组件测试**: @vue/test-utils
- **E2E测试**: Playwright
- **Mock库**: vitest/mock
- **覆盖率工具**: c8
- **测试环境**: jsdom

#### 测试配置

**Vitest配置要点**：
- **测试环境**: 使用jsdom模拟浏览器环境
- **覆盖率设置**: 设定80%的覆盖率阈值
- **全局配置**: 启用全局测试API
- **路径别名**: 配置@指向src目录
- **报告格式**: 支持多种覆盖率报告格式

**Playwright配置要点**：
- **多浏览器**: 支持Chrome、Firefox、Safari测试
- **并行执行**: 提高测试执行效率
- **失败处理**: 自动截图和录像
- **重试机制**: CI环境自动重试失败测试
- **Web服务器**: 自动启动本地服务器

#### 测试设计要点

**测试环境设置**：
- **全局Mock**: 配置路由、国际化、WebSocket等全局Mock
- **组件注册**: 注册测试环境需要的全局组件
- **浏览器API**: Mock window对象和浏览器API
- **第三方库**: Mock ECharts、Element Plus等第三方库

**组件测试策略**：
- **渲染测试**: 验证组件正确渲染
- **Props测试**: 测试组件属性传递和响应
- **事件测试**: 验证用户交互和事件触发
- **生命周期**: 测试组件挂载、更新、销毁过程
- **异步操作**: 测试异步数据加载和状态更新

**服务测试设计**：
- **HTTP请求**: Mock fetch API测试HTTP调用
- **错误处理**: 验证网络错误和API错误处理
- **数据格式**: 确保API返回数据格式正确
- **参数验证**: 测试请求参数构建和验证
- **缓存机制**: 测试数据缓存和失效逻辑

**E2E测试场景**：
- **用户工作流**: 模拟完整的用户操作流程
- **页面导航**: 测试路由跳转和页面加载
- **实时功能**: 验证WebSocket实时数据更新
- **交互操作**: 测试按钮点击、表单提交等操作
- **跨浏览器**: 确保在不同浏览器中正常工作

### 测试执行和CI/CD

#### 测试命令
```bash
# 后端测试
pytest                          # 运行所有测试
pytest -m unit                  # 运行单元测试
pytest -m integration          # 运行集成测试
pytest -m e2e                  # 运行E2E测试
pytest --cov                   # 运行测试并生成覆盖率报告

# 前端测试
npm run test                    # 运行单元测试
npm run test:coverage          # 运行测试并生成覆盖率报告
npm run test:e2e               # 运行E2E测试
npm run test:watch             # 监视模式运行测试
```

#### CI/CD配置

**自动化测试流程**：
- **触发条件**: 代码推送和Pull Request自动触发
- **并行执行**: 前后端测试并行运行，提高效率
- **环境隔离**: 每个作业使用独立的运行环境
- **依赖服务**: 自动启动InfluxDB等测试依赖服务
- **结果报告**: 自动生成测试报告和覆盖率报告

**后端测试流程**：
- **环境准备**: 设置Python环境和依赖安装
- **服务启动**: 启动测试所需的数据库服务
- **测试执行**: 运行单元测试、集成测试、E2E测试
- **覆盖率收集**: 生成代码覆盖率报告
- **结果上传**: 上传覆盖率数据到代码质量平台

**前端测试流程**：
- **环境准备**: 设置Node.js环境和依赖安装
- **单元测试**: 运行组件和服务的单元测试
- **构建验证**: 验证生产构建过程
- **E2E测试**: 运行端到端用户场景测试
- **多浏览器**: 在不同浏览器中验证兼容性

### 测试数据管理

#### 测试数据生成策略
- **工厂模式**: 使用Factory Boy创建可重复的测试数据
- **随机数据**: 集成Faker库生成真实性随机数据
- **数据模型**: 为不同业务对象定义数据工厂
- **关联数据**: 支持有关联关系的复杂数据生成
- **数据清理**: 测试结束后自动清理生成的数据

#### Mock数据设计
- **静态数据**: 预定义常用的测试数据集
- **动态生成**: 根据测试需要动态生成数据
- **数据格式**: 确保Mock数据与真实API格式一致
- **边界情况**: 包含异常和边界情况的测试数据
- **可维护性**: 集中管理Mock数据，便于更新维护

### 测试最佳实践

#### 核心测试原则
- **独立性**: 每个测试独立运行，不依赖其他测试的执行顺序
- **可重复性**: 在任何环境下都能得到一致的测试结果
- **快速性**: 单元测试执行速度要快，提供即时反馈
- **可读性**: 测试代码清晰易懂，便于理解和维护
- **可维护性**: 测试代码结构良好，易于修改和扩展

#### 测试组织规范
- **命名约定**: 统一的文件、类、方法命名规范
- **目录结构**: 清晰的测试目录组织结构
- **分层测试**: 单元、集成、E2E测试层次分明
- **标记分类**: 使用标记区分不同类型和用途的测试

#### 测试编写模式
- **AAA模式**: Arrange-Act-Assert标准测试结构
- **Given-When-Then**: BDD风格的测试描述
- **单一职责**: 每个测试只验证一个功能点
- **边界测试**: 覆盖正常、异常、边界情况

## 部署方案

### 开发环境
**快速启动流程**：
  全部启用docker-compose去进行部署启动，且需要挂载到本地路径

### 生产环境架构

#### nginx反向代理配置
**核心功能**：
- **静态文件服务**: 高效处理前端资源文件
- **API代理**: 转发API请求到FastAPI后端
- **WebSocket代理**: 支持实时通信连接
- **压缩优化**: 启用gzip压缩减少传输数据
- **缓存策略**: 设置适当的静态资源缓存策略
- **SSL支持**: 配置HTTPS安全连接

#### 容器化部署
**服务组件**：
- **FastAPI服务**: 后端API和WebSocket服务
- **nginx服务**: 反向代理和静态文件服务
- **InfluxDB服务**: 时序数据库存储
- **数据持久化**: 使用数据卷保证数据安全
- **环境配置**: 通过环境变量管理配置

**部署优势**：
- **一键部署**: Docker Compose简化部署流程
- **环境一致**: 容器确保开发和生产环境一致
- **扩展性**: 支持水平扩展和负载均衡
- **监控**: 容器状态监控和自动重启

### 部署流程

#### 环境准备
- **系统要求**: Ubuntu 20.04+，Docker，Docker Compose
- **资源要求**: 最小2GB内存，20GB磁盘空间
- **网络配置**: 开放80、443、8000、8086端口
- **权限设置**: 配置适当的用户权限和文件权限

#### 应用部署
- **代码获取**: 从版本控制系统获取最新代码
- **依赖安装**: 安装前后端依赖包
- **构建打包**: 构建生产版本的前端应用
- **服务启动**: 使用Docker Compose启动所有服务
- **配置验证**: 验证各服务启动状态和连接性

#### 配置管理
- **nginx配置**: 设置反向代理规则和SSL证书
- **环境变量**: 配置数据库连接和安全密钥
- **日志配置**: 设置日志输出路径和级别
- **监控设置**: 配置系统监控和告警

## 安全考虑

### 1. 认证授权
- 实现JWT基础的用户认证
- 角色权限管理
- API访问权限控制

### 2. 数据安全
- 敏感数据加密存储
- 数据传输HTTPS加密
- 定期数据备份

### 3. 系统安全
- 防止SQL注入
- XSS攻击防护
- CSRF防护
- 输入验证和过滤

## 性能优化

### 1. 前端优化
- 代码分割和懒加载
- 静态资源压缩和缓存
- 图片优化和WebP格式
- 虚拟滚动处理大量数据

### 2. 后端优化
- 数据库连接池
- 缓存策略（Redis）
- 异步处理
- 数据分页和过滤

### 3. 部署优化
- nginx缓存配置
- CDN加速
- 负载均衡
- 数据库优化

## 监控和运维

### 1. 应用监控
- 进程状态监控
- 性能指标收集
- 异常报警
- 日志分析

### 2. 系统监控
- 系统资源监控
- 网络监控
- 服务可用性监控
- 数据库监控

### 3. 运维工具
- 自动化部署
- 配置管理
- 备份恢复
- 故障处理


## 总结

本方案提供了一个完整的IoT数采系统Web界面解决方案，具有以下优势：

1. **技术先进**：使用FastAPI + Vue.js现代化技术栈
2. **性能优秀**：WebSocket实时通信，nginx反向代理
3. **功能完善**：进程监控、数据可视化、配置管理、系统监控
4. **部署简单**：Docker容器化，一键部署
5. **扩展性强**：模块化设计，便于后续扩展
6. **安全可靠**：完整的安全机制和监控体系
7. **测试完备**：完整的单测架构，保证代码质量
8. **质量保障**：高覆盖率测试，CI/CD自动化

### 测试架构优势

- **全面覆盖**：单元测试、集成测试、E2E测试三层测试体系
- **自动化程度高**：CI/CD集成，代码提交即触发测试
- **质量可控**：覆盖率要求，确保代码质量
- **快速反馈**：分层测试，快速定位问题
- **可维护性强**：测试代码规范，易于维护和扩展

该方案能够满足IoT数采系统的界面需求，为用户提供直观、高效的数据监控和管理体验，同时通过完备的测试架构确保系统的可靠性和可维护性。 