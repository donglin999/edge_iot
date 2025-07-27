"""
统一日志配置模块
用于整个IoT数采系统的日志管理
"""
import os
import logging
import logging.handlers
from datetime import datetime
from pathlib import Path

class LogConfig:
    """日志配置类"""
    
    def __init__(self, base_dir="./edge_iot"):
        self.base_dir = Path(base_dir)
        self.logs_dir = self.base_dir / "logs"
        self.ensure_log_dirs()
    
    def ensure_log_dirs(self):
        """确保日志目录存在"""
        modules = ["backend", "frontend", "data-acquisition", "mock-devices"]
        subdirs = ["core", "services", "routers", "utils", "collector", "connect", "modbus", "opcua", "mitsubishi"]
        
        for module in modules:
            module_dir = self.logs_dir / module
            module_dir.mkdir(parents=True, exist_ok=True)
            
            for subdir in subdirs:
                (module_dir / subdir).mkdir(exist_ok=True)
    
    def get_logger(self, module, submodule=None, component=None):
        """
        获取日志记录器
        Args:
            module: 模块名 (backend/frontend/data-acquisition/mock-devices)
            submodule: 子模块名 (core/services/routers/utils/collector/connect等)
            component: 组件名 (具体的文件名)
        """
        # 构建日志器名称
        logger_name_parts = [module]
        if submodule:
            logger_name_parts.append(submodule)
        if component:
            logger_name_parts.append(component)
        
        logger_name = ".".join(logger_name_parts)
        
        # 构建日志文件路径
        log_path_parts = [self.logs_dir, module]
        if submodule:
            log_path_parts.append(submodule)
        
        log_dir = Path(*log_path_parts)
        
        if component:
            log_file = log_dir / f"{component}.log"
        elif submodule:
            log_file = log_dir / f"{submodule}.log"
        else:
            log_file = log_dir / f"{module}.log"
        
        # 创建日志器
        logger = logging.getLogger(logger_name)
        
        # 如果日志器已经配置过，直接返回
        if logger.handlers:
            return logger
        
        logger.setLevel(logging.DEBUG)
        
        # 创建格式器
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # 文件处理器 - 按日期轮转
        file_handler = logging.handlers.TimedRotatingFileHandler(
            filename=log_file,
            when='midnight',
            interval=1,
            backupCount=7,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
        # 控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%H:%M:%S'
        )
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)
        
        return logger

# 全局日志配置实例
log_config = LogConfig()

def get_logger(module, submodule=None, component=None):
    """快捷函数获取日志器"""
    return log_config.get_logger(module, submodule, component)