from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional
from datetime import datetime
import logging

from models.data_models import (
    DataPoint, DeviceInfo, MeasurementInfo, DataQuery, 
    DataStats, RealTimeData, HistoricalData, 
    DeviceListResponse, MeasurementListResponse
)
from services.data_service import DataService

logger = logging.getLogger(__name__)
router = APIRouter()

def get_data_service() -> DataService:
    return DataService()

@router.get("/realtime", response_model=RealTimeData)
async def get_realtime_data(
    devices: Optional[List[str]] = Query(None),
    measurements: Optional[List[str]] = Query(None),
    limit: int = Query(100, ge=1, le=10000),
    data_service: DataService = Depends(get_data_service)
):
    """Get real-time data"""
    try:
        query = DataQuery(
            devices=devices,
            measurements=measurements,
            limit=limit
        )
        return await data_service.get_realtime_data(query)
    except Exception as e:
        logger.error(f"Error getting real-time data: {e}")
        raise HTTPException(status_code=500, detail="Failed to get real-time data")

@router.get("/history", response_model=HistoricalData)
async def get_historical_data(
    start_time: Optional[datetime] = Query(None),
    end_time: Optional[datetime] = Query(None),
    devices: Optional[List[str]] = Query(None),
    measurements: Optional[List[str]] = Query(None),
    limit: int = Query(1000, ge=1, le=10000),
    offset: int = Query(0, ge=0),
    data_service: DataService = Depends(get_data_service)
):
    """Get historical data"""
    try:
        query = DataQuery(
            start_time=start_time,
            end_time=end_time,
            devices=devices,
            measurements=measurements,
            limit=limit,
            offset=offset
        )
        return await data_service.get_historical_data(query)
    except Exception as e:
        logger.error(f"Error getting historical data: {e}")
        raise HTTPException(status_code=500, detail="Failed to get historical data")

@router.get("/statistics", response_model=DataStats)
async def get_data_statistics(
    data_service: DataService = Depends(get_data_service)
):
    """Get data statistics"""
    try:
        return await data_service.get_data_statistics()
    except Exception as e:
        logger.error(f"Error getting data statistics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get data statistics")

@router.get("/devices", response_model=DeviceListResponse)
async def get_devices(
    data_service: DataService = Depends(get_data_service)
):
    """Get device list"""
    try:
        return await data_service.get_devices()
    except Exception as e:
        logger.error(f"Error getting devices: {e}")
        raise HTTPException(status_code=500, detail="Failed to get devices")

@router.get("/measurements", response_model=MeasurementListResponse)
async def get_measurements(
    device_id: Optional[str] = Query(None),
    data_service: DataService = Depends(get_data_service)
):
    """Get measurement list"""
    try:
        return await data_service.get_measurements(device_id)
    except Exception as e:
        logger.error(f"Error getting measurements: {e}")
        raise HTTPException(status_code=500, detail="Failed to get measurements")