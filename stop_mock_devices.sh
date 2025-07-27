#!/bin/bash

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

print_info "停止模拟设备..."

# 停止通过PID文件管理的进程
cd mock-devices 2>/dev/null || {
    print_error "mock-devices目录不存在"
    exit 1
}

# 停止Modbus设备 (可能需要sudo权限)
if [ -f modbus.pid ]; then
    PID=$(cat modbus.pid)
    print_info "停止Modbus设备 (PID: $PID)..."
    sudo kill $PID 2>/dev/null || kill $PID 2>/dev/null || true
    rm -f modbus.pid
    print_success "Modbus设备已停止"
else
    print_warning "未找到Modbus PID文件"
fi

# 停止OPC UA设备
if [ -f opcua.pid ]; then
    PID=$(cat opcua.pid)
    print_info "停止OPC UA设备 (PID: $PID)..."
    kill $PID 2>/dev/null || true
    rm -f opcua.pid
    print_success "OPC UA设备已停止"
else
    print_warning "未找到OPC UA PID文件"
fi

# 停止三菱PLC设备
if [ -f plc.pid ]; then
    PID=$(cat plc.pid)
    print_info "停止三菱PLC设备 (PID: $PID)..."
    kill $PID 2>/dev/null || true
    rm -f plc.pid
    print_success "三菱PLC设备已停止"
else
    print_warning "未找到PLC PID文件"
fi

cd ..

# 强制停止所有相关进程
print_info "强制停止所有相关进程..."

# 停止Modbus进程 (包括sudo启动的)
sudo pkill -f "modbus_tcp_server.py" 2>/dev/null || true
pkill -f "modbus_tcp_server.py" 2>/dev/null || true

# 停止OPC UA进程
pkill -f "opcua_server.py" 2>/dev/null || true

# 停止三菱PLC进程
pkill -f "plc_server.py" 2>/dev/null || true

# 等待进程完全停止
sleep 2

# 验证进程是否已停止
print_info "验证进程状态:"

MODBUS_RUNNING=$(ps aux | grep -E "modbus_tcp_server" | grep -v grep | wc -l)
OPCUA_RUNNING=$(ps aux | grep -E "opcua_server" | grep -v grep | wc -l)
PLC_RUNNING=$(ps aux | grep -E "plc_server" | grep -v grep | wc -l)

if [ $MODBUS_RUNNING -eq 0 ]; then
    print_success "Modbus设备已停止"
else
    print_warning "Modbus设备仍在运行 ($MODBUS_RUNNING 个进程)"
fi

if [ $OPCUA_RUNNING -eq 0 ]; then
    print_success "OPC UA设备已停止"
else
    print_warning "OPC UA设备仍在运行 ($OPCUA_RUNNING 个进程)"
fi

if [ $PLC_RUNNING -eq 0 ]; then
    print_success "三菱PLC设备已停止"
else
    print_warning "三菱PLC设备仍在运行 ($PLC_RUNNING 个进程)"
fi

# 检查端口状态
print_info "检查端口状态:"

if ! netstat -tlnp 2>/dev/null | grep -q ":502 "; then
    print_success "端口502已释放"
else
    print_warning "端口502仍被占用"
fi

if ! netstat -tlnp 2>/dev/null | grep -q ":4840 "; then
    print_success "端口4840已释放"
else
    print_warning "端口4840仍被占用"
fi

if ! netstat -tlnp 2>/dev/null | grep -q ":5001 "; then
    print_success "端口5001已释放"
else
    print_warning "端口5001仍被占用"
fi

print_success "模拟设备停止完成"
