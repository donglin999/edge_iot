import asyncio
import json
import pytest
import unittest.mock as mock
from datetime import datetime
from fastapi import WebSocket, WebSocketDisconnect

from models.websocket_models import WebSocketMessageType, SubscriptionTopic
from models.process_models import ProcessInfo, ProcessType, ProcessStatus, ConnectionStatus, HealthStatus, PerformanceMetrics, ConnectionInfo, EnhancedProcessInfo, ProcessState
from core.websocket_manager import WebSocketManager

class MockWebSocket:
    """Mock WebSocket class for testing"""
    def __init__(self):
        self.sent_messages = []
        self.closed = False
        
    async def accept(self):
        pass
        
    async def send_text(self, text):
        self.sent_messages.append(text)
        
    async def close(self):
        self.closed = True
        
    def get_messages(self):
        return [json.loads(msg) for msg in self.sent_messages]

@pytest.fixture
def websocket_manager():
    """Create a WebSocketManager instance for testing"""
    manager = WebSocketManager()
    yield manager
    # Clean up
    asyncio.run(manager.stop())

@pytest.mark.asyncio
async def test_connect_and_welcome_message():
    """Test connection and welcome message"""
    manager = WebSocketManager()
    websocket = MockWebSocket()
    connection_id = "test_connection"
    
    await manager.connect(websocket, connection_id)
    
    # Check that connection was added
    assert connection_id in manager.active_connections
    assert connection_id in manager.connection_subscriptions
    
    # Check welcome message
    messages = websocket.get_messages()
    assert len(messages) == 1
    assert messages[0]["type"] == "welcome"
    assert "available_topics" in messages[0]["data"]
    assert "connection_id" in messages[0]["data"]
    assert messages[0]["data"]["connection_id"] == connection_id
    
    await manager.stop()

@pytest.mark.asyncio
async def test_subscribe_and_unsubscribe():
    """Test subscription and unsubscription functionality"""
    manager = WebSocketManager()
    websocket = MockWebSocket()
    connection_id = "test_connection"
    
    await manager.connect(websocket, connection_id)
    websocket.sent_messages.clear()  # Clear welcome message
    
    # Subscribe to topics
    topics = [SubscriptionTopic.PROCESS_STATUS.value, SubscriptionTopic.HEALTH_CHECKS.value]
    await manager.subscribe(connection_id, topics)
    
    # Check subscription confirmation
    messages = websocket.get_messages()
    assert len(messages) == 1
    assert messages[0]["type"] == WebSocketMessageType.SUBSCRIPTION_CONFIRMED
    assert set(messages[0]["data"]["topics"]) == set(topics)
    
    # Check that subscriptions were added
    assert connection_id in manager.connection_subscriptions
    assert set(manager.connection_subscriptions[connection_id]) == set(topics)
    
    websocket.sent_messages.clear()
    
    # Unsubscribe from a topic
    unsubscribe_topic = [SubscriptionTopic.HEALTH_CHECKS.value]
    await manager.unsubscribe(connection_id, unsubscribe_topic)
    
    # Check unsubscription confirmation
    messages = websocket.get_messages()
    assert len(messages) == 1
    assert messages[0]["type"] == WebSocketMessageType.UNSUBSCRIPTION_CONFIRMED
    assert unsubscribe_topic == messages[0]["data"]["topics"]
    
    # Check that subscription was removed
    assert connection_id in manager.connection_subscriptions
    assert SubscriptionTopic.PROCESS_STATUS.value in manager.connection_subscriptions[connection_id]
    assert SubscriptionTopic.HEALTH_CHECKS.value not in manager.connection_subscriptions[connection_id]
    
    await manager.stop()

@pytest.mark.asyncio
async def test_process_status_update():
    """Test process status update functionality"""
    manager = WebSocketManager()
    websocket = MockWebSocket()
    connection_id = "test_connection"
    
    await manager.connect(websocket, connection_id)
    await manager.subscribe(connection_id, [SubscriptionTopic.PROCESS_STATUS.value])
    websocket.sent_messages.clear()  # Clear welcome and subscription messages
    
    # Create a process info object
    process_info = ProcessInfo(
        name="test_process",
        type=ProcessType.MODBUS_TCP,
        status=ProcessStatus.RUNNING,
        pid=1234,
        cpu_percent=10.5,
        memory_mb=50.2,
        start_time=datetime.now(),
        connection_status=ConnectionStatus.CONNECTED,
        health_score=95.0
    )
    
    # Publish process status update
    await manager.publish_process_status_update(process_info)
    
    # Check that message was sent
    messages = websocket.get_messages()
    assert len(messages) == 1
    assert messages[0]["type"] == WebSocketMessageType.PROCESS_STATUS_UPDATE
    assert messages[0]["topic"] == SubscriptionTopic.PROCESS_STATUS.value
    assert messages[0]["data"]["process_name"] == "test_process"
    assert messages[0]["data"]["status"] == ProcessStatus.RUNNING
    assert messages[0]["data"]["pid"] == 1234
    assert messages[0]["data"]["cpu_percent"] == 10.5
    assert messages[0]["data"]["memory_mb"] == 50.2
    assert messages[0]["data"]["health_score"] == 95.0
    assert messages[0]["data"]["connection_status"] == ConnectionStatus.CONNECTED
    
    # Test status change detection
    websocket.sent_messages.clear()
    process_info.status = ProcessStatus.ERROR
    process_info.last_error = "Test error"
    
    # Publish updated status
    await manager.publish_process_status_update(process_info)
    
    # Check that status change was detected
    messages = websocket.get_messages()
    assert len(messages) == 2  # One for status update, one for error alert
    
    # Check status update message
    status_message = next(m for m in messages if m["type"] == WebSocketMessageType.PROCESS_STATUS_UPDATE)
    assert status_message["data"]["status"] == ProcessStatus.ERROR
    assert status_message["data"]["status_changed"] == True
    assert status_message["data"]["previous_status"] == ProcessStatus.RUNNING
    assert "status_change_time" in status_message["data"]
    
    # Check error alert message
    error_message = next(m for m in messages if m["type"] == WebSocketMessageType.ERROR_ALERT)
    assert error_message["topic"] == SubscriptionTopic.ERROR_ALERTS.value
    assert error_message["data"]["process_name"] == "test_process"
    assert error_message["data"]["alert_type"] == "status_change"
    assert error_message["data"]["severity"] == "critical"
    assert "running" in error_message["data"]["message"]
    assert "error" in error_message["data"]["message"]
    
    await manager.stop()

@pytest.mark.asyncio
async def test_health_check_result():
    """Test health check result functionality"""
    manager = WebSocketManager()
    websocket = MockWebSocket()
    connection_id = "test_connection"
    
    await manager.connect(websocket, connection_id)
    await manager.subscribe(connection_id, [SubscriptionTopic.HEALTH_CHECKS.value, SubscriptionTopic.ERROR_ALERTS.value])
    websocket.sent_messages.clear()  # Clear welcome and subscription messages
    
    # Publish a warning health check
    await manager.publish_health_check_result(
        process_name="test_process",
        check_type="resource_usage",
        status=HealthStatus.WARNING,
        details={"cpu_percent": 85.0, "memory_mb": 450.0},
        score=75.0,
        recommendations=["Consider restarting the process"]
    )
    
    # Check that message was sent
    messages = websocket.get_messages()
    assert len(messages) == 1
    assert messages[0]["type"] == WebSocketMessageType.HEALTH_CHECK_RESULT
    assert messages[0]["topic"] == SubscriptionTopic.HEALTH_CHECKS.value
    assert messages[0]["data"]["process_name"] == "test_process"
    assert messages[0]["data"]["check_type"] == "resource_usage"
    assert messages[0]["data"]["status"] == HealthStatus.WARNING
    assert messages[0]["data"]["score"] == 75.0
    assert len(messages[0]["data"]["recommendations"]) == 1
    
    # Test critical health check with error alert
    websocket.sent_messages.clear()
    
    # Publish a critical health check
    await manager.publish_health_check_result(
        process_name="test_process",
        check_type="connection_status",
        status=HealthStatus.CRITICAL,
        details={"connection_errors": 5, "last_error": "Connection timeout"},
        score=25.0,
        recommendations=["Check network connectivity", "Restart the process"]
    )
    
    # Check that both health check and error alert messages were sent
    messages = websocket.get_messages()
    assert len(messages) == 2
    
    # Check health check message
    health_message = next(m for m in messages if m["type"] == WebSocketMessageType.HEALTH_CHECK_RESULT)
    assert health_message["topic"] == SubscriptionTopic.HEALTH_CHECKS.value
    assert health_message["data"]["process_name"] == "test_process"
    assert health_message["data"]["status"] == HealthStatus.CRITICAL
    assert health_message["data"]["score"] == 25.0
    
    # Check error alert message
    error_message = next(m for m in messages if m["type"] == WebSocketMessageType.ERROR_ALERT)
    assert error_message["topic"] == SubscriptionTopic.ERROR_ALERTS.value
    assert error_message["data"]["process_name"] == "test_process"
    assert error_message["data"]["alert_type"] == "health_check"
    assert error_message["data"]["severity"] == "critical"
    assert "Critical health check failure" in error_message["data"]["message"]
    
    await manager.stop()

@pytest.mark.asyncio
async def test_connection_status_update():
    """Test connection status update functionality"""
    manager = WebSocketManager()
    websocket = MockWebSocket()
    connection_id = "test_connection"
    
    await manager.connect(websocket, connection_id)
    await manager.subscribe(connection_id, [SubscriptionTopic.PROCESS_STATUS.value])
    websocket.sent_messages.clear()  # Clear welcome and subscription messages
    
    # Create connection info
    connection_info = ConnectionInfo(
        device_ip="192.168.1.100",
        device_port=502,
        is_connected=True,
        last_connect_time=datetime.now(),
        connection_errors=0,
        protocol_type="modbus_tcp",
        status=ConnectionStatus.CONNECTED
    )
    
    # Publish connection status update
    await manager.publish_connection_status_update("test_process", connection_info)
    
    # Check that message was sent
    messages = websocket.get_messages()
    assert len(messages) == 1
    assert messages[0]["type"] == WebSocketMessageType.CONNECTION_STATUS
    assert messages[0]["topic"] == SubscriptionTopic.PROCESS_STATUS.value
    assert messages[0]["data"]["process_name"] == "test_process"
    assert messages[0]["data"]["device_ip"] == "192.168.1.100"
    assert messages[0]["data"]["device_port"] == 502
    assert messages[0]["data"]["is_connected"] == True
    assert messages[0]["data"]["status"] == ConnectionStatus.CONNECTED
    
    # Test connection status change
    websocket.sent_messages.clear()
    
    # Update connection status to error
    connection_info.status = ConnectionStatus.ERROR
    connection_info.is_connected = False
    connection_info.connection_errors = 3
    
    # Publish updated connection status
    await manager.publish_connection_status_update("test_process", connection_info)
    
    # Check that both connection status update and error alert were sent
    messages = websocket.get_messages()
    assert len(messages) == 2
    
    # Check connection status message
    conn_message = next(m for m in messages if m["type"] == WebSocketMessageType.CONNECTION_STATUS)
    assert conn_message["data"]["status"] == ConnectionStatus.ERROR
    assert conn_message["data"]["is_connected"] == False
    assert conn_message["data"]["connection_errors"] == 3
    assert conn_message["data"]["status_changed"] == True
    assert conn_message["data"]["previous_status"] == ConnectionStatus.CONNECTED
    
    # Check error alert message
    error_message = next(m for m in messages if m["type"] == WebSocketMessageType.ERROR_ALERT)
    assert error_message["topic"] == SubscriptionTopic.ERROR_ALERTS.value
    assert error_message["data"]["process_name"] == "test_process"
    assert error_message["data"]["alert_type"] == "connection_change"
    assert error_message["data"]["severity"] == "critical"
    assert "connected" in error_message["data"]["message"]
    assert "error" in error_message["data"]["message"]
    
    await manager.stop()

@pytest.mark.asyncio
async def test_batch_process_updates():
    """Test batch process updates functionality"""
    manager = WebSocketManager()
    websocket = MockWebSocket()
    connection_id = "test_connection"
    
    await manager.connect(websocket, connection_id)
    await manager.subscribe(connection_id, [SubscriptionTopic.PROCESS_STATUS.value])
    websocket.sent_messages.clear()  # Clear welcome and subscription messages
    
    # Create multiple process info objects
    process_infos = [
        ProcessInfo(
            name="process1",
            type=ProcessType.MODBUS_TCP,
            status=ProcessStatus.RUNNING,
            pid=1001,
            cpu_percent=10.0,
            memory_mb=50.0,
            health_score=95.0
        ),
        ProcessInfo(
            name="process2",
            type=ProcessType.OPC_UA,
            status=ProcessStatus.RUNNING,
            pid=1002,
            cpu_percent=15.0,
            memory_mb=60.0,
            health_score=90.0
        ),
        ProcessInfo(
            name="process3",
            type=ProcessType.MELSOFT_A1E,
            status=ProcessStatus.STOPPED,
            pid=None,
            cpu_percent=0.0,
            memory_mb=0.0,
            health_score=0.0
        )
    ]
    
    # Publish batch update
    await manager.publish_batch_process_updates(process_infos)
    
    # Check that batch message was sent
    messages = websocket.get_messages()
    assert len(messages) == 1
    assert messages[0]["type"] == WebSocketMessageType.PROCESS_STATUS_UPDATE
    assert messages[0]["topic"] == SubscriptionTopic.PROCESS_STATUS.value
    assert messages[0]["data"]["batch"] == True
    assert len(messages[0]["data"]["processes"]) == 3
    
    # Check individual process data in batch
    processes = {p["process_name"]: p for p in messages[0]["data"]["processes"]}
    assert "process1" in processes
    assert processes["process1"]["status"] == ProcessStatus.RUNNING
    assert processes["process1"]["pid"] == 1001
    
    assert "process2" in processes
    assert processes["process2"]["status"] == ProcessStatus.RUNNING
    assert processes["process2"]["pid"] == 1002
    
    assert "process3" in processes
    assert processes["process3"]["status"] == ProcessStatus.STOPPED
    assert processes["process3"]["pid"] is None
    
    await manager.stop()

@pytest.mark.asyncio
async def test_client_message_handling():
    """Test handling of client messages"""
    manager = WebSocketManager()
    websocket = MockWebSocket()
    connection_id = "test_connection"
    
    await manager.connect(websocket, connection_id)
    websocket.sent_messages.clear()  # Clear welcome message
    
    # Test subscribe message
    subscribe_message = json.dumps({
        "type": "subscribe",
        "topics": [SubscriptionTopic.PROCESS_STATUS.value, SubscriptionTopic.HEALTH_CHECKS.value]
    })
    
    await manager.handle_client_message(connection_id, subscribe_message)
    
    # Check subscription confirmation
    messages = websocket.get_messages()
    assert len(messages) == 1
    assert messages[0]["type"] == WebSocketMessageType.SUBSCRIPTION_CONFIRMED
    assert set(messages[0]["data"]["topics"]) == {SubscriptionTopic.PROCESS_STATUS.value, SubscriptionTopic.HEALTH_CHECKS.value}
    
    # Check that subscriptions were added
    assert connection_id in manager.connection_subscriptions
    assert SubscriptionTopic.PROCESS_STATUS.value in manager.connection_subscriptions[connection_id]
    assert SubscriptionTopic.HEALTH_CHECKS.value in manager.connection_subscriptions[connection_id]
    
    websocket.sent_messages.clear()
    
    # Test ping message
    ping_message = json.dumps({
        "type": "ping"
    })
    
    await manager.handle_client_message(connection_id, ping_message)
    
    # Check pong response
    messages = websocket.get_messages()
    assert len(messages) == 1
    assert messages[0]["type"] == WebSocketMessageType.PONG
    assert "server_time" in messages[0]["data"]
    
    websocket.sent_messages.clear()
    
    # Test unsubscribe message
    unsubscribe_message = json.dumps({
        "type": "unsubscribe",
        "topics": [SubscriptionTopic.HEALTH_CHECKS.value]
    })
    
    await manager.handle_client_message(connection_id, unsubscribe_message)
    
    # Check unsubscription confirmation
    messages = websocket.get_messages()
    assert len(messages) == 1
    assert messages[0]["type"] == WebSocketMessageType.UNSUBSCRIPTION_CONFIRMED
    assert messages[0]["data"]["topics"] == [SubscriptionTopic.HEALTH_CHECKS.value]
    
    # Check that subscription was removed
    assert connection_id in manager.connection_subscriptions
    assert SubscriptionTopic.PROCESS_STATUS.value in manager.connection_subscriptions[connection_id]
    assert SubscriptionTopic.HEALTH_CHECKS.value not in manager.connection_subscriptions[connection_id]
    
    await manager.stop()

@pytest.mark.asyncio
async def test_message_history():
    """Test message history functionality"""
    manager = WebSocketManager()
    websocket1 = MockWebSocket()
    connection_id1 = "connection1"
    
    # Connect first client and subscribe
    await manager.connect(websocket1, connection_id1)
    await manager.subscribe(connection_id1, [SubscriptionTopic.PROCESS_STATUS.value])
    websocket1.sent_messages.clear()  # Clear welcome and subscription messages
    
    # Publish some process status updates
    for i in range(3):
        process_info = ProcessInfo(
            name=f"process{i}",
            type=ProcessType.MODBUS_TCP,
            status=ProcessStatus.RUNNING,
            pid=1000 + i,
            cpu_percent=10.0 + i,
            memory_mb=50.0 + i,
            health_score=95.0 - i
        )
        await manager.publish_process_status_update(process_info)
    
    # Check that messages were sent to first client
    messages1 = websocket1.get_messages()
    assert len(messages1) == 3
    
    # Connect second client
    websocket2 = MockWebSocket()
    connection_id2 = "connection2"
    await manager.connect(websocket2, connection_id2)
    
    # Get welcome message and clear
    welcome_message = websocket2.get_messages()[0]
    assert welcome_message["type"] == "welcome"
    websocket2.sent_messages.clear()
    
    # Subscribe second client to same topic
    await manager.subscribe(connection_id2, [SubscriptionTopic.PROCESS_STATUS.value])
    
    # Check that history messages were sent to second client
    messages2 = websocket2.get_messages()
    
    # First message should be subscription confirmation
    assert messages2[0]["type"] == WebSocketMessageType.SUBSCRIPTION_CONFIRMED
    
    # Rest should be history messages
    history_messages = [m for m in messages2 if m["type"] == WebSocketMessageType.PROCESS_STATUS_UPDATE]
    assert len(history_messages) == 3
    
    # Check that history messages are marked as history
    for msg in history_messages:
        assert msg["data"]["is_history"] == True
    
    await manager.stop()

@pytest.mark.asyncio
async def test_topic_handlers():
    """Test topic handler registration and execution"""
    manager = WebSocketManager()
    
    # Create a mock handler
    handler_called = False
    handler_message = None
    
    async def test_handler(message):
        nonlocal handler_called, handler_message
        handler_called = True
        handler_message = message
    
    # Register handler for process status topic
    manager.register_topic_handler(SubscriptionTopic.PROCESS_STATUS.value, test_handler)
    
    # Publish a message to the topic
    process_info = ProcessInfo(
        name="test_process",
        type=ProcessType.MODBUS_TCP,
        status=ProcessStatus.RUNNING,
        pid=1234,
        cpu_percent=10.5,
        memory_mb=50.2,
        health_score=95.0
    )
    
    await manager.publish_process_status_update(process_info)
    
    # Wait for handler to be called
    await asyncio.sleep(0.1)
    
    # Check that handler was called with correct message
    assert handler_called
    assert handler_message is not None
    assert handler_message["type"] == WebSocketMessageType.PROCESS_STATUS_UPDATE
    assert handler_message["topic"] == SubscriptionTopic.PROCESS_STATUS.value
    assert handler_message["data"]["process_name"] == "test_process"
    
    # Unregister handler
    manager.unregister_topic_handler(SubscriptionTopic.PROCESS_STATUS.value, test_handler)
    
    # Reset flags
    handler_called = False
    handler_message = None
    
    # Publish another message
    process_info.status = ProcessStatus.STOPPED
    await manager.publish_process_status_update(process_info)
    
    # Wait for handler to be called (should not be called)
    await asyncio.sleep(0.1)
    
    # Check that handler was not called
    assert not handler_called
    assert handler_message is None
    
    await manager.stop()