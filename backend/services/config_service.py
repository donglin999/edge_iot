import asyncio
import logging
import pandas as pd
import json
import os
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime
from fastapi import UploadFile
from models.config_models import (
    ConfigValidationResult, ConfigInfo, ConfigFile, ConfigStatus,
    ConfigUploadResponse, ConfigValidation, ConfigApplyResponse, 
    ConfigApply, ConfigHistory
)

logger = logging.getLogger(__name__)

class ConfigService:
    """Service for managing configuration"""
    
    def __init__(self):
        self.config_storage_path = "configs/uploaded"
        self.current_config_path = "configs/current_config.json"
        os.makedirs(self.config_storage_path, exist_ok=True)
        os.makedirs("configs", exist_ok=True)
    
    async def upload_config(self, file: UploadFile, description: Optional[str] = None, apply_immediately: bool = False) -> ConfigUploadResponse:
        """Upload and parse Excel configuration file"""
        try:
            # Generate unique config ID
            config_id = str(uuid.uuid4())
            
            # Save uploaded file
            file_path = os.path.join(self.config_storage_path, f"{config_id}_{file.filename}")
            content = await file.read()
            
            with open(file_path, "wb") as f:
                f.write(content)
            
            # Parse Excel file
            config_data = await self._parse_excel_config(file_path)
            
            # Validate parsed configuration
            validation = await self._validate_parsed_config(config_data)
            
            # Save parsed configuration
            config_json_path = os.path.join(self.config_storage_path, f"{config_id}_config.json")
            with open(config_json_path, "w", encoding="utf-8") as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)
            
            # Create config file record
            config_file = ConfigFile(
                id=config_id,
                filename=file.filename,
                upload_time=datetime.now(),
                file_size=len(content),
                status=ConfigStatus.PENDING if validation.is_valid else ConfigStatus.INVALID,
                description=description,
                version="1.0"
            )
            
            # Save config file metadata
            metadata_path = os.path.join(self.config_storage_path, f"{config_id}_metadata.json")
            with open(metadata_path, "w", encoding="utf-8") as f:
                json.dump(config_file.dict(), f, indent=2, default=str)
            
            # Apply immediately if requested and valid
            if apply_immediately and validation.is_valid:
                await self._apply_config_internal(config_id, config_data)
                config_file.status = ConfigStatus.ACTIVE
            
            return ConfigUploadResponse(
                success=True,
                message=f"Configuration uploaded successfully. Found {validation.summary.get('total_devices', 0)} devices and {validation.summary.get('total_points', 0)} data points.",
                config_id=config_id,
                validation=validation
            )
            
        except Exception as e:
            logger.error(f"Error uploading config: {e}")
            return ConfigUploadResponse(
                success=False,
                message=f"Failed to upload configuration: {str(e)}"
            )
    
    async def _parse_excel_config(self, file_path: str) -> Dict[str, Any]:
        """Parse Excel configuration file"""
        try:
            # Read Excel file
            df = pd.read_excel(file_path, sheet_name=0)
            
            # Expected columns in data address list Excel
            required_columns = ["设备名称", "协议类型", "IP地址", "端口", "数据点名称", "地址", "数据类型", "采集间隔"]
            
            # Check if required columns exist
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                raise ValueError(f"缺少必要的列: {missing_columns}")
            
            # Group by device and protocol
            devices = {}
            protocols = set()
            total_points = 0
            
            for _, row in df.iterrows():
                device_name = str(row["设备名称"]).strip()
                protocol_type = str(row["协议类型"]).strip().lower()
                ip_address = str(row["IP地址"]).strip()
                port = int(row["端口"]) if pd.notna(row["端口"]) else None
                point_name = str(row["数据点名称"]).strip()
                address = str(row["地址"]).strip()
                data_type = str(row["数据类型"]).strip()
                interval = int(row["采集间隔"]) if pd.notna(row["采集间隔"]) else 1000
                
                protocols.add(protocol_type)
                
                if device_name not in devices:
                    devices[device_name] = {
                        "name": device_name,
                        "protocol": protocol_type,
                        "connection": {
                            "host": ip_address,
                            "port": port
                        },
                        "points": [],
                        "interval": interval
                    }
                
                devices[device_name]["points"].append({
                    "name": point_name,
                    "address": address,
                    "data_type": data_type
                })
                total_points += 1
            
            # Generate process configurations
            process_configs = {}
            
            for device_name, device_config in devices.items():
                protocol = device_config["protocol"]
                
                if protocol == "modbus_tcp" or protocol == "modbus":
                    process_name = f"modbus_collector_{device_name.lower().replace(' ', '_')}"
                    process_configs[process_name] = {
                        "type": "modbus",
                        "command": ["python", "-m", "apps.collector.modbustcp_influx"],
                        "config_file": f"configs/modbus_{device_name.lower().replace(' ', '_')}_config.json",
                        "description": f"Modbus TCP数据采集进程 - {device_name}",
                        "auto_restart": True,
                        "max_restarts": 5,
                        "working_directory": "../project-data-acquisition"
                    }
                elif protocol == "opcua" or protocol == "opc_ua":
                    process_name = f"opcua_collector_{device_name.lower().replace(' ', '_')}"
                    process_configs[process_name] = {
                        "type": "opcua",
                        "command": ["python", "-m", "apps.collector.opcua_influx"],
                        "config_file": f"configs/opcua_{device_name.lower().replace(' ', '_')}_config.json",
                        "description": f"OPC UA数据采集进程 - {device_name}",
                        "auto_restart": True,
                        "max_restarts": 5,
                        "working_directory": "../project-data-acquisition"
                    }
                elif protocol == "melsoft" or protocol == "melsoft_a1e":
                    process_name = f"melsoft_collector_{device_name.lower().replace(' ', '_')}"
                    process_configs[process_name] = {
                        "type": "melsoft",
                        "command": ["python", "-m", "apps.collector.melseca1enet_influx"],
                        "config_file": f"configs/melsoft_{device_name.lower().replace(' ', '_')}_config.json",
                        "description": f"Melsoft A1E数据采集进程 - {device_name}",
                        "auto_restart": True,
                        "max_restarts": 3,
                        "working_directory": "../project-data-acquisition"
                    }
            
            return {
                "devices": devices,
                "processes": process_configs,
                "metadata": {
                    "total_devices": len(devices),
                    "total_points": total_points,
                    "protocols": list(protocols),
                    "generated_at": datetime.now().isoformat()
                }
            }
            
        except Exception as e:
            logger.error(f"Error parsing Excel config: {e}")
            raise
    
    async def _validate_parsed_config(self, config_data: Dict[str, Any]) -> ConfigValidation:
        """Validate parsed configuration"""
        errors = []
        warnings = []
        
        try:
            devices = config_data.get("devices", {})
            processes = config_data.get("processes", {})
            metadata = config_data.get("metadata", {})
            
            # Validate devices
            if not devices:
                errors.append("没有发现任何设备配置")
            
            for device_name, device_config in devices.items():
                # Check required fields
                if not device_config.get("protocol"):
                    errors.append(f"设备 {device_name} 缺少协议类型")
                
                if not device_config.get("connection", {}).get("host"):
                    errors.append(f"设备 {device_name} 缺少IP地址")
                
                if not device_config.get("points"):
                    warnings.append(f"设备 {device_name} 没有配置数据点")
                
                # Check sampling interval
                interval = device_config.get("interval", 1000)
                if interval < 100:
                    warnings.append(f"设备 {device_name} 采集间隔过短 ({interval}ms)，可能影响性能")
            
            # Validate processes
            if not processes:
                errors.append("没有生成任何数采进程配置")
            
            return ConfigValidation(
                is_valid=len(errors) == 0,
                errors=errors,
                warnings=warnings,
                summary=metadata
            )
            
        except Exception as e:
            logger.error(f"Error validating config: {e}")
            return ConfigValidation(
                is_valid=False,
                errors=[f"配置验证失败: {str(e)}"],
                warnings=[],
                summary={}
            )
    
    async def validate_config(self, config_id: str) -> ConfigValidation:
        """Validate configuration file by ID"""
        try:
            config_json_path = os.path.join(self.config_storage_path, f"{config_id}_config.json")
            
            if not os.path.exists(config_json_path):
                return ConfigValidation(
                    is_valid=False,
                    errors=[f"配置文件不存在: {config_id}"],
                    warnings=[],
                    summary={}
                )
            
            with open(config_json_path, "r", encoding="utf-8") as f:
                config_data = json.load(f)
            
            return await self._validate_parsed_config(config_data)
            
        except Exception as e:
            logger.error(f"Error validating config: {e}")
            return ConfigValidation(
                is_valid=False,
                errors=[f"验证配置时发生错误: {str(e)}"],
                warnings=[],
                summary={}
            )
    
    async def get_current_config(self) -> ConfigInfo:
        """Get current configuration"""
        try:
            if os.path.exists(self.current_config_path):
                with open(self.current_config_path, "r", encoding="utf-8") as f:
                    current_config = json.load(f)
                
                metadata = current_config.get("metadata", {})
                return ConfigInfo(
                    filename=current_config.get("filename", "unknown"),
                    version=current_config.get("version", "1.0"),
                    last_updated=datetime.fromisoformat(current_config.get("last_updated", datetime.now().isoformat())),
                    devices=metadata.get("total_devices", 0),
                    points=metadata.get("total_points", 0)
                )
            else:
                # No current config
                return ConfigInfo(
                    filename="无配置",
                    version="0.0",
                    last_updated=datetime.now(),
                    devices=0,
                    points=0
                )
        except Exception as e:
            logger.error(f"Error getting current config: {e}")
            raise
    
    async def get_config_history(self) -> ConfigHistory:
        """Get configuration history"""
        try:
            configs = []
            
            if os.path.exists(self.config_storage_path):
                for filename in os.listdir(self.config_storage_path):
                    if filename.endswith("_metadata.json"):
                        metadata_path = os.path.join(self.config_storage_path, filename)
                        with open(metadata_path, "r", encoding="utf-8") as f:
                            config_data = json.load(f)
                            
                        # Convert datetime strings back to datetime objects
                        config_data["upload_time"] = datetime.fromisoformat(config_data["upload_time"])
                        
                        config_file = ConfigFile(**config_data)
                        configs.append(config_file)
            
            # Sort by upload time, newest first
            configs.sort(key=lambda x: x.upload_time, reverse=True)
            
            return ConfigHistory(
                configs=configs,
                total_count=len(configs)
            )
            
        except Exception as e:
            logger.error(f"Error getting config history: {e}")
            raise
    
    async def apply_config(self, config_apply: ConfigApply) -> ConfigApplyResponse:
        """Apply configuration"""
        try:
            config_json_path = os.path.join(self.config_storage_path, f"{config_apply.config_id}_config.json")
            
            if not os.path.exists(config_json_path):
                return ConfigApplyResponse(
                    success=False,
                    message=f"配置文件不存在: {config_apply.config_id}"
                )
            
            with open(config_json_path, "r", encoding="utf-8") as f:
                config_data = json.load(f)
            
            # Update config status to active
            metadata_path = os.path.join(self.config_storage_path, f"{config_apply.config_id}_metadata.json")
            if os.path.exists(metadata_path):
                with open(metadata_path, "r", encoding="utf-8") as f:
                    metadata = json.load(f)
                metadata["status"] = "active"
                with open(metadata_path, "w", encoding="utf-8") as f:
                    json.dump(metadata, f, indent=2, default=str)
            
            # Set all other configs to pending
            for filename in os.listdir(self.config_storage_path):
                if filename.endswith("_metadata.json") and filename != f"{config_apply.config_id}_metadata.json":
                    other_metadata_path = os.path.join(self.config_storage_path, filename)
                    with open(other_metadata_path, "r", encoding="utf-8") as f:
                        other_metadata = json.load(f)
                    if other_metadata.get("status") == "active":
                        other_metadata["status"] = "pending"
                        with open(other_metadata_path, "w", encoding="utf-8") as f:
                            json.dump(other_metadata, f, indent=2, default=str)
            
            # Backup current config if requested
            backup_id = None
            if config_apply.backup_current and os.path.exists(self.current_config_path):
                backup_id = await self._backup_current_config()
            
            # Apply the configuration
            affected_processes = await self._apply_config_internal(config_apply.config_id, config_data)
            
            return ConfigApplyResponse(
                success=True,
                message=f"配置应用成功，影响了 {len(affected_processes)} 个进程",
                backup_id=backup_id,
                affected_processes=affected_processes
            )
            
        except Exception as e:
            logger.error(f"Error applying config: {e}")
            return ConfigApplyResponse(
                success=False,
                message=f"应用配置失败: {str(e)}"
            )
    
    async def _apply_config_internal(self, config_id: str, config_data: Dict[str, Any]) -> List[str]:
        """Internal method to apply configuration"""
        try:
            # Update process_config.json
            processes = config_data.get("processes", {})
            
            process_config_path = "configs/process_config.json"
            process_config = {"processes": processes}
            
            with open(process_config_path, "w", encoding="utf-8") as f:
                json.dump(process_config, f, indent=2, ensure_ascii=False)
            
            # Generate individual device config files
            devices = config_data.get("devices", {})
            for device_name, device_config in devices.items():
                protocol = device_config["protocol"]
                safe_name = device_name.lower().replace(' ', '_')
                
                device_config_data = {
                    "device": device_config,
                    "influxdb": {
                        "url": "http://localhost:8086",
                        "token": "iot-token-12345",
                        "org": "iot-org",
                        "bucket": "iot-data"
                    }
                }
                
                if protocol == "modbus_tcp" or protocol == "modbus":
                    config_file_path = f"configs/modbus_{safe_name}_config.json"
                elif protocol == "opcua" or protocol == "opc_ua":
                    config_file_path = f"configs/opcua_{safe_name}_config.json"
                elif protocol == "melsoft" or protocol == "melsoft_a1e":
                    config_file_path = f"configs/melsoft_{safe_name}_config.json"
                else:
                    config_file_path = f"configs/{protocol}_{safe_name}_config.json"
                
                with open(config_file_path, "w", encoding="utf-8") as f:
                    json.dump(device_config_data, f, indent=2, ensure_ascii=False)
            
            # Update current config
            current_config = {
                "config_id": config_id,
                "filename": f"config_{config_id}",
                "version": "1.0",
                "last_updated": datetime.now().isoformat(),
                "devices": config_data.get("devices", {}),
                "processes": processes,
                "metadata": config_data.get("metadata", {})
            }
            
            with open(self.current_config_path, "w", encoding="utf-8") as f:
                json.dump(current_config, f, indent=2, ensure_ascii=False)
            
            # Reload process manager configuration
            from core.enhanced_process_manager import enhanced_process_manager
            enhanced_process_manager.load_process_configs()
            
            return list(processes.keys())
            
        except Exception as e:
            logger.error(f"Error applying config internally: {e}")
            raise
    
    async def _backup_current_config(self) -> str:
        """Backup current configuration"""
        try:
            backup_id = f"backup_{int(datetime.now().timestamp())}"
            backup_path = os.path.join(self.config_storage_path, f"{backup_id}_config.json")
            
            # Copy current config to backup
            import shutil
            shutil.copy2(self.current_config_path, backup_path)
            
            return backup_id
            
        except Exception as e:
            logger.error(f"Error backing up current config: {e}")
            raise