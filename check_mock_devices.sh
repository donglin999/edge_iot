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

echo "=========================================="
echo "    IoT数采系统模拟设备状态检查"
echo "=========================================="
echo

# 检查进程状态
print_info "进程状态检查:"
echo

# Modbus TCP设备
MODBUS_PROCESSES=$(ps aux | grep -E "modbus_tcp_server" | grep -v grep | wc -l)
if [ $MODBUS_PROCESSES -gt 0 ]; then
    print_success "📟 Modbus TCP设备 - 运行中 ($MODBUS_PROCESSES 个进程)"
    ps aux | grep -E "modbus_tcp_server" | grep -v grep | while read line; do
        echo "   $line"
    done
else
    print_error "📟 Modbus TCP设备 - 未运行"
fi
echo

# OPC UA设备
OPCUA_PROCESSES=$(ps aux | grep -E "opcua_server" | grep -v grep | wc -l)
if [ $OPCUA_PROCESSES -gt 0 ]; then
    print_success "🌐 OPC UA设备 - 运行中 ($OPCUA_PROCESSES 个进程)"
    ps aux | grep -E "opcua_server" | grep -v grep | while read line; do
        echo "   $line"
    done
else
    print_error "🌐 OPC UA设备 - 未运行"
fi
echo

# 三菱PLC设备
PLC_PROCESSES=$(ps aux | grep -E "plc_server" | grep -v grep | wc -l)
if [ $PLC_PROCESSES -gt 0 ]; then
    print_success "🏭 三菱PLC设备 - 运行中 ($PLC_PROCESSES 个进程)"
    ps aux | grep -E "plc_server" | grep -v grep | while read line; do
        echo "   $line"
    done
else
    print_error "🏭 三菱PLC设备 - 未运行"
fi
echo

# 检查端口状态
print_info "端口状态检查:"
echo

# 检查端口502 (Modbus TCP)
if netstat -tlnp 2>/dev/null | grep -q ":502 "; then
    print_success "📟 端口502 (Modbus TCP) - 监听中"
    netstat -tlnp 2>/dev/null | grep ":502 " | while read line; do
        echo "   $line"
    done
else
    print_error "📟 端口502 (Modbus TCP) - 未监听"
fi
echo

# 检查端口4840 (OPC UA)
if netstat -tlnp 2>/dev/null | grep -q ":4840 "; then
    print_success "🌐 端口4840 (OPC UA) - 监听中"
    netstat -tlnp 2>/dev/null | grep ":4840 " | while read line; do
        echo "   $line"
    done
else
    print_error "🌐 端口4840 (OPC UA) - 未监听"
fi
echo

# 检查端口5001 (三菱PLC)
if netstat -tlnp 2>/dev/null | grep -q ":5001 "; then
    print_success "🏭 端口5001 (三菱PLC) - 监听中"
    netstat -tlnp 2>/dev/null | grep ":5001 " | while read line; do
        echo "   $line"
    done
else
    print_error "🏭 端口5001 (三菱PLC) - 未监听"
fi
echo

# 检查PID文件
print_info "PID文件检查:"
echo

if [ -f "mock-devices/modbus.pid" ]; then
    PID=$(cat mock-devices/modbus.pid)
    if ps -p $PID > /dev/null 2>&1; then
        print_success "📟 Modbus PID文件存在 (PID: $PID) - 有效"
    else
        print_warning "📟 Modbus PID文件存在 (PID: $PID) - 进程不存在"
    fi
else
    print_warning "📟 Modbus PID文件不存在"
fi

if [ -f "mock-devices/opcua.pid" ]; then
    PID=$(cat mock-devices/opcua.pid)
    if ps -p $PID > /dev/null 2>&1; then
        print_success "🌐 OPC UA PID文件存在 (PID: $PID) - 有效"
    else
        print_warning "🌐 OPC UA PID文件存在 (PID: $PID) - 进程不存在"
    fi
else
    print_warning "🌐 OPC UA PID文件不存在"
fi

if [ -f "mock-devices/plc.pid" ]; then
    PID=$(cat mock-devices/plc.pid)
    if ps -p $PID > /dev/null 2>&1; then
        print_success "🏭 PLC PID文件存在 (PID: $PID) - 有效"
    else
        print_warning "🏭 PLC PID文件存在 (PID: $PID) - 进程不存在"
    fi
else
    print_warning "🏭 PLC PID文件不存在"
fi
echo

# 设备连接信息
print_info "设备连接信息:"
echo "📟 Modbus TCP: localhost:502"
echo "🌐 OPC UA: opc.tcp://localhost:4840/freeopcua/server/"
echo "🏭 三菱PLC: localhost:5001"
echo

# 管理命令
print_info "管理命令:"
echo "启动设备: ./start_mock_devices_simple.sh"
echo "停止设备: ./stop_mock_devices.sh"
echo "重启设备: ./restart_mock_devices.sh"
echo "查看日志: tail -f mock-devices/*.log"
echo

echo "=========================================="
