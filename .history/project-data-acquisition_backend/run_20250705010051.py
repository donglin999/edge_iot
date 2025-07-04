#!/usr/bin/env python
# -*- encoding: utf-8 -*-

import pandas as pd
import multiprocessing
from utils.baseLogger import Log
from apps.utils.excel_processor import process_excel_data
from apps.utils.process_manager import ProcessManager

def main():
    try:
        # 读取Excel配置
        df = pd.read_excel('数据地址清单.xlsx', sheet_name='Sheet1')
        device_data_addresses = process_excel_data(df)
        # 创建进程管理器
        process_manager = ProcessManager()
        # 添加进程配置
        for config in device_data_addresses.values():
            process_type = config['protocol_type']
            process_manager.add_process_config(process_type, config)
        Log().printInfo(f"process_manager: {process_manager}")
        # 启动所有进程
        process_manager.start_all_processes()
        
        # 启动进程监控
        process_manager.monitor_processes()
        
    except Exception as e:
        Log().printError(f"程序运行出错: {e}")
        raise

if __name__ == "__main__":
    multiprocessing.freeze_support()
    main()


