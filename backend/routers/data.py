from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging

from services.data_service import DataService

logger = logging.getLogger(__name__)
router = APIRouter()

def get_data_service() -> DataService:
    return DataService()

@router.get("/realtime")
async def get_realtime_data(
    device: Optional[str] = Query(None, description="Device ID filter"),
    measurements: Optional[List[str]] = Query(None, description="Measurement filters"),
    limit: int = Query(100, ge=1, le=1000, description="Limit results"),
    data_service: DataService = Depends(get_data_service)
):
    """Get real-time data from InfluxDB"""
    try:
        query_params = {
            "device": device,
            "measurements": measurements,
            "limit": limit
        }
        return await data_service.get_realtime_data(query_params)
    except Exception as e:
        logger.error(f"Error getting real-time data: {e}")
        raise HTTPException(status_code=500, detail="Failed to get real-time data")

@router.get("/statistics")
async def get_data_statistics(
    data_service: DataService = Depends(get_data_service)
):
    """Get data statistics from InfluxDB"""
    try:
        return await data_service.get_statistics()
    except Exception as e:
        logger.error(f"Error getting data statistics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get data statistics")

@router.get("/devices")
async def get_devices(
    data_service: DataService = Depends(get_data_service)
):
    """Get device list from InfluxDB"""
    try:
        return await data_service.get_devices()
    except Exception as e:
        logger.error(f"Error getting devices: {e}")
        raise HTTPException(status_code=500, detail="Failed to get devices")

@router.get("/measurements")
async def get_measurements(
    device_id: Optional[str] = Query(None, description="Device ID to filter measurements"),
    data_service: DataService = Depends(get_data_service)
):
    """Get measurement list from InfluxDB"""
    try:
        measurements = await data_service.get_measurements(device_id)
        return measurements
    except Exception as e:
        logger.error(f"Error getting measurements: {e}")
        raise HTTPException(status_code=500, detail="Failed to get measurements")

@router.post("/export")
async def export_data(
    request: Dict[str, Any],
    data_service: DataService = Depends(get_data_service)
):
    """Export data in specified format"""
    try:
        query_params = request.get("query", {})
        format_type = request.get("format", "csv")
        
        result = await data_service.export_data(query_params, format_type)
        
        return {
            "data": result,
            "format": format_type,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error exporting data: {e}")
        raise HTTPException(status_code=500, detail="Failed to export data")

@router.get("/database/status")
async def get_database_status(
    data_service: DataService = Depends(get_data_service)
):
    """Get database connection status"""
    try:
        return await data_service.get_database_status()
    except Exception as e:
        logger.error(f"Error getting database status: {e}")
        raise HTTPException(status_code=500, detail="Failed to get database status")