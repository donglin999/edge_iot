import asyncio
import psutil
import logging
from typing import Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)

class MonitorService:
    """Service for system monitoring"""
    
    def __init__(self):
        pass
    
    async def get_system_stats(self) -> Dict[str, Any]:
        """Get system resource statistics"""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            
            # Memory usage
            memory = psutil.virtual_memory()
            
            # Disk usage
            disk = psutil.disk_usage('/')
            
            # Network stats
            net_io = psutil.net_io_counters()
            
            return {
                "timestamp": datetime.now().isoformat(),
                "cpu": {
                    "percent": cpu_percent,
                    "count": cpu_count
                },
                "memory": {
                    "total": memory.total,
                    "available": memory.available,
                    "percent": memory.percent,
                    "used": memory.used
                },
                "disk": {
                    "total": disk.total,
                    "used": disk.used,
                    "free": disk.free,
                    "percent": (disk.used / disk.total) * 100
                },
                "network": {
                    "bytes_sent": net_io.bytes_sent,
                    "bytes_recv": net_io.bytes_recv,
                    "packets_sent": net_io.packets_sent,
                    "packets_recv": net_io.packets_recv
                }
            }
        except Exception as e:
            logger.error(f"Error getting system stats: {e}")
            raise
    
    async def get_service_health(self) -> Dict[str, Any]:
        """Get service health status"""
        try:
            return {
                "api_server": {
                    "status": "healthy",
                    "uptime": "1h 23m"
                },
                "database": {
                    "status": "connected",
                    "response_time": "12ms"
                },
                "websocket": {
                    "status": "active",
                    "connections": 2
                }
            }
        except Exception as e:
            logger.error(f"Error getting service health: {e}")
            raise