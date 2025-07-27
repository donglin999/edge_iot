#!/bin/bash

# IoT数采系统模拟设备一键启动脚本
# 作者：IoT团队
# 日期：2024

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印带颜色的消息
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查并安装依赖
check_dependencies() {
    print_info "检查Python依赖..."
    
    cd mock-devices
    
    # 检查虚拟环境
    if [ ! -d "venv" ]; then
        print_info "创建虚拟环境..."
        python3 -m venv venv
    fi
    
    # 激活虚拟环境
    source venv/bin/activate
    
    # 安装依赖
    print_info "安装Python依赖..."
    pip install -r requirements.txt
    
    cd ..
    print_success "依赖检查完成"
}

# 停止已运行的进程
stop_existing_processes() {
    print_info "停止已运行的模拟设备进程..."
    
    # 停止Modbus TCP设备
    pkill -f "modbus_tcp_server.py" || true
    
    # 停止OPC UA设备
    pkill -f "opcua_server.py" || true
    
    # 停止三菱PLC设备
    pkill -f "plc_server.py" || true
    
    sleep 2
    print_success "进程清理完成"
}

# 修改Modbus配置为使用标准端口502
setup_modbus_config() {
    print_info "配置Modbus TCP设备使用标准端口502..."
    
    cd mock-devices
    
    # 修改配置文件
    cat > modbus/modbus_config.json << 'EOF'
{
    "device_id": "modbus_tcp_001",
    "host": "0.0.0.0",
    "port": 502,
    "unit_id": 1,
    "update_interval": 1.0,
    "coil_count": 100,
    "discrete_input_count": 100,
    "input_register_count": 100,
    "holding_register_count": 100,
    "data_generator": {
        "type": "composite",
        "generators": [
            {
                "type": "sine",
                "amplitude": 1000,
                "frequency": 0.1,
                "offset": 2000,
                "addresses": [0, 1, 2]
            },
            {
                "type": "random",
                "min_value": 0,
                "max_value": 4095,
                "data_type": "int",
                "addresses": [10, 11, 12]
            },
            {
                "type": "counter",
                "start_value": 0,
                "increment": 1,
                "addresses": [20, 21, 22]
            },
            {
                "type": "temperature",
                "base_temp": 25.0,
                "variation": 5.0,
                "addresses": [30, 31, 32]
            },
            {
                "type": "pressure",
                "base_pressure": 1013.25,
                "variation": 50.0,
                "addresses": [40, 41, 42]
            },
            {
                "type": "humidity",
                "base_humidity": 50.0,
                "variation": 20.0,
                "addresses": [50, 51, 52]
            },
            {
                "type": "flow_rate",
                "base_flow": 100.0,
                "variation": 30.0,
                "addresses": [60, 61, 62]
            }
        ]
    },
    "logging": {
        "level": "INFO",
        "file": "modbus.log"
    }
}
EOF
    
    cd ..
    print_success "Modbus配置已更新为使用端口502"
}

# 启动模拟设备
start_devices() {
    print_info "启动模拟设备..."
    
    cd mock-devices
    source venv/bin/activate
    
    # 启动Modbus TCP设备 (使用sudo权限绑定端口502)
    print_info "启动Modbus TCP设备 (端口502)..."
    sudo -E env "PATH=$PATH" python modbus/modbus_tcp_server.py > modbus.log 2>&1 &
    MODBUS_PID=$!
    echo $MODBUS_PID > modbus.pid
    
    # 启动OPC UA设备
    print_info "启动OPC UA设备 (端口4840)..."
    python opcua/opcua_server.py > opcua.log 2>&1 &
    OPCUA_PID=$!
    echo $OPCUA_PID > opcua.pid
    
    # 启动三菱PLC设备
    print_info "启动三菱PLC设备 (端口5001)..."
    python mitsubishi/plc_server.py > plc.log 2>&1 &
    PLC_PID=$!
    echo $PLC_PID > plc.pid
    
    cd ..
    
    print_success "所有模拟设备启动完成"
}

# 验证设备状态
verify_devices() {
    print_info "验证设备状态..."
    
    sleep 3
    
    # 检查端口监听状态
    print_info "检查端口监听状态:"
    
    if netstat -tlnp 2>/dev/null | grep -q ":502 "; then
        print_success "Modbus TCP设备 (端口502) - 运行中"
    else
        print_error "Modbus TCP设备 (端口502) - 未运行"
    fi
    
    if netstat -tlnp 2>/dev/null | grep -q ":4840 "; then
        print_success "OPC UA设备 (端口4840) - 运行中"
    else
        print_error "OPC UA设备 (端口4840) - 未运行"
    fi
    
    if netstat -tlnp 2>/dev/null | grep -q ":5001 "; then
        print_success "三菱PLC设备 (端口5001) - 运行中"
    else
        print_error "三菱PLC设备 (端口5001) - 未运行"
    fi
    
    # 检查进程状态
    print_info "检查进程状态:"
    ps aux | grep -E "(modbus_tcp_server|opcua_server|plc_server)" | grep -v grep || print_warning "未找到相关进程"
}

# 主函数
main() {
    print_info "=== IoT数采系统模拟设备启动脚本 ==="
    
    # 检查是否在正确的目录
    if [ ! -d "mock-devices" ]; then
        print_error "请在项目根目录运行此脚本"
        exit 1
    fi
    
    # 检查sudo权限
    if ! sudo -n true 2>/dev/null; then
        print_warning "需要sudo权限来绑定端口502，请输入密码:"
        sudo true
    fi
    
    check_dependencies
    stop_existing_processes
    setup_modbus_config
    start_devices
    verify_devices
    
    print_success "=== 模拟设备启动完成 ==="
    print_info "设备地址:"
    print_info "  - Modbus TCP: localhost:502"
    print_info "  - OPC UA: opc.tcp://localhost:4840/freeopcua/server/"
    print_info "  - 三菱PLC: localhost:5001"
    print_info ""
    print_info "查看日志:"
    print_info "  - Modbus: tail -f mock-devices/modbus.log"
    print_info "  - OPC UA: tail -f mock-devices/opcua.log"
    print_info "  - PLC: tail -f mock-devices/plc.log"
}

# 运行主函数
main "$@" 