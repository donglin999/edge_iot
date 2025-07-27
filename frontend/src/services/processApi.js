import api from './api'

export default {
  // Get all processes
  async getProcesses() {
    return await api.get('/api/processes/')
  },
  
  // Start processes
  async startProcesses(processNames = []) {
    return await api.post('/api/processes/start', {
      action: 'start',
      process_names: processNames
    })
  },
  
  // Stop processes
  async stopProcesses(processNames = []) {
    return await api.post('/api/processes/stop', {
      action: 'stop',
      process_names: processNames
    })
  },
  
  // Restart processes
  async restartProcesses(processNames = []) {
    return await api.post('/api/processes/restart', {
      action: 'restart',
      process_names: processNames
    })
  },
  
  // Get specific process status
  async getProcessStatus(processName) {
    return await api.get(`/api/processes/${processName}/status`)
  },
  
  // Get process logs
  async getProcessLogs(processName, lines = 100, page = 1) {
    return await api.get(`/api/processes/${processName}/logs`, {
      params: { lines, page }
    })
  }
}