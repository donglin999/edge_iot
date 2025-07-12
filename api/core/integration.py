import os
import sys
import importlib.util
import logging
from typing import Dict, List, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

class DataAcquisitionIntegration:
    """Integration with existing data acquisition system"""
    
    def __init__(self):
        self.data_acquisition_path = None
        self.process_manager = None
        self.config_manager = None
        self._initialize_integration()
    
    def _initialize_integration(self):
        """Initialize integration with existing system"""
        try:
            # Get the data acquisition system path
            data_acquisition_path = os.getenv("DATA_ACQUISITION_PATH", "/app/data_acquisition")
            if os.path.exists(data_acquisition_path):
                self.data_acquisition_path = data_acquisition_path
                sys.path.insert(0, data_acquisition_path)
                logger.info(f"Data acquisition system path: {data_acquisition_path}")
                
                # Try to import existing components
                self._import_existing_components()
            else:
                logger.warning(f"Data acquisition system not found at {data_acquisition_path}")
                
        except Exception as e:
            logger.error(f"Failed to initialize data acquisition integration: {e}")
    
    def _import_existing_components(self):
        """Import existing system components"""
        try:
            # Try to import process manager
            if self._module_exists("apps.utils.process_manager"):
                process_manager_module = importlib.import_module("apps.utils.process_manager")
                if hasattr(process_manager_module, "ProcessManager"):
                    self.process_manager = process_manager_module.ProcessManager()
                    logger.info("Process manager imported successfully")
            
            # Try to import config manager
            if self._module_exists("apps.utils.config_manager"):
                config_manager_module = importlib.import_module("apps.utils.config_manager")
                if hasattr(config_manager_module, "ConfigManager"):
                    self.config_manager = config_manager_module.ConfigManager()
                    logger.info("Config manager imported successfully")
                    
        except Exception as e:
            logger.error(f"Failed to import existing components: {e}")
    
    def _module_exists(self, module_name: str) -> bool:
        """Check if a module exists"""
        try:
            spec = importlib.util.find_spec(module_name)
            return spec is not None
        except (ImportError, ValueError, ModuleNotFoundError):
            return False
    
    def get_process_manager(self):
        """Get the process manager instance"""
        if self.process_manager:
            return self.process_manager
        
        # Return a mock process manager if the real one is not available
        return MockProcessManager()
    
    def get_config_manager(self):
        """Get the config manager instance"""
        if self.config_manager:
            return self.config_manager
        
        # Return a mock config manager if the real one is not available
        return MockConfigManager()
    
    def get_data_acquisition_path(self) -> Optional[str]:
        """Get the data acquisition system path"""
        return self.data_acquisition_path
    
    def is_system_available(self) -> bool:
        """Check if the data acquisition system is available"""
        return self.data_acquisition_path is not None

class MockProcessManager:
    """Mock process manager for testing/development"""
    
    def __init__(self):
        self.processes = {}
        logger.info("Using mock process manager")
    
    def get_all_processes(self) -> Dict:
        """Get all process information"""
        return {
            "modbus_collector": {
                "pid": 1234,
                "name": "modbus_collector",
                "status": "running",
                "cpu_percent": 2.5,
                "memory_percent": 1.2,
                "start_time": "2023-01-01 12:00:00"
            },
            "opcua_collector": {
                "pid": 1235,
                "name": "opcua_collector",
                "status": "running",
                "cpu_percent": 3.1,
                "memory_percent": 2.1,
                "start_time": "2023-01-01 12:00:00"
            }
        }
    
    def start_process(self, process_name: str) -> bool:
        """Start a process"""
        logger.info(f"Mock: Starting process {process_name}")
        return True
    
    def stop_process(self, process_name: str) -> bool:
        """Stop a process"""
        logger.info(f"Mock: Stopping process {process_name}")
        return True
    
    def restart_process(self, process_name: str) -> bool:
        """Restart a process"""
        logger.info(f"Mock: Restarting process {process_name}")
        return True
    
    def get_process_logs(self, process_name: str, lines: int = 100) -> List[str]:
        """Get process logs"""
        return [
            f"2023-01-01 12:00:00 INFO: Process {process_name} started",
            f"2023-01-01 12:00:01 INFO: Connecting to device",
            f"2023-01-01 12:00:02 INFO: Connection established",
            f"2023-01-01 12:00:03 INFO: Data collection started"
        ]

class MockConfigManager:
    """Mock config manager for testing/development"""
    
    def __init__(self):
        self.configs = {}
        logger.info("Using mock config manager")
    
    def validate_config(self, config_path: str) -> Dict:
        """Validate configuration file"""
        logger.info(f"Mock: Validating config {config_path}")
        return {
            "is_valid": True,
            "errors": [],
            "warnings": [],
            "summary": {
                "total_devices": 5,
                "total_points": 100,
                "protocols": ["modbus_tcp", "opcua"]
            }
        }
    
    def apply_config(self, config_path: str) -> bool:
        """Apply configuration"""
        logger.info(f"Mock: Applying config {config_path}")
        return True
    
    def get_current_config(self) -> Dict:
        """Get current configuration"""
        return {
            "filename": "current_config.xlsx",
            "version": "1.0",
            "last_updated": "2023-01-01 12:00:00",
            "devices": 5,
            "points": 100
        }

# Global integration instance
integration = DataAcquisitionIntegration()