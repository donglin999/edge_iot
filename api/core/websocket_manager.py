import asyncio
import json
import logging
from typing import Dict, Set, List, Any
from fastapi import WebSocket, WebSocketDisconnect
from datetime import datetime
import weakref

logger = logging.getLogger(__name__)

class WebSocketManager:
    """WebSocket connection manager for real-time communication"""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.connection_subscriptions: Dict[str, Set[str]] = {}
        self.broadcast_task = None
        self.running = False
        
    async def start(self):
        """Start the WebSocket manager"""
        self.running = True
        self.broadcast_task = asyncio.create_task(self._broadcast_loop())
        logger.info("WebSocket manager started")
        
    async def stop(self):
        """Stop the WebSocket manager"""
        self.running = False
        if self.broadcast_task:
            self.broadcast_task.cancel()
            try:
                await self.broadcast_task
            except asyncio.CancelledError:
                pass
        
        # Close all connections
        for connection_id, websocket in self.active_connections.items():
            try:
                await websocket.close()
            except:
                pass
        
        self.active_connections.clear()
        self.connection_subscriptions.clear()
        logger.info("WebSocket manager stopped")
    
    async def connect(self, websocket: WebSocket, connection_id: str):
        """Accept a WebSocket connection"""
        await websocket.accept()
        self.active_connections[connection_id] = websocket
        self.connection_subscriptions[connection_id] = set()
        logger.info(f"WebSocket connection {connection_id} established")
        
    async def disconnect(self, connection_id: str):
        """Disconnect a WebSocket connection"""
        if connection_id in self.active_connections:
            try:
                await self.active_connections[connection_id].close()
            except:
                pass
            del self.active_connections[connection_id]
            del self.connection_subscriptions[connection_id]
            logger.info(f"WebSocket connection {connection_id} disconnected")
    
    async def subscribe(self, connection_id: str, topics: List[str]):
        """Subscribe a connection to specific topics"""
        if connection_id in self.connection_subscriptions:
            self.connection_subscriptions[connection_id].update(topics)
            logger.info(f"Connection {connection_id} subscribed to topics: {topics}")
    
    async def unsubscribe(self, connection_id: str, topics: List[str]):
        """Unsubscribe a connection from specific topics"""
        if connection_id in self.connection_subscriptions:
            self.connection_subscriptions[connection_id].difference_update(topics)
            logger.info(f"Connection {connection_id} unsubscribed from topics: {topics}")
    
    async def send_personal_message(self, connection_id: str, message: dict):
        """Send a message to a specific connection"""
        if connection_id in self.active_connections:
            try:
                await self.active_connections[connection_id].send_text(json.dumps(message))
            except Exception as e:
                logger.error(f"Error sending message to {connection_id}: {e}")
                await self.disconnect(connection_id)
    
    async def broadcast_to_topic(self, topic: str, message: dict):
        """Broadcast a message to all connections subscribed to a topic"""
        message_json = json.dumps(message)
        disconnected_connections = []
        
        for connection_id, subscriptions in self.connection_subscriptions.items():
            if topic in subscriptions:
                try:
                    await self.active_connections[connection_id].send_text(message_json)
                except Exception as e:
                    logger.error(f"Error broadcasting to {connection_id}: {e}")
                    disconnected_connections.append(connection_id)
        
        # Clean up disconnected connections
        for connection_id in disconnected_connections:
            await self.disconnect(connection_id)
    
    async def broadcast_to_all(self, message: dict):
        """Broadcast a message to all active connections"""
        message_json = json.dumps(message)
        disconnected_connections = []
        
        for connection_id, websocket in self.active_connections.items():
            try:
                await websocket.send_text(message_json)
            except Exception as e:
                logger.error(f"Error broadcasting to {connection_id}: {e}")
                disconnected_connections.append(connection_id)
        
        # Clean up disconnected connections
        for connection_id in disconnected_connections:
            await self.disconnect(connection_id)
    
    async def _broadcast_loop(self):
        """Background task for periodic broadcasts"""
        while self.running:
            try:
                # Broadcast system status every 5 seconds
                await asyncio.sleep(5)
                
                if self.active_connections:
                    status_message = {
                        "type": "system_status",
                        "timestamp": datetime.now().isoformat(),
                        "data": {
                            "active_connections": len(self.active_connections),
                            "server_time": datetime.now().isoformat()
                        }
                    }
                    await self.broadcast_to_topic("system", status_message)
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in broadcast loop: {e}")
                await asyncio.sleep(1)
    
    def get_connection_stats(self) -> dict:
        """Get connection statistics"""
        return {
            "total_connections": len(self.active_connections),
            "connections": list(self.active_connections.keys()),
            "subscription_stats": {
                topic: len([c for c, subs in self.connection_subscriptions.items() if topic in subs])
                for topic in set().union(*self.connection_subscriptions.values())
            }
        }

# Global WebSocket manager instance
websocket_manager = WebSocketManager()