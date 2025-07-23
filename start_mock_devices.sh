#!/bin/bash

# IoT数采系统模拟设备启动脚本
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

# 检查Docker是否安装
check_docker() {
    if ! command -v docker &> /dev/null; then
        print_error "Docker未安装，请先安装Docker"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose未安装，请先安装Docker Compose"
        exit 1
    fi
    
    print_success "Docker环境检查通过"
}

# 检查端口是否被占用
check_ports() {
    local ports=(502 4840 5001 8080)
    local occupied_ports=()
    
    for port in "${ports[@]}"; do
        if netstat -tuln 2>/dev/null | grep -q ":$port "; then
            occupied_ports+=($port)
        fi
    done
    
    if [ ${#occupied_ports[@]} -gt 0 ]; then
        print_warning "以下端口被占用: ${occupied_ports[*]}"
        print_warning "模拟设备可能无法正常启动"
        read -p "是否继续启动？(y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    else
        print_success "端口检查通过"
    fi
}

# 构建Docker镜像
build_images() {
    print_info "开始构建模拟设备Docker镜像..."
    
    cd mock-devices
    
    # 构建Modbus TCP设备镜像
    print_info "构建Modbus TCP设备镜像..."
    docker build -t iot-mock-modbus -f docker/Dockerfile.modbus . || {
        print_error "Modbus TCP设备镜像构建失败"
        exit 1
    }
    
    # 构建OPC UA设备镜像
    print_info "构建OPC UA设备镜像..."
    docker build -t iot-mock-opcua -f docker/Dockerfile.opcua . || {
        print_error "OPC UA设备镜像构建失败"
        exit 1
    }
    
    # 构建三菱PLC设备镜像
    print_info "构建三菱PLC设备镜像..."
    docker build -t iot-mock-plc -f docker/Dockerfile.plc . || {
        print_error "三菱PLC设备镜像构建失败"
        exit 1
    }
    
    # 构建设备管理器镜像
    print_info "构建设备管理器镜像..."
    docker build -t iot-mock-manager -f docker/Dockerfile.manager . || {
        print_error "设备管理器镜像构建失败"
        exit 1
    }
    
    cd ..
    print_success "所有Docker镜像构建完成"
}

# 启动模拟设备
start_devices() {
    print_info "启动模拟设备服务..."
    
    # 使用docker-compose启动
    docker-compose up -d mock-modbus mock-opcua mock-plc mock-device-manager || {
        print_error "模拟设备启动失败"
        exit 1
    }
    
    print_success "模拟设备启动成功"
}

# 检查设备状态
check_device_status() {
    print_info "检查设备状态..."
    
    sleep 5  # 等待设备启动
    
    # 检查Modbus TCP设备
    if curl -s --connect-timeout 3 telnet://localhost:502 &>/dev/null; then
        print_success "Modbus TCP设备 (端口502) 运行正常"
    else
        print_warning "Modbus TCP设备 (端口502) 连接失败"
    fi
    
    # 检查OPC UA设备
    if curl -s --connect-timeout 3 telnet://localhost:4840 &>/dev/null; then
        print_success "OPC UA设备 (端口4840) 运行正常"
    else
        print_warning "OPC UA设备 (端口4840) 连接失败"
    fi
    
    # 检查三菱PLC设备
    if curl -s --connect-timeout 3 telnet://localhost:5001 &>/dev/null; then
        print_success "三菱PLC设备 (端口5001) 运行正常"
    else
        print_warning "三菱PLC设备 (端口5001) 连接失败"
    fi
    
    # 检查设备管理器
    if curl -s --connect-timeout 3 http://localhost:8080/health &>/dev/null; then
        print_success "设备管理器 (端口8080) 运行正常"
    else
        print_warning "设备管理器 (端口8080) 连接失败"
    fi
}

# 显示设备信息
show_device_info() {
    print_info "模拟设备信息："
    echo
    echo "📟 Modbus TCP设备："
    echo "   - 地址: localhost:502"
    echo "   - 单元ID: 1"
    echo "   - 支持: 线圈、离散输入、输入寄存器、保持寄存器"
    echo
    echo "🌐 OPC UA设备："
    echo "   - 地址: opc.tcp://localhost:4840/freeopcua/server/"
    echo "   - 命名空间: http://mock.iot.device/opcua001"
    echo "   - 节点: Temperature, Pressure, Humidity, FlowRate, SystemStatus, ProductionCounter"
    echo
    echo "🏭 三菱PLC设备："
    echo "   - 地址: localhost:5001"
    echo "   - 协议: A1E"
    echo "   - 支持: D寄存器、M继电器、X输入、Y输出"
    echo
    echo "🎛️  设备管理器："
    echo "   - 地址: http://localhost:8080"
    echo "   - 功能: 统一管理所有模拟设备"
    echo
    echo "📊 监控和日志："
    echo "   - 设备状态: docker-compose ps"
    echo "   - 设备日志: docker-compose logs [服务名]"
    echo "   - 停止设备: docker-compose down"
}

# 主函数
main() {
    echo "=========================================="
    echo "    IoT数采系统模拟设备启动脚本"
    echo "=========================================="
    echo
    
    # 检查环境
    check_docker
    check_ports
    
    # 询问是否重新构建镜像
    read -p "是否重新构建Docker镜像？(y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        build_images
    fi
    
    # 启动设备
    start_devices
    
    # 检查状态
    check_device_status
    
    # 显示信息
    show_device_info
    
    print_success "模拟设备启动完成！"
    print_info "使用 'docker-compose logs -f' 查看实时日志"
    print_info "使用 'docker-compose down' 停止所有设备"
}

# 处理脚本参数
case "${1:-}" in
    "build")
        build_images
        ;;
    "start")
        start_devices
        ;;
    "status")
        check_device_status
        ;;
    "info")
        show_device_info
        ;;
    *)
        main
        ;;
esac 