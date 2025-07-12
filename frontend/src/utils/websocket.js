import mitt from 'mitt'

class WebSocketManager {
  constructor() {
    this.ws = null
    this.url = import.meta.env.VITE_WS_URL || 'ws://localhost:8000'
    this.reconnectInterval = 3000
    this.maxReconnectAttempts = 5
    this.reconnectAttempts = 0
    this.isConnecting = false
    this.isConnected = false
    this.subscriptions = new Set()
    this.eventBus = mitt()
  }
  
  // Event handling
  on(event, handler) {
    this.eventBus.on(event, handler)
  }
  
  off(event, handler) {
    this.eventBus.off(event, handler)
  }
  
  emit(event, data) {
    this.eventBus.emit(event, data)
  }
  
  // Connect to WebSocket
  async connect() {
    if (this.isConnecting || this.isConnected) {
      return
    }
    
    this.isConnecting = true
    
    try {
      const wsUrl = `${this.url}/ws/connect`
      this.ws = new WebSocket(wsUrl)
      
      this.ws.onopen = () => {
        console.log('WebSocket connected')
        this.isConnected = true
        this.isConnecting = false
        this.reconnectAttempts = 0
        this.emit('connected')
      }
      
      this.ws.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data)
          this.handleMessage(message)
        } catch (error) {
          console.error('Error parsing WebSocket message:', error)
        }
      }
      
      this.ws.onclose = (event) => {
        console.log('WebSocket disconnected:', event.code, event.reason)
        this.isConnected = false
        this.isConnecting = false
        this.emit('disconnected')
        
        // Attempt to reconnect if not intentional
        if (event.code !== 1000 && this.reconnectAttempts < this.maxReconnectAttempts) {
          this.scheduleReconnect()
        }
      }
      
      this.ws.onerror = (error) => {
        console.error('WebSocket error:', error)
        this.isConnecting = false
        this.emit('error', error)
      }
      
    } catch (error) {
      this.isConnecting = false
      this.emit('error', error)
      throw error
    }
  }
  
  // Disconnect from WebSocket
  async disconnect() {
    if (this.ws) {
      this.ws.close(1000, 'Intentional disconnect')
      this.ws = null
    }
    this.isConnected = false
    this.isConnecting = false
  }
  
  // Schedule reconnection
  scheduleReconnect() {
    this.reconnectAttempts++
    console.log(`Scheduling reconnect attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts}`)
    
    setTimeout(() => {
      if (!this.isConnected) {
        this.connect()
      }
    }, this.reconnectInterval)
  }
  
  // Send message
  send(message) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message))
    } else {
      console.warn('WebSocket not connected, unable to send message')
    }
  }
  
  // Subscribe to topics
  async subscribe(topics) {
    if (!Array.isArray(topics)) {
      topics = [topics]
    }
    
    for (const topic of topics) {
      this.subscriptions.add(topic)
    }
    
    this.send({
      type: 'subscribe',
      topics: topics
    })
  }
  
  // Unsubscribe from topics
  async unsubscribe(topics) {
    if (!Array.isArray(topics)) {
      topics = [topics]
    }
    
    for (const topic of topics) {
      this.subscriptions.delete(topic)
    }
    
    this.send({
      type: 'unsubscribe',
      topics: topics
    })
  }
  
  // Handle incoming messages
  handleMessage(message) {
    switch (message.type) {
      case 'subscription_confirmed':
        console.log('Subscription confirmed:', message.topics)
        break
      case 'unsubscription_confirmed':
        console.log('Unsubscription confirmed:', message.topics)
        break
      case 'pong':
        console.log('Pong received')
        break
      default:
        this.emit('message', message)
    }
  }
  
  // Send ping
  ping() {
    this.send({ type: 'ping' })
  }
  
  // Get connection status
  isSocketConnected() {
    return this.isConnected
  }
}

export default new WebSocketManager()