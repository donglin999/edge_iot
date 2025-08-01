import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

// Create axios instance
const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// Request interceptor
api.interceptors.request.use(
  (config) => {
    // 添加请求开始时间
    config.metadata = { startTime: new Date() }
    
    // Add authentication token if available
    const token = localStorage.getItem('auth_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor
api.interceptors.response.use(
  (response) => {
    // 计算响应时间
    const endTime = new Date()
    const startTime = response.config.metadata?.startTime
    if (startTime) {
      const duration = endTime - startTime
      if (duration > 1000) { // 超过1秒的请求
        console.warn(`慢请求警告: ${response.config.url} 耗时 ${duration}ms`)
      }
    }
    
    return response.data
  },
  (error) => {
    // 计算错误请求的响应时间
    const endTime = new Date()
    const startTime = error.config?.metadata?.startTime
    if (startTime) {
      const duration = endTime - startTime
      console.error(`请求失败: ${error.config?.url} 耗时 ${duration}ms`, error.message)
    }
    
    // Handle common errors
    if (error.response) {
      // Server responded with error status
      const { status, data } = error.response
      
      switch (status) {
        case 401:
          // Unauthorized - redirect to login
          localStorage.removeItem('auth_token')
          window.location.href = '/login'
          break
        case 403:
          // Forbidden
          console.error('Access denied')
          break
        case 404:
          // Not found
          console.error('Resource not found')
          break
        case 500:
          // Server error
          console.error('Server error:', data.detail)
          break
        default:
          console.error('API error:', data.detail || error.message)
      }
      
      return Promise.reject(new Error(data.detail || error.message))
    } else if (error.request) {
      // Network error
      console.error('Network error:', error.message)
      return Promise.reject(new Error('Network error: Unable to connect to server'))
    } else {
      // Other error
      console.error('Error:', error.message)
      return Promise.reject(error)
    }
  }
)

export default api