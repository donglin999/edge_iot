from fastapi import APIRouter, HTTPException, Depends, File, UploadFile
from typing import List, Optional
import logging

from models.config_models import (
    ConfigFile, ConfigValidation, ConfigApply, ConfigHistory,
    ConfigUploadResponse, ConfigApplyResponse, ConfigRollback, ConfigRollbackResponse
)
from services.config_service import ConfigService

logger = logging.getLogger(__name__)
router = APIRouter()

def get_config_service() -> ConfigService:
    return ConfigService()

@router.post("/upload", response_model=ConfigUploadResponse)
async def upload_config(
    file: UploadFile = File(...),
    description: Optional[str] = None,
    apply_immediately: bool = False,
    config_service: ConfigService = Depends(get_config_service)
):
    """Upload Excel configuration file"""
    try:
        return await config_service.upload_config(file, description, apply_immediately)
    except Exception as e:
        logger.error(f"Error uploading config: {e}")
        raise HTTPException(status_code=500, detail="Failed to upload config")

@router.get("/current", response_model=ConfigFile)
async def get_current_config(
    config_service: ConfigService = Depends(get_config_service)
):
    """Get current configuration"""
    try:
        return await config_service.get_current_config()
    except Exception as e:
        logger.error(f"Error getting current config: {e}")
        raise HTTPException(status_code=500, detail="Failed to get current config")

@router.get("/history", response_model=ConfigHistory)
async def get_config_history(
    config_service: ConfigService = Depends(get_config_service)
):
    """Get configuration history"""
    try:
        return await config_service.get_config_history()
    except Exception as e:
        logger.error(f"Error getting config history: {e}")
        raise HTTPException(status_code=500, detail="Failed to get config history")

@router.post("/apply", response_model=ConfigApplyResponse)
async def apply_config(
    config_apply: ConfigApply,
    config_service: ConfigService = Depends(get_config_service)
):
    """Apply configuration"""
    try:
        return await config_service.apply_config(config_apply)
    except Exception as e:
        logger.error(f"Error applying config: {e}")
        raise HTTPException(status_code=500, detail="Failed to apply config")

@router.get("/validate/{config_id}", response_model=ConfigValidation)
async def validate_config(
    config_id: str,
    config_service: ConfigService = Depends(get_config_service)
):
    """Validate configuration file"""
    try:
        return await config_service.validate_config(config_id)
    except Exception as e:
        logger.error(f"Error validating config: {e}")
        raise HTTPException(status_code=500, detail="Failed to validate config")