from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from typing import List, Optional
import json
import uuid
import logging

from core.websocket_manager import websocket_manager

logger = logging.getLogger(__name__)
router = APIRouter()

@router.websocket("/connect")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time communication"""
    connection_id = str(uuid.uuid4())
    
    try:
        await websocket_manager.connect(websocket, connection_id)
        
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Handle different message types
            if message.get("type") == "subscribe":
                topics = message.get("topics", [])
                await websocket_manager.subscribe(connection_id, topics)
                await websocket_manager.send_personal_message(
                    connection_id, 
                    {
                        "type": "subscription_confirmed",
                        "topics": topics,
                        "timestamp": "2023-01-01T12:00:00"
                    }
                )
            
            elif message.get("type") == "unsubscribe":
                topics = message.get("topics", [])
                await websocket_manager.unsubscribe(connection_id, topics)
                await websocket_manager.send_personal_message(
                    connection_id,
                    {
                        "type": "unsubscription_confirmed",
                        "topics": topics,
                        "timestamp": "2023-01-01T12:00:00"
                    }
                )
            
            elif message.get("type") == "ping":
                await websocket_manager.send_personal_message(
                    connection_id,
                    {
                        "type": "pong",
                        "timestamp": "2023-01-01T12:00:00"
                    }
                )
                
    except WebSocketDisconnect:
        logger.info(f"WebSocket connection {connection_id} disconnected")
    except Exception as e:
        logger.error(f"WebSocket error for connection {connection_id}: {e}")
    finally:
        await websocket_manager.disconnect(connection_id)

@router.get("/stats")
async def get_websocket_stats():
    """Get WebSocket connection statistics"""
    return websocket_manager.get_connection_stats()