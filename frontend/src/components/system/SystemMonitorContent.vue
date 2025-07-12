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
import { ref, computed } from 'vue'

export default {
  name: 'SystemMonitorContent',
  setup() {
    const systemStats = ref({
      cpu: 45.2,
      memory: 68.5,
      disk: 72.1,
      network: '正常'
    })

    const systemInfo = ref({
      os: 'Ubuntu 20.04 LTS',
      version: 'Linux 5.4.0-74-generic',
      uptime: '15天 8小时',
      cpuModel: 'Intel Core i7-9700K',
      totalMemory: '16.0 GB',
      availableMemory: '5.1 GB'
    })

    const services = ref([
      { name: 'nginx', status: 'running' },
      { name: 'influxdb', status: 'running' },
      { name: 'redis', status: 'running' },
      { name: 'postgres', status: 'stopped' },
      { name: 'docker', status: 'running' }
    ])

    const logLevel = ref('all')

    const logs = ref([
      { id: 1, timestamp: '2024-01-15 14:30:00', level: 'INFO', message: '系统启动完成' },
      { id: 2, timestamp: '2024-01-15 14:30:15', level: 'INFO', message: 'ModbusTCP收集器连接成功' },
      { id: 3, timestamp: '2024-01-15 14:30:30', level: 'WARNING', message: 'PLC-003连接超时，正在重试' },
      { id: 4, timestamp: '2024-01-15 14:30:45', level: 'ERROR', message: 'MelsoftA1E收集器连接失败' },
      { id: 5, timestamp: '2024-01-15 14:31:00', level: 'INFO', message: '数据库连接正常' }
    ])

    const filteredLogs = computed(() => {
      if (logLevel.value === 'all') {
        return logs.value
      }
      return logs.value.filter(log => log.level.toLowerCase() === logLevel.value.toLowerCase())
    })

    const refreshSystem = () => {
      console.log('刷新系统状态')
    }

    const restartSystem = () => {
      console.log('重启系统')
    }

    const exportLogs = () => {
      console.log('导出日志')
    }

    const startService = (service) => {
      console.log('启动服务:', service.name)
    }

    const stopService = (service) => {
      console.log('停止服务:', service.name)
    }

    const refreshLogs = () => {
      console.log('刷新日志')
    }

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