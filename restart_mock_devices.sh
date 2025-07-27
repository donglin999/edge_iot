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

print_info "=== 重启模拟设备 ==="

# 检查脚本是否存在
if [ ! -f "./stop_mock_devices.sh" ]; then
    print_error "停止脚本不存在: stop_mock_devices.sh"
    exit 1
fi

if [ ! -f "./start_mock_devices_simple.sh" ]; then
    print_error "启动脚本不存在: start_mock_devices_simple.sh"
    exit 1
fi

# 停止设备
print_info "步骤1: 停止现有设备..."
./stop_mock_devices.sh

# 等待进程完全停止
print_info "等待进程完全停止..."
sleep 3

# 启动设备
print_info "步骤2: 重新启动设备..."
./start_mock_devices_simple.sh

print_success "=== 模拟设备重启完成 ==="
