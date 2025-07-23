# IoT数采系统模拟设备

## 概述

本目录包含用于IoT数采系统测试的模拟设备服务器实现。支持多种工业协议的设备模拟，用于在没有真实硬件的情况下进行系统测试和验证。

## 支持的设备类型

### 1. Modbus TCP设备
- 文件位置：`modbus/modbus_tcp_server.py`
- 功能：模拟Modbus TCP协议设备
- 支持功能：Holding Registers、Input Registers、Coils、Discrete Inputs
- 数据类型：16位整型、32位整型、浮点型、布尔型

### 2. OPC UA设备
- 文件位置：`opcua/opcua_server.py`
- 功能：模拟OPC UA协议设备
- 支持功能：节点树、数据订阅、历史数据
- 数据类型：所有OPC UA标准数据类型

### 3. 三菱PLC设备
- 文件位置：`mitsubishi/plc_server.py`
- 功能：模拟三菱A1E网络协议设备
- 支持功能：D寄存器、M寄存器、X/Y点位读写
- 数据类型：16位整型、32位浮点型、布尔型

## 使用方法

### 启动单个设备
```bash
# 启动Modbus TCP模拟设备
python modbus/modbus_tcp_server.py

# 启动OPC UA模拟设备
python opcua/opcua_server.py

# 启动三菱PLC模拟设备
python mitsubishi/plc_server.py
```

### 使用Docker启动
```bash
# 构建镜像
docker build -t mock-modbus -f docker/Dockerfile.modbus .
docker build -t mock-opcua -f docker/Dockerfile.opcua .
docker build -t mock-plc -f docker/Dockerfile.plc .

# 启动容器
docker run -p 502:502 mock-modbus
docker run -p 4840:4840 mock-opcua
docker run -p 5021:5021 mock-plc
```

### 使用Docker Compose启动
```bash
# 启动所有模拟设备
docker-compose up mock-modbus mock-opcua mock-plc
```

## 配置文件

每个设备类型都有对应的配置文件：
- `modbus/modbus_config.json` - Modbus TCP设备配置
- `opcua/opcua_config.json` - OPC UA设备配置
- `mitsubishi/plc_config.json` - 三菱PLC设备配置

## 测试

### 运行单元测试
```bash
cd mock-devices
python -m pytest tests/unit/ -v
```

### 运行集成测试
```bash
python -m pytest tests/integration/ -v
```

## 数据生成

模拟设备支持多种数据生成模式：
- **正弦波数据**：模拟连续变化的传感器数据
- **随机数据**：模拟噪声和波动
- **阶跃数据**：模拟开关状态变化
- **自定义函数**：用户自定义数据生成逻辑

## 异常情况模拟

支持以下异常情况的模拟：
- 网络延迟和超时
- 连接断开和重连
- 数据异常和错误值
- 设备故障状态

## 性能测试支持

- 支持大量并发连接（100+设备）
- 支持高频数据更新（1秒级）
- 支持大数据量测试（1000+数据点）
- 内存使用监控和优化 