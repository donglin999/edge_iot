import asyncio
import json
import logging
from typing import Dict, Set, List, Any, Optional, Union, Callable, TypeVar, Generic
from fastapi import WebSocket, WebSocketDisconnect
from datetime import datetime
import weakref
from models.websocket_models import (
    WebSocketMessageType, 
    SubscriptionTopic, 
    WebSocketMessage,
    ProcessStatusUpdateMessage,
    HealthCheckResultMessage,
    PerformanceMetricsMessage,
    SubscriptionMessage,
    UnsubscriptionMessage
)
from models.process_models import (
    ProcessInfo, 
    EnhancedProcessInfo, 
    HealthStatus, 
    ConnectionStatus,
    ProcessState,
    PerformanceMetrics
)

logger = logging.getLogger(__name__)

class WebSocketManager:
    """Enhanced WebSocket connection manager for real-time communication with topic subscription support"""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.connection_subscriptions: Dict[str, Set[str]] = {}
        self.broadcast_task = None
        self.running = False
        self.message_queue = asyncio.Queue()
        self.message_processor_task = None
        self.topic_handlers: Dict[str, List[Callable]] = {
            topic.value: [] for topic in SubscriptionTopic
        }
        # Message history buffer for each topic (last 10 messages)
        self.message_history: Dict[str, List[dict]] = {
            topic.value: [] for topic in SubscriptionTopic
        }
        self.max_history_size = 10
        # Track process status changes for detecting transitions
        self.process_status_cache: Dict[str, Dict[str, Any]] = {}
        
    async def start(self):
        """Start the WebSocket manager"""
        self.running = True
        self.broadcast_task = asyncio.create_task(self._broadcast_loop())
        self.message_processor_task = asyncio.create_task(self._process_message_queue())
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
                
        if self.message_processor_task:
            self.message_processor_task.cancel()
            try:
                await self.message_processor_task
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
        
        # Send welcome message with available topics
        welcome_message = {
            "type": "welcome",
            "timestamp": datetime.now().isoformat(),
            "data": {
                "message": "Connection established",
                "available_topics": [topic.value for topic in SubscriptionTopic],
                "connection_id": connection_id
            }
        }
        await self.send_personal_message(connection_id, welcome_message)
        
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
            
            # Send subscription confirmation
            confirmation = {
                "type": WebSocketMessageType.SUBSCRIPTION_CONFIRMED,
                "timestamp": datetime.now().isoformat(),
                "data": {
                    "topics": topics,
                    "active_subscriptions": list(self.connection_subscriptions[connection_id])
                }
            }
            await self.send_personal_message(connection_id, confirmation)
            
            # Send recent message history for each subscribed topic
            for topic in topics:
                if topic in self.message_history and self.message_history[topic]:
                    for history_message in self.message_history[topic]:
                        # Add history flag to indicate this is a historical message
                        history_message_copy = history_message.copy()
                        if "data" not in history_message_copy:
                            history_message_copy["data"] = {}
                        history_message_copy["data"]["is_history"] = True
                        await self.send_personal_message(connection_id, history_message_copy)
    
    async def unsubscribe(self, connection_id: str, topics: List[str]):
        """Unsubscribe a connection from specific topics"""
        if connection_id in self.connection_subscriptions:
            self.connection_subscriptions[connection_id].difference_update(topics)
            logger.info(f"Connection {connection_id} unsubscribed from topics: {topics}")
            
            # Send unsubscription confirmation
            confirmation = {
                "type": WebSocketMessageType.UNSUBSCRIPTION_CONFIRMED,
                "timestamp": datetime.now().isoformat(),
                "data": {
                    "topics": topics,
                    "active_subscriptions": list(self.connection_subscriptions[connection_id])
                }
            }
            await self.send_personal_message(connection_id, confirmation)
            
    async def handle_client_message(self, connection_id: str, message_text: str):
        """Handle incoming messages from clients"""
        try:
            message_data = json.loads(message_text)
            message_type = message_data.get("type", "")
            
            if message_type == "subscribe":
                # Handle subscription request
                topics = message_data.get("topics", [])
                if topics:
                    await self.subscribe(connection_id, topics)
            
            elif message_type == "unsubscribe":
                # Handle unsubscription request
                topics = message_data.get("topics", [])
                if topics:
                    await self.unsubscribe(connection_id, topics)
            
            elif message_type == "ping":
                # Handle ping request
                await self.send_personal_message(connection_id, {
                    "type": WebSocketMessageType.PONG,
                    "timestamp": datetime.now().isoformat(),
                    "data": {"server_time": datetime.now().isoformat()}
                })
                
            else:
                logger.warning(f"Unknown message type from client {connection_id}: {message_type}")
                
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON from client {connection_id}: {message_text}")
        except Exception as e:
            logger.error(f"Error handling client message from {connection_id}: {e}")
    
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
                for topic in set().union(*self.connection_subscriptions.values()) if self.connection_subscriptions
            }
        }
    
    async def _process_message_queue(self):
        """Background task for processing messages in the queue"""
        while self.running:
            try:
                # Get message from queue
                message = await self.message_queue.get()
                
                # Process message based on topic
                topic = message.get("topic", "all")
                
                # Execute any registered handlers for this topic
                if topic in self.topic_handlers:
                    for handler in self.topic_handlers[topic]:
                        try:
                            await handler(message)
                        except Exception as e:
                            logger.error(f"Error in topic handler for {topic}: {e}")
                
                # Broadcast to subscribers
                await self.broadcast_to_topic(topic, message)
                
                # Mark task as done
                self.message_queue.task_done()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error processing message: {e}")
                await asyncio.sleep(0.1)
    
    async def publish_message(self, topic: str, message_type: WebSocketMessageType, data: dict):
        """Publish a message to a specific topic"""
        message = {
            "type": message_type,
            "topic": topic,
            "timestamp": datetime.now().isoformat(),
            "data": data
        }
        
        # Store message in history buffer
        if topic in self.message_history:
            self.message_history[topic].append(message)
            # Trim history if it exceeds max size
            if len(self.message_history[topic]) > self.max_history_size:
                self.message_history[topic] = self.message_history[topic][-self.max_history_size:]
        
        await self.message_queue.put(message)
        return message
    
    def register_topic_handler(self, topic: str, handler: Callable):
        """Register a handler function for a specific topic"""
        if topic in self.topic_handlers:
            self.topic_handlers[topic].append(handler)
            logger.info(f"Handler registered for topic: {topic}")
        else:
            logger.warning(f"Attempted to register handler for unknown topic: {topic}")
    
    def unregister_topic_handler(self, topic: str, handler: Callable):
        """Unregister a handler function for a specific topic"""
        if topic in self.topic_handlers and handler in self.topic_handlers[topic]:
            self.topic_handlers[topic].remove(handler)
            logger.info(f"Handler unregistered for topic: {topic}")
    
    # Process status update methods
    async def publish_process_status_update(self, process_info: Union[ProcessInfo, EnhancedProcessInfo]):
        """Publish a process status update message"""
        # Convert to dict if it's a dataclass
        if hasattr(process_info, "__dataclass_fields__"):
            # Handle dataclass conversion
            data = {
                "process_name": process_info.name,
                "status": process_info.status,
                "pid": process_info.pid,
                "cpu_percent": process_info.cpu_percent,
                "memory_mb": process_info.memory_mb,
                "uptime_seconds": process_info.uptime_seconds if hasattr(process_info, "uptime_seconds") else 0,
                "health_score": process_info.health_score,
                "connection_status": process_info.connection_info.status.value if hasattr(process_info, "connection_info") and process_info.connection_info else "unknown",
                "last_error": process_info.last_error
            }
        else:
            # Handle Pydantic model
            data = {
                "process_name": process_info.name,
                "status": process_info.status,
                "pid": process_info.pid,
                "cpu_percent": process_info.cpu_percent,
                "memory_mb": process_info.memory_mb,
                "uptime_seconds": process_info.uptime,
                "health_score": process_info.health_score,
                "connection_status": process_info.connection_status,
                "last_error": process_info.last_error
            }
        
        # Check for status changes and add transition information
        process_name = process_info.name
        current_status = data["status"]
        
        # Detect status changes
        status_changed = False
        previous_status = None
        
        if process_name in self.process_status_cache:
            previous_status = self.process_status_cache[process_name].get("status")
            if previous_status != current_status:
                status_changed = True
                data["status_changed"] = True
                data["previous_status"] = previous_status
                data["status_change_time"] = datetime.now().isoformat()
                
                # Add special notification for important transitions
                if current_status in ["error", "crashed"] or (previous_status == "running" and current_status == "stopped"):
                    # Create a separate error alert message for critical status changes
                    await self.publish_message(
                        topic=SubscriptionTopic.ERROR_ALERTS.value,
                        message_type=WebSocketMessageType.ERROR_ALERT,
                        data={
                            "process_name": process_name,
                            "alert_type": "status_change",
                            "severity": "critical" if current_status in ["error", "crashed"] else "warning",
                            "message": f"Process {process_name} changed from {previous_status} to {current_status}",
                            "timestamp": datetime.now().isoformat(),
                            "details": {
                                "previous_status": previous_status,
                                "current_status": current_status,
                                "last_error": data.get("last_error")
                            }
                        }
                    )
        
        # Update cache with current status
        if process_name not in self.process_status_cache:
            self.process_status_cache[process_name] = {}
        self.process_status_cache[process_name].update(data)
        
        return await self.publish_message(
            topic=SubscriptionTopic.PROCESS_STATUS.value,
            message_type=WebSocketMessageType.PROCESS_STATUS_UPDATE,
            data=data
        )
    
    # Health check update methods
    async def publish_health_check_result(self, process_name: str, check_type: str, 
                                         status: HealthStatus, details: dict, 
                                         score: float, recommendations: List[str] = None):
        """Publish a health check result message"""
        data = {
            "process_name": process_name,
            "check_type": check_type,
            "status": status.value if isinstance(status, HealthStatus) else status,
            "details": details,
            "score": score,
            "recommendations": recommendations or []
        }
        
        # Check if this is a critical health check result
        is_critical = (isinstance(status, HealthStatus) and status == HealthStatus.CRITICAL) or \
                     (isinstance(status, str) and status.lower() == "critical")
        
        # For critical health checks, also send an error alert
        if is_critical:
            await self.publish_message(
                topic=SubscriptionTopic.ERROR_ALERTS.value,
                message_type=WebSocketMessageType.ERROR_ALERT,
                data={
                    "process_name": process_name,
                    "alert_type": "health_check",
                    "severity": "critical",
                    "message": f"Critical health check failure for {process_name}: {check_type}",
                    "timestamp": datetime.now().isoformat(),
                    "details": {
                        "check_type": check_type,
                        "score": score,
                        "details": details,
                        "recommendations": recommendations or []
                    }
                }
            )
        
        return await self.publish_message(
            topic=SubscriptionTopic.HEALTH_CHECKS.value,
            message_type=WebSocketMessageType.HEALTH_CHECK_RESULT,
            data=data
        )
    
    # Performance metrics update methods
    async def publish_performance_metrics(self, metrics: PerformanceMetrics):
        """Publish performance metrics message"""
        # Convert to dict if it's a dataclass
        if hasattr(metrics, "__dataclass_fields__"):
            data = {
                "process_name": metrics.process_name,
                "timestamp": metrics.timestamp.isoformat(),
                "cpu_percent": metrics.cpu_percent,
                "memory_mb": metrics.memory_mb,
                "data_points_per_minute": metrics.data_points_per_minute,
                "error_rate": metrics.error_rate,
                "response_time_ms": metrics.response_time_ms
            }
        else:
            data = metrics.dict()
            if "timestamp" in data and isinstance(data["timestamp"], datetime):
                data["timestamp"] = data["timestamp"].isoformat()
        
        return await self.publish_message(
            topic=SubscriptionTopic.PERFORMANCE.value,
            message_type=WebSocketMessageType.PERFORMANCE_METRICS,
            data=data
        )
        
    # Connection status update methods
    async def publish_connection_status_update(self, process_name: str, connection_info: Union[ConnectionInfo, Dict[str, Any]]):
        """Publish connection status update message"""
        # Convert to dict if it's a dataclass
        if hasattr(connection_info, "__dataclass_fields__"):
            data = {
                "process_name": process_name,
                "device_ip": connection_info.device_ip,
                "device_port": connection_info.device_port,
                "is_connected": connection_info.is_connected,
                "last_connect_time": connection_info.last_connect_time.isoformat() if connection_info.last_connect_time else None,
                "connection_errors": connection_info.connection_errors,
                "protocol_type": connection_info.protocol_type,
                "status": connection_info.status.value if hasattr(connection_info.status, "value") else connection_info.status
            }
        else:
            data = {
                "process_name": process_name,
                **connection_info
            }
            if "last_connect_time" in data and isinstance(data["last_connect_time"], datetime):
                data["last_connect_time"] = data["last_connect_time"].isoformat()
        
        # Check for connection status changes
        connection_key = f"{process_name}_connection"
        previous_status = None
        status_changed = False
        
        if connection_key in self.process_status_cache:
            previous_status = self.process_status_cache[connection_key].get("status")
            current_status = data.get("status")
            
            if previous_status != current_status:
                status_changed = True
                data["status_changed"] = True
                data["previous_status"] = previous_status
                data["status_change_time"] = datetime.now().isoformat()
                
                # Add special notification for connection status changes
                if current_status in ["error", "disconnected"] or (previous_status == "connected" and current_status != "connected"):
                    # Create a separate error alert for connection issues
                    await self.publish_message(
                        topic=SubscriptionTopic.ERROR_ALERTS.value,
                        message_type=WebSocketMessageType.ERROR_ALERT,
                        data={
                            "process_name": process_name,
                            "alert_type": "connection_change",
                            "severity": "critical" if current_status in ["error"] else "warning",
                            "message": f"Connection for {process_name} changed from {previous_status} to {current_status}",
                            "timestamp": datetime.now().isoformat(),
                            "details": {
                                "device_ip": data.get("device_ip"),
                                "device_port": data.get("device_port"),
                                "protocol_type": data.get("protocol_type"),
                                "previous_status": previous_status,
                                "current_status": current_status,
                                "connection_errors": data.get("connection_errors", 0)
                            }
                        }
                    )
        
        # Update cache with current connection status
        self.process_status_cache[connection_key] = data
        
        return await self.publish_message(
            topic=SubscriptionTopic.PROCESS_STATUS.value,
            message_type=WebSocketMessageType.CONNECTION_STATUS,
            data=data
        )
        
    # Batch update methods for improved performance
    async def publish_batch_process_updates(self, process_infos: List[Union[ProcessInfo, EnhancedProcessInfo]]):
        """Publish multiple process status updates in a batch"""
        batch_data = []
        
        for process_info in process_infos:
            # Convert to dict using the same logic as in publish_process_status_update
            if hasattr(process_info, "__dataclass_fields__"):
                data = {
                    "process_name": process_info.name,
                    "status": process_info.status,
                    "pid": process_info.pid,
                    "cpu_percent": process_info.cpu_percent,
                    "memory_mb": process_info.memory_mb,
                    "uptime_seconds": process_info.uptime_seconds if hasattr(process_info, "uptime_seconds") else 0,
                    "health_score": process_info.health_score,
                    "connection_status": process_info.connection_info.status.value if hasattr(process_info, "connection_info") and process_info.connection_info else "unknown",
                    "last_error": process_info.last_error
                }
            else:
                data = {
                    "process_name": process_info.name,
                    "status": process_info.status,
                    "pid": process_info.pid,
                    "cpu_percent": process_info.cpu_percent,
                    "memory_mb": process_info.memory_mb,
                    "uptime_seconds": process_info.uptime,
                    "health_score": process_info.health_score,
                    "connection_status": process_info.connection_status,
                    "last_error": process_info.last_error
                }
            
            # Check for status changes
            process_name = process_info.name
            current_status = data["status"]
            
            if process_name in self.process_status_cache:
                previous_status = self.process_status_cache[process_name].get("status")
                if previous_status != current_status:
                    data["status_changed"] = True
                    data["previous_status"] = previous_status
                    data["status_change_time"] = datetime.now().isoformat()
            
            # Update cache
            if process_name not in self.process_status_cache:
                self.process_status_cache[process_name] = {}
            self.process_status_cache[process_name].update(data)
            
            batch_data.append(data)
        
        # Publish batch update
        return await self.publish_message(
            topic=SubscriptionTopic.PROCESS_STATUS.value,
            message_type=WebSocketMessageType.PROCESS_STATUS_UPDATE,
            data={"batch": True, "processes": batch_data}
        )

# Global WebSocket manager instance
websocket_manager = WebSocketManager()