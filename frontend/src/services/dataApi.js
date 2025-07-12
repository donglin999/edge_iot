import api from './api'

export default {
  // Get real-time data
  async getRealtimeData(query = {}) {
    return await api.get('/api/data/realtime', { params: query })
  },
  
  // Get historical data
  async getHistoricalData(query = {}) {
    return await api.get('/api/data/history', { params: query })
  },
  
  // Get data statistics
  async getStatistics() {
    return await api.get('/api/data/statistics')
  },
  
  // Get device list
  async getDevices() {
    return await api.get('/api/data/devices')
  },
  
  // Get measurements
  async getMeasurements(deviceId = null) {
    const params = deviceId ? { device_id: deviceId } : {}
    return await api.get('/api/data/measurements', { params })
  },
  
  // Export data
  async exportData(query, format = 'csv') {
    return await api.post('/api/data/export', {
      format,
      query
    })
  }
}