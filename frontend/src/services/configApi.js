import api from './api'

export default {
  // Upload configuration file
  async uploadConfig(file, description = null, applyImmediately = false, onUploadProgress = null) {
    const formData = new FormData()
    formData.append('file', file)
    if (description) {
      formData.append('description', description)
    }
    formData.append('apply_immediately', applyImmediately)
    
    return await api.post('/api/config/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      },
      onUploadProgress: (progressEvent) => {
        if (onUploadProgress) {
          const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total)
          onUploadProgress(progress)
        }
      }
    })
  },
  
  // Get current configuration
  async getCurrentConfig() {
    return await api.get('/api/config/current')
  },
  
  // Get configuration history
  async getConfigHistory() {
    return await api.get('/api/config/history')
  },
  
  // Apply configuration
  async applyConfig(configApply) {
    return await api.post('/api/config/apply', configApply)
  },
  
  // Validate configuration
  async validateConfig(configId) {
    return await api.get(`/api/config/validate/${configId}`)
  },
  
  // Rollback configuration
  async rollbackConfig(configId, reason = null) {
    return await api.post('/api/config/rollback', {
      config_id: configId,
      reason
    })
  }
}