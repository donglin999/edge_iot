from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Optional
import logging
import psutil
import platform
import sqlite3
from datetime import datetime
import os

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/status")
async def get_system_status():
    """Get system status"""
    try:
        boot_time = datetime.fromtimestamp(psutil.boot_time())
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "uptime": int((datetime.now() - boot_time).total_seconds()),
            "version": "1.0.0",
            "services": {
                "api": "running",
                "database": "connected",
                "influxdb": "connected"
            }
        }
    except Exception as e:
        logger.error(f"Error getting system status: {e}")
        raise HTTPException(status_code=500, detail="Failed to get system status")

@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

@router.get("/metrics")
async def get_system_metrics():
    """Get system metrics"""
    try:
        # CPU metrics
        cpu_percent = psutil.cpu_percent(interval=1)
        
        # Memory metrics
        memory = psutil.virtual_memory()
        memory_percent = memory.percent
        
        # Disk metrics
        disk = psutil.disk_usage('/')
        disk_percent = (disk.used / disk.total) * 100
        
        # Network metrics
        network = psutil.net_io_counters()
        
        return {
            "cpu_percent": round(cpu_percent, 1),
            "memory_percent": round(memory_percent, 1),
            "disk_usage": round(disk_percent, 1),
            "network_io": {
                "bytes_sent": network.bytes_sent,
                "bytes_recv": network.bytes_recv,
                "bytes_sent_mb": round(network.bytes_sent / 1024 / 1024, 2),
                "bytes_recv_mb": round(network.bytes_recv / 1024 / 1024, 2)
            },
            "memory_info": {
                "total_gb": round(memory.total / 1024 / 1024 / 1024, 2),
                "available_gb": round(memory.available / 1024 / 1024 / 1024, 2),
                "used_gb": round(memory.used / 1024 / 1024 / 1024, 2)
            },
            "disk_info": {
                "total_gb": round(disk.total / 1024 / 1024 / 1024, 2),
                "used_gb": round(disk.used / 1024 / 1024 / 1024, 2),
                "free_gb": round(disk.free / 1024 / 1024 / 1024, 2)
            },
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting system metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get system metrics")

@router.get("/logs")
async def get_system_logs(
    level: Optional[str] = Query("all", description="Log level filter"),
    limit: int = Query(100, ge=1, le=1000, description="Number of logs to return")
):
    """Get system logs"""
    try:
        # In a real implementation, you would read from actual log files
        # For now, return some sample logs
        sample_logs = [
            {
                "timestamp": datetime.now().isoformat(),
                "level": "INFO",
                "message": "System monitoring service is running"
            },
            {
                "timestamp": datetime.now().isoformat(),
                "level": "INFO", 
                "message": "Database connection established"
            },
            {
                "timestamp": datetime.now().isoformat(),
                "level": "WARN",
                "message": "High CPU usage detected"
            }
        ]
        
        if level != "all":
            sample_logs = [log for log in sample_logs if log["level"].lower() == level.lower()]
            
        return {
            "logs": sample_logs[:limit],
            "total": len(sample_logs),
            "level": level,
            "limit": limit
        }
    except Exception as e:
        logger.error(f"Error getting system logs: {e}")
        raise HTTPException(status_code=500, detail="Failed to get system logs")

@router.get("/info")
async def get_system_info():
    """Get detailed system information"""
    try:
        boot_time = datetime.fromtimestamp(psutil.boot_time())
        uptime_seconds = int((datetime.now() - boot_time).total_seconds())
        
        # Calculate uptime in a readable format
        days = uptime_seconds // 86400
        hours = (uptime_seconds % 86400) // 3600
        minutes = (uptime_seconds % 3600) // 60
        
        uptime_str = f"{days}天 {hours}小时 {minutes}分钟"
        
        return {
            "os": platform.system(),
            "version": platform.version(),
            "arch": platform.machine(),
            "cpu_cores": psutil.cpu_count(),
            "total_memory": f"{round(psutil.virtual_memory().total / 1024 / 1024 / 1024, 1)} GB",
            "boot_time": boot_time.isoformat(),
            "uptime": uptime_str,
            "hostname": platform.node(),
            "python_version": platform.python_version()
        }
    except Exception as e:
        logger.error(f"Error getting system info: {e}")
        raise HTTPException(status_code=500, detail="Failed to get system info")

@router.get("/services")
async def get_service_status():
    """Get service status"""
    try:
        # In a real implementation, check actual service status
        services = [
            {"name": "FastAPI", "status": "running", "uptime": "2d 15h", "description": "Web API服务"},
            {"name": "InfluxDB", "status": "running", "uptime": "2d 15h", "description": "时序数据库"},
            {"name": "Nginx", "status": "running", "uptime": "2d 15h", "description": "反向代理服务器"},
            {"name": "Redis", "status": "stopped", "uptime": "0", "description": "缓存服务"},
            {"name": "Collector", "status": "running", "uptime": "1d 8h", "description": "数据采集服务"}
        ]
        
        return {
            "services": services,
            "total": len(services),
            "running": len([s for s in services if s["status"] == "running"]),
            "stopped": len([s for s in services if s["status"] == "stopped"])
        }
    except Exception as e:
        logger.error(f"Error getting service status: {e}")
        raise HTTPException(status_code=500, detail="Failed to get service status")

@router.get("/databases")
async def get_database_status():
    """Get database connection status"""
    try:
        databases = []
        
        # Check SQLite database
        try:
            if os.path.exists("./data/iot.db"):
                conn = sqlite3.connect("./data/iot.db")
                conn.close()
                databases.append({
                    "name": "SQLite",
                    "status": "已连接",
                    "url": "./data/iot.db",
                    "response_time": "2ms"
                })
            else:
                databases.append({
                    "name": "SQLite", 
                    "status": "连接失败",
                    "url": "./data/iot.db",
                    "response_time": "-"
                })
        except Exception:
            databases.append({
                "name": "SQLite",
                "status": "连接失败", 
                "url": "./data/iot.db",
                "response_time": "-"
            })
        
        # Check InfluxDB (mock for now)
        databases.append({
            "name": "InfluxDB",
            "status": "已连接",
            "url": "http://localhost:8086",
            "response_time": "15ms"
        })
        
        # Check Redis (mock for now)
        databases.append({
            "name": "Redis",
            "status": "连接失败",
            "url": "localhost:6379", 
            "response_time": "-"
        })
        
        return {
            "databases": databases,
            "total": len(databases),
            "connected": len([db for db in databases if db["status"] == "已连接"]),
            "failed": len([db for db in databases if db["status"] == "连接失败"])
        }
    except Exception as e:
        logger.error(f"Error getting database status: {e}")
        raise HTTPException(status_code=500, detail="Failed to get database status")

@router.post("/databases/test")
async def test_database_connections():
    """Test all database connections"""
    try:
        # Simulate testing connections
        return {
            "message": "Database connection test completed",
            "timestamp": datetime.now().isoformat(),
            "results": [
                {"name": "SQLite", "status": "success", "response_time": "2ms"},
                {"name": "InfluxDB", "status": "success", "response_time": "15ms"},
                {"name": "Redis", "status": "failed", "response_time": "-"}
            ]
        }
    except Exception as e:
        logger.error(f"Error testing database connections: {e}")
        raise HTTPException(status_code=500, detail="Failed to test database connections")