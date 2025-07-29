from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional
from datetime import datetime
import logging

from models.process_models import (
    ProcessInfo, ProcessControl, ProcessListResponse, 
    ProcessControlResponse, ProcessLog, ProcessLogResponse
)
from services.process_service import ProcessService

logger = logging.getLogger(__name__)
router = APIRouter()

def get_process_service() -> ProcessService:
    return ProcessService()

@router.get("/", response_model=ProcessListResponse)
async def get_processes(
    process_service: ProcessService = Depends(get_process_service)
):
    """Get all processes status"""
    try:
        return await process_service.get_all_processes()
    except Exception as e:
        logger.error(f"Error getting processes: {e}")
        raise HTTPException(status_code=500, detail="Failed to get processes")

@router.post("/reload-config")
async def reload_config(
    process_service: ProcessService = Depends(get_process_service)
):
    """重新加载进程配置"""
    try:
        process_service.process_manager.reload_config()
        processes_data = process_service.process_manager.get_all_processes()
        return {
            "success": True,
            "message": f"配置重新加载成功，当前有 {len(processes_data)} 个进程",
            "processes": list(processes_data.keys())
        }
    except Exception as e:
        logger.error(f"重新加载配置失败: {e}")
        raise HTTPException(status_code=500, detail=f"重新加载配置失败: {str(e)}")

@router.post("/clear-cache")
async def clear_cache(
    process_service: ProcessService = Depends(get_process_service)
):
    """清除进程数据缓存"""
    try:
        process_service.clear_cache()
        return {
            "success": True,
            "message": "缓存已清除，下次请求将获取最新数据"
        }
    except Exception as e:
        logger.error(f"清除缓存失败: {e}")
        raise HTTPException(status_code=500, detail=f"清除缓存失败: {str(e)}")

@router.post("/start", response_model=ProcessControlResponse)
async def start_processes(
    control: ProcessControl,
    process_service: ProcessService = Depends(get_process_service)
):
    """Start processes"""
    try:
        return await process_service.start_processes(control.process_names)
    except Exception as e:
        logger.error(f"Error starting processes: {e}")
        raise HTTPException(status_code=500, detail="Failed to start processes")

@router.post("/stop", response_model=ProcessControlResponse)
async def stop_processes(
    control: ProcessControl,
    process_service: ProcessService = Depends(get_process_service)
):
    """Stop processes"""
    try:
        return await process_service.stop_processes(control.process_names)
    except Exception as e:
        logger.error(f"Error stopping processes: {e}")
        raise HTTPException(status_code=500, detail="Failed to stop processes")

@router.post("/restart", response_model=ProcessControlResponse)
async def restart_processes(
    control: ProcessControl,
    process_service: ProcessService = Depends(get_process_service)
):
    """Restart processes"""
    try:
        return await process_service.restart_processes(control.process_names)
    except Exception as e:
        logger.error(f"Error restarting processes: {e}")
        raise HTTPException(status_code=500, detail="Failed to restart processes")

@router.get("/{process_name}/status", response_model=ProcessInfo)
async def get_process_status(
    process_name: str,
    process_service: ProcessService = Depends(get_process_service)
):
    """Get specific process status"""
    try:
        process_info = await process_service.get_process_status(process_name)
        if not process_info:
            raise HTTPException(status_code=404, detail=f"Process {process_name} not found")
        return process_info
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting process status: {e}")
        raise HTTPException(status_code=500, detail="Failed to get process status")

@router.get("/{process_name}/logs", response_model=ProcessLogResponse)
async def get_process_logs(
    process_name: str,
    lines: int = Query(100, ge=1, le=10000),
    page: int = Query(1, ge=1),
    process_service: ProcessService = Depends(get_process_service)
):
    """Get process logs"""
    try:
        return await process_service.get_process_logs(process_name, lines, page)
    except Exception as e:
        logger.error(f"Error getting process logs: {e}")
        raise HTTPException(status_code=500, detail="Failed to get process logs")