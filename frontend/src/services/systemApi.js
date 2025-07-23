import api from './api'

export default {
  // Get system status
  async getSystemStatus() {
    return await api.get('/api/system/status')
  },
  
  // Get system metrics (CPU, memory, disk, network)
  async getSystemMetrics() {
    return await api.get('/api/system/metrics')
  },
  
  // Get system logs
  async getSystemLogs(level = 'all', limit = 100) {
    return await api.get('/api/system/logs', {
      params: { level, limit }
    })
  },
  
  // Health check
  async healthCheck() {
    return await api.get('/api/system/health')
  },
  
  // Get system information
  async getSystemInfo() {
    return await api.get('/api/system/info')
  },
  
  // Get service status
  async getServiceStatus() {
    return await api.get('/api/system/services')
  },
  
  // Get database connections status
  async getDatabaseStatus() {
    return await api.get('/api/system/databases')
  },
  
  // Test database connections
  async testDatabaseConnections() {
    return await api.post('/api/system/databases/test')
  },
  
  // Control service (start/stop)
  async controlService(serviceName, action) {
    return await api.post(`/api/system/services/${serviceName}/${action}`)
  }
}