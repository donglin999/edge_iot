<template>
  <div class="system-monitor-content">
    <!-- System Overview -->
    <el-row :gutter="20" class="stats-row">
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon cpu">
              <el-icon><Cpu /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ systemStats.cpu }}%</div>
              <div class="stat-label">CPU使用率</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon memory">
              <el-icon><Monitor /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ systemStats.memory }}%</div>
              <div class="stat-label">内存使用率</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon disk">
              <el-icon><FolderOpened /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ systemStats.disk }}%</div>
              <div class="stat-label">磁盘使用率</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon network">
              <el-icon><Connection /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ systemStats.network }}</div>
              <div class="stat-label">网络状态</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- System Actions -->
    <el-row class="action-panel">
      <el-col :span="24">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>系统操作</span>
              <div class="action-buttons">
                <el-button type="success" @click="refreshSystem">
                  <el-icon><Refresh /></el-icon>
                  刷新状态
                </el-button>
                <el-button type="warning" @click="restartSystem">
                  <el-icon><RefreshRight /></el-icon>
                  重启系统
                </el-button>
                <el-button type="info" @click="exportLogs">
                  <el-icon><Download /></el-icon>
                  导出日志
                </el-button>
              </div>
            </div>
          </template>
        </el-card>
      </el-col>
    </el-row>

    <!-- System Details -->
    <el-row :gutter="20">
      <el-col :span="12">
        <el-card class="detail-card">
          <template #header>
            <span>系统信息</span>
          </template>
          <div class="system-info">
            <div class="info-item">
              <span class="label">操作系统:</span>
              <span class="value">{{ systemInfo.os }}</span>
            </div>
            <div class="info-item">
              <span class="label">系统版本:</span>
              <span class="value">{{ systemInfo.version }}</span>
            </div>
            <div class="info-item">
              <span class="label">启动时间:</span>
              <span class="value">{{ systemInfo.uptime }}</span>
            </div>
            <div class="info-item">
              <span class="label">CPU型号:</span>
              <span class="value">{{ systemInfo.cpuModel }}</span>
            </div>
            <div class="info-item">
              <span class="label">总内存:</span>
              <span class="value">{{ systemInfo.totalMemory }}</span>
            </div>
            <div class="info-item">
              <span class="label">可用内存:</span>
              <span class="value">{{ systemInfo.availableMemory }}</span>
            </div>
          </div>
        </el-card>
      </el-col>

      <el-col :span="12">
        <el-card class="detail-card">
          <template #header>
            <span>服务状态</span>
          </template>
          <div class="service-list">
            <div v-for="service in services" :key="service.name" class="service-item">
              <div class="service-info">
                <span class="service-name">{{ service.name }}</span>
                <el-tag :type="service.status === 'running' ? 'success' : 'danger'" size="small">
                  {{ service.status === 'running' ? '运行中' : '已停止' }}
                </el-tag>
              </div>
              <div class="service-actions">
                <el-button size="small" @click="startService(service)">启动</el-button>
                <el-button size="small" @click="stopService(service)">停止</el-button>
              </div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- Performance Charts -->
    <el-row :gutter="20" class="charts-row">
      <el-col :span="12">
        <el-card class="chart-card">
          <template #header>
            <span>CPU使用率趋势</span>
          </template>
          <div class="chart-container">
            <p style="text-align: center; margin-top: 100px;">CPU使用率图表区域</p>
          </div>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card class="chart-card">
          <template #header>
            <span>内存使用率趋势</span>
          </template>
          <div class="chart-container">
            <p style="text-align: center; margin-top: 100px;">内存使用率图表区域</p>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- System Logs -->
    <el-row>
      <el-col :span="24">
        <el-card class="logs-card">
          <template #header>
            <div class="card-header">
              <span>系统日志</span>
              <div class="log-controls">
                <el-select v-model="logLevel" size="small" style="width: 120px;">
                  <el-option label="全部" value="all" />
                  <el-option label="ERROR" value="error" />
                  <el-option label="WARNING" value="warning" />
                  <el-option label="INFO" value="info" />
                </el-select>
                <el-button type="primary" size="small" @click="refreshLogs">刷新</el-button>
              </div>
            </div>
          </template>
          <div class="logs-container">
            <div v-for="log in filteredLogs" :key="log.id" class="log-item" :class="log.level">
              <span class="log-time">{{ log.timestamp }}</span>
              <span class="log-level">{{ log.level }}</span>
              <span class="log-message">{{ log.message }}</span>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
import systemApi from '../../services/systemApi'

export default {
  name: 'SystemMonitorContent',
  setup() {
    const systemStats = ref({
      cpu: 0,
      memory: 0,
      disk: 0,
      network: '正常'
    })

    const systemInfo = ref({
      os: '',
      version: '',
      uptime: '',
      cpuModel: '',
      totalMemory: '',
      availableMemory: ''
    })

    const services = ref([])
    const logLevel = ref('all')
    const logs = ref([])
    let refreshTimer = null

    const filteredLogs = computed(() => {
      if (logLevel.value === 'all') {
        return logs.value
      }
      return logs.value.filter(log => log.level.toLowerCase() === logLevel.value.toLowerCase())
    })

    // API 调用函数
    const loadSystemMetrics = async () => {
      try {
        const response = await systemApi.getSystemMetrics()
        systemStats.value = {
          cpu: response.cpu_percent || 0,
          memory: response.memory_percent || 0,
          disk: response.disk_usage || 0,
          network: '正常'
        }
      } catch (error) {
        console.error('Failed to load system metrics:', error)
      }
    }

    const loadSystemInfo = async () => {
      try {
        const response = await systemApi.getSystemInfo()
        systemInfo.value = {
          os: response.os || '',
          version: response.version || '',
          uptime: response.uptime || '',
          cpuModel: `${response.arch} ${response.cpu_cores}核心`,
          totalMemory: response.total_memory || '',
          availableMemory: response.total_memory || ''
        }
      } catch (error) {
        console.error('Failed to load system info:', error)
      }
    }

    const loadServices = async () => {
      try {
        const response = await systemApi.getServiceStatus()
        services.value = response.services || []
      } catch (error) {
        console.error('Failed to load services:', error)
      }
    }

    const loadSystemLogs = async () => {
      try {
        const response = await systemApi.getSystemLogs(logLevel.value, 50)
        logs.value = response.logs || []
      } catch (error) {
        console.error('Failed to load system logs:', error)
      }
    }

    const loadAllData = async () => {
      await Promise.all([
        loadSystemMetrics(),
        loadSystemInfo(),
        loadServices(),
        loadSystemLogs()
      ])
    }

    const refreshSystem = async () => {
      try {
        await loadAllData()
        ElMessage.success('系统状态已刷新')
      } catch (error) {
        ElMessage.error('刷新失败')
      }
    }

    const restartSystem = () => {
      ElMessage.warning('重启系统功能暂未实现')
    }

    const exportLogs = () => {
      try {
        const logData = filteredLogs.value.map(log => 
          `${log.timestamp} [${log.level}] ${log.message}`
        ).join('\n')
        
        const blob = new Blob([logData], { type: 'text/plain' })
        const url = window.URL.createObjectURL(blob)
        const link = document.createElement('a')
        link.href = url
        link.download = `system_logs_${new Date().toISOString().slice(0, 10)}.txt`
        link.click()
        window.URL.revokeObjectURL(url)
        
        ElMessage.success('日志导出成功')
      } catch (error) {
        ElMessage.error('导出日志失败')
      }
    }

    const startService = async (service) => {
      try {
        await systemApi.controlService(service.name, 'start')
        service.status = 'running'
        ElMessage.success(`服务 ${service.name} 启动成功`)
      } catch (error) {
        ElMessage.error(`启动服务 ${service.name} 失败`)
      }
    }

    const stopService = async (service) => {
      try {
        await systemApi.controlService(service.name, 'stop')
        service.status = 'stopped'
        ElMessage.success(`服务 ${service.name} 停止成功`)
      } catch (error) {
        ElMessage.error(`停止服务 ${service.name} 失败`)
      }
    }

    const refreshLogs = async () => {
      try {
        await loadSystemLogs()
        ElMessage.success('日志已刷新')
      } catch (error) {
        ElMessage.error('刷新日志失败')
      }
    }

    onMounted(() => {
      loadAllData()
      // 设置定时刷新
      refreshTimer = setInterval(() => {
        loadSystemMetrics()
      }, 30000) // 每30秒刷新系统指标
    })

    onUnmounted(() => {
      if (refreshTimer) {
        clearInterval(refreshTimer)
      }
    })

    return {
      systemStats,
      systemInfo,
      services,
      logLevel,
      logs,
      filteredLogs,
      refreshSystem,
      restartSystem,
      exportLogs,
      startService,
      stopService,
      refreshLogs
    }
  }
}
</script>

<style scoped>
.system-monitor-content {
  width: 100%;
}

.stats-row {
  margin-bottom: 20px;
}

.stat-card {
  height: 100px;
}

.stat-content {
  display: flex;
  align-items: center;
  height: 100%;
}

.stat-icon {
  width: 50px;
  height: 50px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 15px;
  font-size: 24px;
  color: #fff;
}

.stat-icon.cpu { background-color: #409eff; }
.stat-icon.memory { background-color: #67c23a; }
.stat-icon.disk { background-color: #e6a23c; }
.stat-icon.network { background-color: #f56c6c; }

.stat-info {
  flex: 1;
}

.stat-value {
  font-size: 24px;
  font-weight: bold;
  color: #333;
}

.stat-label {
  font-size: 14px;
  color: #666;
  margin-top: 5px;
}

.action-panel {
  margin-bottom: 20px;
}

.action-buttons {
  display: flex;
  gap: 10px;
}

.detail-card {
  height: 300px;
  margin-bottom: 20px;
}

.system-info {
  padding: 10px 0;
}

.info-item {
  display: flex;
  justify-content: space-between;
  padding: 8px 0;
  border-bottom: 1px solid #f0f0f0;
}

.info-item:last-child {
  border-bottom: none;
}

.label {
  font-weight: 500;
  color: #666;
}

.value {
  color: #333;
}

.service-list {
  padding: 10px 0;
}

.service-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 0;
  border-bottom: 1px solid #f0f0f0;
}

.service-item:last-child {
  border-bottom: none;
}

.service-info {
  display: flex;
  align-items: center;
  gap: 10px;
}

.service-name {
  font-weight: 500;
}

.service-actions {
  display: flex;
  gap: 5px;
}

.charts-row {
  margin-bottom: 20px;
}

.chart-card {
  height: 300px;
}

.chart-container {
  height: 220px;
}

.logs-card {
  min-height: 400px;
}

.log-controls {
  display: flex;
  gap: 10px;
  align-items: center;
}

.logs-container {
  max-height: 300px;
  overflow-y: auto;
  font-family: monospace;
  font-size: 12px;
}

.log-item {
  display: flex;
  gap: 15px;
  padding: 5px 0;
  border-bottom: 1px solid #f5f5f5;
}

.log-time {
  color: #666;
  width: 150px;
  flex-shrink: 0;
}

.log-level {
  width: 60px;
  flex-shrink: 0;
  font-weight: bold;
}

.log-level.INFO { color: #409eff; }
.log-level.WARNING { color: #e6a23c; }
.log-level.ERROR { color: #f56c6c; }

.log-message {
  flex: 1;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>