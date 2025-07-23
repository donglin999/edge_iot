# IoT数采系统模拟设备

## 📋 概述

本模块提供了完整的IoT设备模拟功能，用于在没有真实硬件的情况下进行IoT数采系统的开发、测试和演示。支持多种工业通信协议，提供真实的数据变化模拟。

## 🎯 支持的设备类型

### 1. Modbus TCP设备
- **协议支持**：完整的Modbus TCP协议实现
- **功能码支持**：
  - 0x01: 读线圈
  - 0x02: 读离散输入
  - 0x03: 读保持寄存器
  - 0x04: 读输入寄存器
  - 0x05: 写单个线圈
  - 0x06: 写单个寄存器
  - 0x0F: 写多个线圈
  - 0x10: 写多个寄存器
- **数据区域**：支持10000+个寄存器和线圈
- **默认端口**：502

### 2. OPC UA设备
- **协议支持**：OPC UA服务器实现
- **功能特性**：
  - 自定义命名空间
  - 多种数据类型（Double, Boolean, Int32, Float等）
  - 节点树结构
  - 数据订阅（如果支持asyncua库）
- **模拟模式**：无需asyncua库也可运行
- **默认端口**：4840

### 3. 三菱PLC设备
- **协议支持**：三菱A1E网络协议
- **PLC型号**：FX3U系列模拟
- **存储区域**：
  - D寄存器：数据寄存器
  - M继电器：中间继电器
  - X输入：输入点位
  - Y输出：输出点位
  - T定时器、C计数器
- **默认端口**：5001

### 4. 设备管理器
- **功能**：统一管理所有模拟设备
- **特性**：
  - 设备状态监控
  - 批量启动/停止
  - 配置文件管理
  - 健康检查
- **默认端口**：8080

## 🚀 快速开始

### 方式一：使用启动脚本（推荐）

```bash
# 1. 运行启动脚本
./start_mock_devices.sh

# 2. 根据提示操作
# - 检查Docker环境
# - 选择是否重新构建镜像
# - 自动启动所有设备
# - 显示设备状态和连接信息
```

### 方式二：使用Docker Compose

```bash
# 1. 启动所有模拟设备
docker-compose up -d mock-modbus mock-opcua mock-plc mock-device-manager

# 2. 查看设备状态
docker-compose ps

# 3. 查看设备日志
docker-compose logs -f mock-modbus
docker-compose logs -f mock-opcua
docker-compose logs -f mock-plc
docker-compose logs -f mock-device-manager

# 4. 停止设备
docker-compose down
```

### 方式三：直接运行Python脚本

```bash
# 1. 安装依赖
cd mock-devices
pip install -r requirements.txt

# 2. 启动单个设备
python modbus/modbus_tcp_server.py
python opcua/opcua_server.py
python mitsubishi/plc_server.py

# 3. 启动设备管理器
python common/device_manager.py
```

## 📊 数据生成器

### 支持的数据生成类型

1. **正弦波生成器 (sine)**
   ```json
   {
     "type": "sine",
     "amplitude": 1000,      // 振幅
     "frequency": 0.1,       // 频率 (Hz)
     "offset": 2000,         // 偏移量
     "phase": 0,             // 相位 (弧度)
     "addresses": [0, 1, 2]  // 应用的地址
   }
   ```

2. **随机数生成器 (random)**
   ```json
   {
     "type": "random",
     "min_value": 0,         // 最小值
     "max_value": 4095,      // 最大值
     "data_type": "int",     // 数据类型: int, float
     "addresses": [10, 11, 12]
   }
   ```

3. **阶跃生成器 (step)**
   ```json
   {
     "type": "step",
     "values": [true, false, true],  // 阶跃值序列
     "step_interval": 5.0,           // 阶跃间隔 (秒)
     "addresses": [20]
   }
   ```

4. **线性变化生成器 (linear)**
   ```json
   {
     "type": "linear",
     "start_value": 0,       // 起始值
     "end_value": 4095,      // 结束值
     "duration": 30.0,       // 持续时间 (秒)
     "repeat": true,         // 是否重复
     "addresses": [50, 51]
   }
   ```

5. **复合生成器 (composite)**
   ```json
   {
     "type": "composite",
     "generators": [
       // 包含多个子生成器的配置
     ]
   }
   ```

## 🔧 配置文件

### Modbus TCP设备配置
文件：`mock-devices/modbus/modbus_config.json`

```json
{
  "device_id": "modbus_tcp_001",
  "device_name": "Modbus TCP模拟设备",
  "host": "0.0.0.0",
  "port": 502,
  "unit_id": 1,
  "data_areas": {
    "coil_count": 1000,
    "input_register_count": 1000,
    "holding_register_count": 1000
  },
  "data_generator": {
    "type": "composite",
    "generators": [
      // 生成器配置
    ]
  }
}
```

### OPC UA设备配置
文件：`mock-devices/opcua/opcua_config.json`

```json
{
  "device_id": "opcua_device_001",
  "port": 4840,
  "server_settings": {
    "server_name": "IoT Mock OPC UA Server",
    "namespace": "http://mock.iot.device/opcua001"
  },
  "nodes": [
    {
      "name": "Temperature",
      "data_type": "Double",
      "initial_value": 25.0,
      "unit": "°C",
      "description": "环境温度传感器"
    }
  ]
}
```

### 三菱PLC设备配置
文件：`mock-devices/mitsubishi/plc_config.json`

```json
{
  "device_id": "mitsubishi_plc_001",
  "port": 5001,
  "plc_settings": {
    "plc_type": "FX3U",
    "protocol": "A1E"
  },
  "memory_layout": {
    "d_register_count": 8000,
    "m_relay_count": 8000
  }
}
```

## 🧪 测试和验证

### 运行单元测试

```bash
# 进入模拟设备目录
cd mock-devices

# 运行所有测试
python -m pytest tests/ -v

# 运行特定测试
python -m pytest tests/unit/test_modbus_server.py -v
python -m pytest tests/unit/test_opcua_server.py -v
```

### 手动测试连接

#### 测试Modbus TCP设备
```bash
# 使用telnet测试连接
telnet localhost 502

# 使用Python测试
python -c "
import socket
s = socket.socket()
s.connect(('localhost', 502))
print('Modbus TCP连接成功')
s.close()
"
```

#### 测试OPC UA设备
```bash
# 测试端口连接
telnet localhost 4840

# 如果安装了opcua客户端工具
# opcua-client opc.tcp://localhost:4840/freeopcua/server/
```

#### 测试三菱PLC设备
```bash
# 测试端口连接
telnet localhost 5001
```

#### 测试设备管理器
```bash
# 测试Web接口
curl http://localhost:8080/health

# 获取设备状态
curl http://localhost:8080/devices/status
```

## 📱 监控和管理

### 设备状态监控

```bash
# 查看所有容器状态
docker-compose ps

# 查看设备健康状态
docker-compose exec mock-device-manager python -c "
from common.device_manager import DeviceManager
manager = DeviceManager('config.json')
print(manager.get_all_devices_status())
"
```

### 日志查看

```bash
# 实时查看所有设备日志
docker-compose logs -f

# 查看特定设备日志
docker-compose logs -f mock-modbus
docker-compose logs -f mock-opcua
docker-compose logs -f mock-plc
docker-compose logs -f mock-device-manager
```

### 性能监控

```bash
# 查看容器资源使用
docker stats

# 查看网络连接
netstat -tulpn | grep -E "502|4840|5001|8080"
```

## 🔒 网络和安全

### 端口映射
- **502**: Modbus TCP设备
- **4840**: OPC UA设备
- **5001**: 三菱PLC设备
- **8080**: 设备管理器

### 防火墙配置
如果启用了防火墙，需要开放相应端口：

```bash
# Ubuntu/Debian
sudo ufw allow 502
sudo ufw allow 4840
sudo ufw allow 5001
sudo ufw allow 8080

# CentOS/RHEL
sudo firewall-cmd --add-port=502/tcp --permanent
sudo firewall-cmd --add-port=4840/tcp --permanent
sudo firewall-cmd --add-port=5001/tcp --permanent
sudo firewall-cmd --add-port=8080/tcp --permanent
sudo firewall-cmd --reload
```

## 🐛 故障排除

### 常见问题

1. **端口被占用**
   ```bash
   # 查看端口占用
   netstat -tulpn | grep :502
   
   # 杀死占用进程
   sudo kill -9 <PID>
   ```

2. **Docker镜像构建失败**
   ```bash
   # 清理Docker缓存
   docker system prune -a
   
   # 重新构建
   ./start_mock_devices.sh build
   ```

3. **设备连接失败**
   ```bash
   # 检查容器状态
   docker-compose ps
   
   # 重启设备
   docker-compose restart mock-modbus
   ```

4. **数据不更新**
   ```bash
   # 检查数据生成器配置
   # 验证update_interval设置
   # 查看设备日志
   docker-compose logs mock-modbus
   ```

### 调试模式

```bash
# 以调试模式启动设备
docker-compose -f docker-compose.yml -f docker-compose.debug.yml up

# 进入容器调试
docker-compose exec mock-modbus bash
```

## 📝 开发指南

### 添加新设备类型

1. **创建设备服务器类**
   ```python
   # 继承BaseDeviceServer
   class NewDeviceServer(BaseDeviceServer):
       def start_server(self):
           # 实现启动逻辑
           pass
       
       def handle_client_request(self, client_socket, data):
           # 实现协议处理
           pass
   ```

2. **添加配置文件**
   ```json
   {
     "device_id": "new_device_001",
     "device_type": "new_protocol",
     "port": 5002
   }
   ```

3. **创建Dockerfile**
   ```dockerfile
   FROM python:3.9-slim
   # 设备特定配置
   ```

4. **添加到设备管理器**
   ```python
   # 在device_manager.py中添加设备类型支持
   ```

### 自定义数据生成器

```python
class CustomDataGenerator(DataGenerator):
    def generate_data(self) -> Dict[int, Any]:
        # 实现自定义数据生成逻辑
        return {address: value}
```

## 📚 参考资料

- [Modbus协议规范](https://modbus.org/docs/Modbus_Application_Protocol_V1_1b3.pdf)
- [OPC UA规范](https://opcfoundation.org/developer-tools/specifications-unified-architecture)
- [三菱PLC通信协议](https://www.mitsubishielectric.com/fa/products/cnt/plc/pmerit/easy_com/index.html)
- [Docker使用指南](https://docs.docker.com/)
- [IoT数采系统设计文档](./IoT数采系统界面方案设计.md)

## 🤝 贡献指南

1. Fork项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开Pull Request

## 📄 许可证

本项目采用MIT许可证 - 查看 [LICENSE](LICENSE) 文件了解详情

## 📞 支持

如有问题或建议，请：
- 创建GitHub Issue
- 联系开发团队
- 查看项目Wiki

---

**IoT数采系统模拟设备** - 让IoT开发更简单！ 🚀 