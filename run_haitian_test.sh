#!/bin/bash

# 海天注塑机数据清单完整流程测试脚本
# 基于Excel数据地址清单的IoT数采系统测试

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

print_header() {
    echo "=========================================="
    echo "  海天注塑机数据清单完整流程测试"
    echo "  基于Excel数据地址清单"
    echo "=========================================="
    echo
}

# 检查环境依赖
check_dependencies() {
    print_info "检查环境依赖..."
    
    # 检查Python环境
    if ! command -v python3 &> /dev/null; then
        print_error "Python3未安装"
        exit 1
    fi
    
    # 检查Docker环境
    if ! command -v docker &> /dev/null; then
        print_error "Docker未安装"
        exit 1
    fi
    
    # 检查必要的Python包
    python3 -c "import pandas, pymodbus, asyncua" 2>/dev/null || {
        print_warning "正在安装必要的Python包..."
        pip3 install pandas pymodbus asyncua influxdb-client
    }
    
    print_success "环境依赖检查完成"
}

# 启动模拟设备
start_mock_devices() {
    print_info "启动模拟设备..."
    
    # 使用自定义配置启动Modbus设备
    cd mock-devices
    
    # 启动Modbus TCP设备 (端口502映射到4196)
    print_info "启动海天注塑机Modbus设备..."
    python3 -c "
import sys
import os
sys.path.append(os.getcwd())
from modbus.modbus_tcp_server import ModbusTCPServer
import json
import threading
import time

# 使用海天注塑机配置
config = {
    'device_id': 'haitian_modbus_01',
    'host': '127.0.0.1',
    'port': 502,
    'unit_id': 1,
    'update_interval': 1.0
}

server = ModbusTCPServer(config)

# 在后台线程中启动服务器
def run_server():
    server.start_server()

thread = threading.Thread(target=run_server, daemon=True)
thread.start()

print('Modbus TCP设备已启动在端口502')
print('按Ctrl+C停止...')

try:
    while True:
        time.sleep(1)
        # 更新一些测试数据
        server.holding_registers[0] = int(time.time()) % 100  # 设备状态
        server.holding_registers[46] = int(time.time()) % 1000  # 产量
except KeyboardInterrupt:
    print('停止Modbus设备...')
    server.stop_server()
" &
    MODBUS_PID=$!
    
    # 等待Modbus设备启动
    sleep 3
    
    # 启动OPC UA设备
    print_info "启动海天注塑机36# OPC UA设备..."
    python3 -c "
import sys
import os
sys.path.append(os.getcwd())
from opcua.opcua_server import OPCUAServer
import threading
import time

# 使用海天注塑机36#配置
config = {
    'device_id': 'haitian_opcua_36',
    'host': '127.0.0.1',
    'port': 4840,
    'update_interval': 1.0
}

server = OPCUAServer(config)

# 在后台线程中启动服务器
def run_server():
    server.start_server()

thread = threading.Thread(target=run_server, daemon=True)
thread.start()

print('OPC UA设备已启动在端口4840')
print('按Ctrl+C停止...')

try:
    while True:
        time.sleep(1)
        server.update_data()
except KeyboardInterrupt:
    print('停止OPC UA设备...')
    server.stop_server()
" &
    OPCUA_PID=$!
    
    cd ..
    
    # 等待设备完全启动
    sleep 5
    print_success "模拟设备启动完成"
}

# 验证设备连接
verify_device_connections() {
    print_info "验证设备连接..."
    
    # 验证Modbus连接
    python3 -c "
from pymodbus.client.sync import ModbusTcpClient
import sys

try:
    client = ModbusTcpClient('127.0.0.1', port=502)
    if client.connect():
        # 尝试读取设备状态寄存器
        result = client.read_holding_registers(40047-40001, 1, unit=1)
        if not result.isError():
            print('Modbus设备连接成功，设备状态值:', result.registers[0])
        else:
            print('Modbus读取失败:', result)
        client.close()
    else:
        print('Modbus连接失败')
        sys.exit(1)
except Exception as e:
    print('Modbus连接异常:', e)
    sys.exit(1)
"
    
    # 验证OPC UA连接
    python3 -c "
try:
    from asyncua import Client
    import asyncio
    
    async def test_opcua():
        client = Client('opc.tcp://127.0.0.1:4840/freeopcua/server/')
        try:
            await client.connect()
            print('OPC UA设备连接成功')
            
            # 尝试读取一些节点
            root = client.get_root_node()
            print('OPC UA根节点:', root)
            
            await client.disconnect()
        except Exception as e:
            print('OPC UA连接异常:', e)
    
    asyncio.run(test_opcua())
except ImportError:
    print('OPC UA库未安装，跳过OPC UA连接验证')
except Exception as e:
    print('OPC UA连接异常:', e)
"
    
    print_success "设备连接验证完成"
}

# 运行数据采集测试
run_data_collection_test() {
    print_info "启动数据采集测试..."
    
    # 创建简化的数据采集测试脚本
    python3 -c "
import time
import json
from pymodbus.client.sync import ModbusTcpClient
from datetime import datetime
import sys

print('开始数据采集测试...')

# 连接Modbus设备
client = ModbusTcpClient('127.0.0.1', port=502)
if not client.connect():
    print('无法连接到Modbus设备')
    sys.exit(1)

# 定义数据点映射 (基于Excel清单)
data_points = {
    '设备状态': {'address': 40047, 'type': 'INT16'},
    '输出压力': {'address': 40001, 'type': 'INT16'},
    '输出速度': {'address': 40002, 'type': 'INT16'},
    '输出背压': {'address': 40003, 'type': 'INT16'},
    '循环周期': {'address': 40004, 'type': 'INT32'},
    '动作计时': {'address': 40006, 'type': 'INT16'},
    '射出位置': {'address': 40007, 'type': 'INT16'},
    '推力座位置': {'address': 40008, 'type': 'INT16'},
    '顶针位置': {'address': 40009, 'type': 'INT16'},
    '产量': {'address': 40069, 'type': 'INT32'}
}

print('数据点配置:')
for name, config in data_points.items():
    print(f'  {name}: 地址{config[\"address\"]}, 类型{config[\"type\"]}')

print('\n开始数据采集...')

# 采集5轮数据
collected_data = []
for round_num in range(5):
    round_data = {
        'timestamp': datetime.now().isoformat(),
        'round': round_num + 1,
        'data': {}
    }
    
    print(f'\n第{round_num + 1}轮数据采集:')
    for name, config in data_points.items():
        try:
            if config['type'] == 'INT32':
                # 读取32位数据需要读取2个寄存器
                result = client.read_holding_registers(config['address']-40001, 2, unit=1)
                if not result.isError():
                    value = (result.registers[1] << 16) | result.registers[0]
                else:
                    value = None
            else:
                # 读取16位数据
                result = client.read_holding_registers(config['address']-40001, 1, unit=1)
                if not result.isError():
                    value = result.registers[0]
                else:
                    value = None
            
            round_data['data'][name] = value
            print(f'  {name}: {value}')
            
        except Exception as e:
            print(f'  {name}: 读取失败 - {e}')
            round_data['data'][name] = None
    
    collected_data.append(round_data)
    time.sleep(2)

# 关闭连接
client.close()

# 保存采集的数据
with open('haitian_test_data.json', 'w', encoding='utf-8') as f:
    json.dump(collected_data, f, ensure_ascii=False, indent=2)

print('\n数据采集完成!')
print(f'共采集 {len(collected_data)} 轮数据')
print('数据已保存到 haitian_test_data.json')

# 数据分析
print('\n数据分析:')
for name in data_points.keys():
    values = [round_data['data'][name] for round_data in collected_data if round_data['data'][name] is not None]
    if values:
        print(f'{name}: 最小值={min(values)}, 最大值={max(values)}, 平均值={sum(values)/len(values):.2f}')
    else:
        print(f'{name}: 无有效数据')
"
    
    print_success "数据采集测试完成"
}

# 验证测试结果
verify_test_results() {
    print_info "验证测试结果..."
    
    if [[ -f "haitian_test_data.json" ]]; then
        python3 -c "
import json

# 读取测试数据
with open('haitian_test_data.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print('测试结果验证:')
print(f'采集轮数: {len(data)}')

# 检查数据完整性
total_points = 0
valid_points = 0

for round_data in data:
    for name, value in round_data['data'].items():
        total_points += 1
        if value is not None:
            valid_points += 1

success_rate = (valid_points / total_points * 100) if total_points > 0 else 0
print(f'数据点总数: {total_points}')
print(f'有效数据点: {valid_points}')
print(f'成功率: {success_rate:.2f}%')

# 检查数据变化
print('\n数据变化检查:')
for name in ['设备状态', '输出压力', '产量']:
    values = [round_data['data'][name] for round_data in data if round_data['data'][name] is not None]
    if len(values) > 1:
        if len(set(values)) > 1:
            print(f'{name}: 数据有变化 ✓')
        else:
            print(f'{name}: 数据无变化 ⚠')
    else:
        print(f'{name}: 数据不足')

if success_rate >= 80:
    print('\n✅ 测试通过: 数据采集成功率达到要求')
else:
    print('\n❌ 测试失败: 数据采集成功率不足')
"
        print_success "测试结果验证完成"
    else
        print_error "未找到测试数据文件"
    fi
}

# 清理资源
cleanup() {
    print_info "清理测试资源..."
    
    # 停止模拟设备进程
    if [[ ! -z "$MODBUS_PID" ]]; then
        kill $MODBUS_PID 2>/dev/null || true
    fi
    
    if [[ ! -z "$OPCUA_PID" ]]; then
        kill $OPCUA_PID 2>/dev/null || true
    fi
    
    # 清理临时文件
    # rm -f haitian_test_data.json
    
    print_success "资源清理完成"
}

# 主函数
main() {
    print_header
    
    # 设置清理陷阱
    trap cleanup EXIT
    
    check_dependencies
    start_mock_devices
    verify_device_connections
    run_data_collection_test
    verify_test_results
    
    print_success "海天注塑机数据清单完整流程测试完成！"
    print_info "测试数据已保存到 haitian_test_data.json"
}

# 处理脚本参数
case "${1:-}" in
    "devices")
        start_mock_devices
        echo "模拟设备已启动，按Ctrl+C停止..."
        wait
        ;;
    "collect")
        run_data_collection_test
        ;;
    "verify")
        verify_test_results
        ;;
    "cleanup")
        cleanup
        ;;
    *)
        main
        ;;
esac 