#!/bin/bash

# IoT数采系统测试运行脚本
# 运行所有模块的测试用例

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

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

# 检查Python和pytest
check_requirements() {
    if ! command -v python3 &> /dev/null; then
        print_error "Python3未安装"
        exit 1
    fi
    
    if ! python3 -c "import pytest" &> /dev/null; then
        print_warning "pytest未安装，正在安装..."
        pip3 install pytest pytest-cov
    fi
    
    print_success "测试环境检查通过"
}

# 运行后端测试
run_backend_tests() {
    print_info "运行后端测试..."
    
    cd backend
    if [ -d "tests" ]; then
        python3 -m pytest tests/ -v --tb=short || {
            print_warning "后端测试存在失败项"
        }
    else
        print_warning "后端测试目录不存在"
    fi
    cd ..
}

# 运行前端测试
run_frontend_tests() {
    print_info "运行前端测试..."
    
    cd frontend
    if [ -d "tests" ] && [ -f "package.json" ]; then
        if command -v npm &> /dev/null; then
            npm test || {
                print_warning "前端测试存在失败项"
            }
        else
            print_warning "npm未安装，跳过前端测试"
        fi
    else
        print_warning "前端测试环境不完整"
    fi
    cd ..
}

# 运行数采服务测试
run_data_acquisition_tests() {
    print_info "运行数采服务测试..."
    
    cd project-data-acquisition
    if [ -d "tests" ]; then
        python3 -m pytest tests/ -v --tb=short || {
            print_warning "数采服务测试存在失败项"
        }
    else
        print_warning "数采服务测试目录不存在"
    fi
    cd ..
}

# 运行模拟设备测试
run_mock_device_tests() {
    print_info "运行模拟设备测试..."
    
    cd mock-devices
    if [ -d "tests" ]; then
        python3 -m pytest tests/ -v --tb=short || {
            print_warning "模拟设备测试存在失败项"
        }
    else
        print_warning "模拟设备测试目录不存在"
    fi
    cd ..
}

# 生成测试报告
generate_test_report() {
    print_info "生成测试覆盖率报告..."
    
    # 合并所有Python测试覆盖率
    python3 -m pytest \
        backend/tests/ \
        project-data-acquisition/tests/ \
        mock-devices/tests/ \
        --cov=backend \
        --cov=project-data-acquisition \
        --cov=mock-devices \
        --cov-report=html:test_coverage_report \
        --cov-report=term \
        -v || {
        print_warning "生成覆盖率报告时出现问题"
    }
    
    if [ -d "test_coverage_report" ]; then
        print_success "测试覆盖率报告已生成: test_coverage_report/index.html"
    fi
}

# 主函数
main() {
    echo "=========================================="
    echo "      IoT数采系统测试运行脚本"
    echo "=========================================="
    echo
    
    check_requirements
    
    # 运行各模块测试
    run_backend_tests
    run_frontend_tests
    run_data_acquisition_tests
    run_mock_device_tests
    
    # 生成报告
    read -p "是否生成测试覆盖率报告？(y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        generate_test_report
    fi
    
    print_success "所有测试执行完成！"
    print_info "查看详细结果请检查各模块的测试输出"
}

# 处理脚本参数
case "${1:-}" in
    "backend")
        run_backend_tests
        ;;
    "frontend")
        run_frontend_tests
        ;;
    "data-acquisition")
        run_data_acquisition_tests
        ;;
    "mock-devices")
        run_mock_device_tests
        ;;
    "coverage")
        generate_test_report
        ;;
    *)
        main
        ;;
esac 