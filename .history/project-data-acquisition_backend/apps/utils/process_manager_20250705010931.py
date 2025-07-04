import multiprocessing
from multiprocessing import Process
import threading
import time
from apps.utils.baseLogger import Log
from settings import DevelopmentConfig


class ProcessManager:
    """进程管理器"""

    def __init__(self):
        self.processes = {}
        self.process_configs = {}

    def add_process_config(self, process_type, config):
        """添加进程配置"""
        if process_type not in self.process_configs:
            self.process_configs[process_type] = []
        self.process_configs[process_type].append(config)

    def start_process(self, process_type, config):
        #print(f"start_process: {process_type}, config: {config}")
        """启动单个进程"""
        try:
            if process_type == 'MC':
                from apps.collector.plc_influx import PlcInflux
                process = Process(target=PlcInflux(config).plc_influx)
            elif process_type == 'modbustcp':
                from apps.collector.modbustcp_influx import ModbustcpInflux
                process = Process(target=ModbustcpInflux(config).modbustcp_influx)
            elif process_type == 'opc':
                from apps.collector.opcua_influx import OpcuaInflux
                process = Process(target=OpcuaInflux(config).start_collector)
            elif process_type == 'melseca1enet':
                from apps.collector.melseca1enet_influx import MelsecA1ENetInflux
                process = Process(target=MelsecA1ENetInflux(config).melseca1enet_influx)
            else:
                Log().printError(f"未知的进程类型: {process_type}")
                return None
            #print(f"start_process: {process_type}, config: {config}")

            process.start()
            self.processes[process.pid] = {
                'process': process,
                'type': process_type,
                'config': config
            }
            Log().printInfo(f"启动{process_type}进程成功, PID: {process.pid}")
            print(f"启动{process_type}进程成功, PID: {process.pid}")
            return process.pid

        except Exception as e:
            Log().printError(f"启动{process_type}进程失败: {e}")
            print(f"启动{process_type}进程失败: {e}")
            return None

    def start_all_processes(self):
        """启动所有配置的进程"""
        for process_type, configs in self.process_configs.items():
            for config in configs:
                Log().printInfo(f"process_type: {process_type}")
                print(f"process_type: {process_type}")
                self.start_process(process_type, config)

    def monitor_processes(self):
        pass
        """监控进程状态"""
        while True:
            for pid, info in list(self.processes.items()):
                if not info['process'].is_alive():
                    Log().printInfo(f"进程 {pid} ({info['type']}) 已终止,尝试重启")
                    print(f"进程 {pid} ({info['type']}) 已终止,尝试重启")
                    self.start_process(info['type'], info['config'])
                    del self.processes[pid]
            time.sleep(5)