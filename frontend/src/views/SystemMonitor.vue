<template>
  <div class="system-monitor">
    <el-container>
      <!-- Header -->
      <el-header height="60px" class="header">
        <div class="header-left">
          <h1 class="title">系统监控</h1>
        </div>
        <div class="header-right">
          <el-button type="primary" @click="refreshSystemInfo">
            <el-icon><Refresh /></el-icon>
            刷新系统
          </el-button>
        </div>
      </el-header>

      <el-main class="main-content">
        <!-- System Overview -->
        <el-row :gutter="20" class="overview-row">
          <el-col :span="6">
            <el-card class="overview-card">
              <div class="overview-content">
                <div class="overview-icon cpu">
                  <el-icon><Cpu /></el-icon>
                </div>
                <div class="overview-info">
                  <div class="overview-title">CPU使用率</div>
                  <div class="overview-value">{{ systemMetrics.cpu }}%</div>
                  <el-progress 
                    :percentage="systemMetrics.cpu" 
                    :color="getProgressColor(systemMetrics.cpu)"
                    :show-text="false" 
                  />
                </div>
              </div>
            </el-card>
          </el-col>
          
          <el-col :span="6">
            <el-card class="overview-card">
              <div class="overview-content">
                <div class="overview-icon memory">
                  <el-icon><MemoryCard /></el-icon>
                </div>
                <div class="overview-info">
                  <div class="overview-title">内存使用率</div>
                  <div class="overview-value">{{ systemMetrics.memory }}%</div>
                  <el-progress 
                    :percentage="systemMetrics.memory" 
                    :color="getProgressColor(systemMetrics.memory)"
                    :show-text="false" 
                  />
                </div>
              </div>
            </el-card>
          </el-col>
          
          <el-col :span="6">
            <el-card class="overview-card">
              <div class="overview-content">
                <div class="overview-icon disk">
                  <el-icon><FolderOpened /></el-icon>
                </div>
                <div class="overview-info">
                  <div class="overview-title">磁盘使用率</div>
                  <div class="overview-value">{{ systemMetrics.disk }}%</div>
                  <el-progress 
                    :percentage="systemMetrics.disk" 
                    :color="getProgressColor(systemMetrics.disk)"
                    :show-text="false" 
                  />
                </div>
              </div>
            </el-card>
          </el-col>
          
          <el-col :span="6">
            <el-card class="overview-card">
              <div class="overview-content">
                <div class="overview-icon network">
                  <el-icon><Connection /></el-icon>
                </div>
                <div class="overview-info">
                  <div class="overview-title">网络状态</div>
                  <div class="overview-value">正常</div>
                  <div class="network-speed">
                    ↓{{ systemMetrics.networkDown }}MB/s ↑{{ systemMetrics.networkUp }}MB/s
                  </div>
                </div>
              </div>
            </el-card>
          </el-col>
        </el-row>

        <!-- Service Status -->
        <el-row :gutter="20" class="service-row">
          <el-col :span="12">
            <el-card class="service-card">
              <template #header>
                <div class="card-header">
                  <span>服务状态</span>
                  <el-button type="primary" size="small" @click="refreshServices">
                    <el-icon><Refresh /></el-icon>
                    刷新
                  </el-button>
                </div>
              </template>
              <el-table :data="services" stripe>
                <el-table-column prop="name" label="服务名称" width="150" />
                <el-table-column prop="status" label="状态" width="100">
                  <template #default="scope">
                    <el-tag :type="getServiceStatusType(scope.row.status)">
                      {{ scope.row.status }}
                    </el-tag>
                  </template>
                </el-table-column>
                <el-table-column prop="uptime" label="运行时间" width="120" />
                <el-table-column prop="description" label="描述" />
                <el-table-column label="操作" width="100">
                  <template #default="scope">
                    <el-button 
                      size="small" 
                      :type="scope.row.status === 'running' ? 'danger' : 'success'"
                      @click="toggleService(scope.row)"
                    >
                      {{ scope.row.status === 'running' ? '停止' : '启动' }}
                    </el-button>
                  </template>
                </el-table-column>
              </el-table>
            </el-card>
          </el-col>
          
          <el-col :span="12">
            <el-card class="service-card">
              <template #header>
                <div class="card-header">
                  <span>数据库连接</span>
                  <el-button type="primary" size="small" @click="testConnections">
                    <el-icon><Connection /></el-icon>
                    测试连接
                  </el-button>
                </div>
              </template>
              <el-table :data="databases" stripe>
                <el-table-column prop="name" label="数据库" width="120" />
                <el-table-column prop="status" label="状态" width="100">
                  <template #default="scope">
                    <el-tag :type="getDbStatusType(scope.row.status)">
                      {{ scope.row.status }}
                    </el-tag>
                  </template>
                </el-table-column>
                <el-table-column prop="url" label="连接地址" />
                <el-table-column prop="responseTime" label="响应时间" width="100" />
              </el-table>
            </el-card>
          </el-col>
        </el-row>

        <!-- System Info -->
        <el-row :gutter="20" class="info-row">
          <el-col :span="12">
            <el-card class="info-card">
              <template #header>
                <span>系统信息</span>
              </template>
              <el-descriptions :column="1" border>
                <el-descriptions-item label="操作系统">
                  {{ systemInfo.os }}
                </el-descriptions-item>
                <el-descriptions-item label="系统版本">
                  {{ systemInfo.version }}
                </el-descriptions-item>
                <el-descriptions-item label="CPU架构">
                  {{ systemInfo.arch }}
                </el-descriptions-item>
                <el-descriptions-item label="CPU核心数">
                  {{ systemInfo.cpuCores }}
                </el-descriptions-item>
                <el-descriptions-item label="总内存">
                  {{ systemInfo.totalMemory }}
                </el-descriptions-item>
                <el-descriptions-item label="系统启动时间">
                  {{ formatTime(systemInfo.bootTime) }}
                </el-descriptions-item>
                <el-descriptions-item label="运行时间">
                  {{ systemInfo.uptime }}
                </el-descriptions-item>
              </el-descriptions>
            </el-card>
          </el-col>
          
          <el-col :span="12">
            <el-card class="info-card">
              <template #header>
                <div class="card-header">
                  <span>系统日志</span>
                  <div class="log-controls">
                    <el-select v-model="logLevel" size="small" style="width: 100px;">
                      <el-option label="全部" value="all" />
                      <el-option label="错误" value="error" />
                      <el-option label="警告" value="warn" />
                      <el-option label="信息" value="info" />
                    </el-select>
                    <el-button type="primary" size="small" @click="refreshLogs">
                      <el-icon><Refresh /></el-icon>
                      刷新
                    </el-button>
                  </div>
                </div>
              </template>
              <div class="log-container">
                <el-scrollbar height="300px">
                  <div v-for="log in filteredLogs" :key="log.id" class="log-item">
                    <span class="log-time">{{ formatLogTime(log.time) }}</span>
                    <el-tag :type="getLogType(log.level)" size="small">{{ log.level }}</el-tag>
                    <span class="log-message">{{ log.message }}</span>
                  </div>
                </el-scrollbar>
              </div>
            </el-card>
          </el-col>
        </el-row>

        <!-- Performance Charts -->
        <el-row>
          <el-col :span="24">
            <el-card class="chart-card">
              <template #header>
                <div class="card-header">
                  <span>性能监控</span>
                  <div class="chart-controls">
                    <el-button-group>
                      <el-button 
                        :type="chartTimeRange === '1h' ? 'primary' : ''" 
                        size="small"
                        @click="chartTimeRange = '1h'"
                      >1小时</el-button>
                      <el-button 
                        :type="chartTimeRange === '6h' ? 'primary' : ''" 
                        size="small"
                        @click="chartTimeRange = '6h'"
                      >6小时</el-button>
                      <el-button 
                        :type="chartTimeRange === '24h' ? 'primary' : ''" 
                        size="small"
                        @click="chartTimeRange = '24h'"
                      >24小时</el-button>
                    </el-button-group>
                  </div>
                </div>
              </template>
              <div class="performance-charts">
                <div class="chart-item">
                  <h4>CPU使用率趋势</h4>
                  <div class="mock-chart">CPU趋势图 ({{ chartTimeRange }})</div>
                </div>
                <div class="chart-item">
                  <h4>内存使用率趋势</h4>
                  <div class="mock-chart">内存趋势图 ({{ chartTimeRange }})</div>
                </div>
                <div class="chart-item">
                  <h4>网络流量趋势</h4>
                  <div class="mock-chart">网络趋势图 ({{ chartTimeRange }})</div>
                </div>
              </div>
            </el-card>
          </el-col>
        </el-row>
      </el-main>
    </el-container>
  </div>
</template>

<script>
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import systemApi from '../services/systemApi'

export default {
  name: 'SystemMonitor',
  setup() {
    const logLevel = ref('all')
    const chartTimeRange = ref('1h')

    // Data from API
    const systemMetrics = ref({
      cpu: 0,
      memory: 0,
      disk: 0,
      networkDown: 0,
      networkUp: 0
    })

    const systemInfo = ref({
      os: '',
      version: '',
      arch: '',
      cpuCores: 0,
      totalMemory: '',
      bootTime: '',
      uptime: ''
    })

    const services = ref([])
    const databases = ref([])
    const systemLogs = ref([])

    const filteredLogs = computed(() => {
      if (logLevel.value === 'all') return systemLogs.value
      return systemLogs.value.filter(log => log.level.toLowerCase() === logLevel.value.toLowerCase())
    })

    const getProgressColor = (percentage) => {
      if (percentage < 60) return '#67c23a'
      if (percentage < 80) return '#e6a23c'
      return '#f56c6c'
    }

    const getServiceStatusType = (status) => {
      return status === 'running' ? 'success' : 'danger'
    }

    const getDbStatusType = (status) => {
      return status === '已连接' ? 'success' : 'danger'
    }

    const getLogType = (level) => {
      switch (level.toLowerCase()) {
        case 'error': return 'danger'
        case 'warn': return 'warning'
        case 'info': return 'info'
        default: return 'info'
      }
    }

    const formatTime = (timeStr) => {
      if (!timeStr) return '-'
      return new Date(timeStr).toLocaleString('zh-CN')
    }

    const formatLogTime = (timeStr) => {
      if (!timeStr) return '-'
      return new Date(timeStr).toLocaleTimeString('zh-CN')
    }

    // API functions
    const loadSystemMetrics = async () => {
      try {
        const response = await systemApi.getSystemMetrics()
        systemMetrics.value = {
          cpu: response.cpu_percent || 0,
          memory: response.memory_percent || 0,
          disk: response.disk_usage || 0,
          networkDown: response.network_io?.bytes_recv_mb || 0,
          networkUp: response.network_io?.bytes_sent_mb || 0
        }
      } catch (error) {
        console.error('Failed to load system metrics:', error)
        ElMessage.error('加载系统指标失败')
      }
    }

    const loadSystemInfo = async () => {
      try {
        const response = await systemApi.getSystemInfo()
        systemInfo.value = {
          os: response.os || '',
          version: response.version || '',
          arch: response.arch || '',
          cpuCores: response.cpu_cores || 0,
          totalMemory: response.total_memory || '',
          bootTime: response.boot_time || '',
          uptime: response.uptime || ''
        }
      } catch (error) {
        console.error('Failed to load system info:', error)
        ElMessage.error('加载系统信息失败')
      }
    }

    const loadServices = async () => {
      try {
        const response = await systemApi.getServiceStatus()
        services.value = response.services || []
      } catch (error) {
        console.error('Failed to load services:', error)
        ElMessage.error('加载服务状态失败')
      }
    }

    const loadDatabases = async () => {
      try {
        const response = await systemApi.getDatabaseStatus()
        databases.value = response.databases || []
      } catch (error) {
        console.error('Failed to load databases:', error)
        ElMessage.error('加载数据库状态失败')
      }
    }

    const loadSystemLogs = async () => {
      try {
        const response = await systemApi.getSystemLogs(logLevel.value, 100)
        systemLogs.value = response.logs || []
      } catch (error) {
        console.error('Failed to load system logs:', error)
        ElMessage.error('加载系统日志失败')
      }
    }

    const refreshSystemInfo = async () => {
      try {
        await Promise.all([
          loadSystemMetrics(),
          loadSystemInfo()
        ])
        ElMessage.success('系统信息已刷新')
      } catch (error) {
        ElMessage.error('刷新失败')
      }
    }

    const refreshServices = async () => {
      await loadServices()
      ElMessage.success('服务状态已刷新')
    }

    const testConnections = async () => {
      try {
        await systemApi.testDatabaseConnections()
        await loadDatabases()
        ElMessage.success('数据库连接测试完成')
      } catch (error) {
        ElMessage.error('连接测试失败')
      }
    }

    const refreshLogs = async () => {
      await loadSystemLogs()
      ElMessage.success('日志已刷新')
    }

    const toggleService = async (service) => {
      try {
        const action = service.status === 'running' ? 'stop' : 'start'
        await systemApi.controlService(service.name, action)
        service.status = service.status === 'running' ? 'stopped' : 'running'
        ElMessage.success(`服务 ${service.name} ${action === 'start' ? '启动' : '停止'}成功`)
      } catch (error) {
        console.error('Failed to control service:', error)
        ElMessage.error(`服务操作失败`)
      }
    }

    const loadAllData = async () => {
      await Promise.all([
        loadSystemMetrics(),
        loadSystemInfo(),
        loadServices(),
        loadDatabases(),
        loadSystemLogs()
      ])
    }

    onMounted(() => {
      loadAllData()
      // Set up periodic refresh for metrics
      setInterval(loadSystemMetrics, 30000) // Refresh every 30 seconds
    })

    return {
      logLevel,
      chartTimeRange,
      systemMetrics,
      systemInfo,
      services,
      databases,
      systemLogs,
      filteredLogs,
      getProgressColor,
      getServiceStatusType,
      getDbStatusType,
      getLogType,
      formatTime,
      formatLogTime,
      refreshSystemInfo,
      refreshServices,
      testConnections,
      refreshLogs,
      toggleService
    }
  }
}
</script>

<style scoped>
.system-monitor {
  height: 100vh;
  background-color: #f5f5f5;
}

.header {
  background-color: #fff;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 20px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.header-left .title {
  margin: 0;
  font-size: 20px;
  color: #333;
}

.main-content {
  padding: 20px;
}

.overview-row {
  margin-bottom: 20px;
}

.overview-card {
  height: 120px;
}

.overview-content {
  display: flex;
  align-items: center;
  height: 100%;
}

.overview-icon {
  width: 60px;
  height: 60px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 15px;
  font-size: 28px;
  color: #fff;
}

.overview-icon.cpu {
  background-color: #409eff;
}

.overview-icon.memory {
  background-color: #67c23a;
}

.overview-icon.disk {
  background-color: #e6a23c;
}

.overview-icon.network {
  background-color: #f56c6c;
}

.overview-info {
  flex: 1;
}

.overview-title {
  font-size: 14px;
  color: #666;
  margin-bottom: 5px;
}

.overview-value {
  font-size: 24px;
  font-weight: bold;
  color: #333;
  margin-bottom: 5px;
}

.network-speed {
  font-size: 12px;
  color: #999;
}

.service-row {
  margin-bottom: 20px;
}

.service-card {
  height: 400px;
}

.info-row {
  margin-bottom: 20px;
}

.info-card {
  height: 400px;
}

.chart-card {
  height: 500px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.log-controls {
  display: flex;
  gap: 10px;
  align-items: center;
}

.chart-controls {
  display: flex;
  gap: 10px;
}

.log-container {
  padding: 10px;
}

.log-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 5px 0;
  border-bottom: 1px solid #eee;
}

.log-time {
  font-size: 12px;
  color: #999;
  width: 80px;
}

.log-message {
  flex: 1;
  font-size: 14px;
}

.performance-charts {
  display: grid;
  grid-template-columns: 1fr 1fr 1fr;
  gap: 20px;
  height: 400px;
}

.chart-item {
  text-align: center;
}

.chart-item h4 {
  margin: 0 0 10px 0;
  color: #333;
}

.mock-chart {
  height: 300px;
  background-color: #f9f9f9;
  border: 1px dashed #ddd;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #999;
  border-radius: 4px;
}
</style>