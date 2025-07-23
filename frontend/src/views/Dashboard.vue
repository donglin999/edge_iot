<template>
  <div class="dashboard">
    <el-container>
      <!-- Header -->
      <el-header height="60px" class="header">
        <div class="header-left">
          <h1 class="title">IoT数采系统监控平台</h1>
        </div>
        <div class="header-right">
          <el-badge value="已连接" type="success" class="connection-badge">
            <el-icon><Connection /></el-icon>
          </el-badge>
          <span class="time">{{ currentTime }}</span>
        </div>
      </el-header>

      <el-container>
        <!-- Sidebar -->
        <el-aside width="200px" class="sidebar">
          <el-menu 
            :default-active="activeTab" 
            @select="handleMenuSelect"
            unique-opened
            background-color="#304156"
            text-color="#bfcbd9"
            active-text-color="#409EFF"
          >
            <el-menu-item index="dashboard">
              <el-icon><Monitor /></el-icon>
              <span>仪表盘</span>
            </el-menu-item>
            <el-menu-item index="data">
              <el-icon><DataLine /></el-icon>
              <span>数据查看</span>
            </el-menu-item>
            <el-menu-item index="config">
              <el-icon><Document /></el-icon>
              <span>配置管理</span>
            </el-menu-item>
            <el-menu-item index="system">
              <el-icon><Platform /></el-icon>
              <span>系统监控</span>
            </el-menu-item>
          </el-menu>
        </el-aside>

        <!-- Main Content -->
        <el-main class="main-content">
          <!-- Dashboard Content -->
          <div v-show="activeTab === 'dashboard'" class="tab-content">
            <!-- Stats Cards -->
            <el-row :gutter="20" class="stats-row">
              <el-col :span="6">
                <el-card class="stats-card">
                  <div class="stats-content">
                    <div class="stats-icon running">
                      <el-icon><CircleCheck /></el-icon>
                    </div>
                    <div class="stats-info">
                      <div class="stats-value">{{ runningProcesses }}</div>
                      <div class="stats-label">运行中进程</div>
                    </div>
                  </div>
                </el-card>
              </el-col>
              
              <el-col :span="6">
                <el-card class="stats-card">
                  <div class="stats-content">
                    <div class="stats-icon stopped">
                      <el-icon><CircleClose /></el-icon>
                    </div>
                    <div class="stats-info">
                      <div class="stats-value">{{ stoppedProcesses }}</div>
                      <div class="stats-label">停止进程</div>
                    </div>
                  </div>
                </el-card>
              </el-col>
              
              <el-col :span="6">
                <el-card class="stats-card">
                  <div class="stats-content">
                    <div class="stats-icon devices">
                      <el-icon><Cpu /></el-icon>
                    </div>
                    <div class="stats-info">
                      <div class="stats-value">{{ activeDevices }}</div>
                      <div class="stats-label">活跃设备</div>
                    </div>
                  </div>
                </el-card>
              </el-col>
              
              <el-col :span="6">
                <el-card class="stats-card">
                  <div class="stats-content">
                    <div class="stats-icon data-rate">
                      <el-icon><TrendCharts /></el-icon>
                    </div>
                    <div class="stats-info">
                      <div class="stats-value">{{ dataRate }}</div>
                      <div class="stats-label">数据速率/秒</div>
                    </div>
                  </div>
                </el-card>
              </el-col>
            </el-row>

            <!-- Charts Section -->
            <el-row :gutter="20" class="charts-row">
              <el-col :span="12">
                <el-card class="chart-card">
                  <template #header>
                    <div class="card-header">
                      <span>实时数据趋势</span>
                      <el-button type="primary" size="small" @click="refreshDashboard">
                        <el-icon><Refresh /></el-icon>
                        刷新
                      </el-button>
                    </div>
                  </template>
                  <div class="chart-container">
                    <p style="text-align: center; margin-top: 100px;">图表展示区域</p>
                  </div>
                </el-card>
              </el-col>
              
              <el-col :span="12">
                <el-card class="chart-card">
                  <template #header>
                    <div class="card-header">
                      <span>进程状态分布</span>
                    </div>
                  </template>
                  <div class="chart-container">
                    <p style="text-align: center; margin-top: 100px;">饼图展示区域</p>
                  </div>
                </el-card>
              </el-col>
            </el-row>

            <!-- Process List -->
            <el-row>
              <el-col :span="24">
                <el-card class="process-card">
                  <template #header>
                    <div class="card-header">
                      <span>进程状态</span>
                      <div class="process-actions">
                        <el-button type="success" size="small" @click="startAllProcesses" :loading="loading">
                          <el-icon><VideoPlay /></el-icon>
                          全部启动
                        </el-button>
                        <el-button type="warning" size="small" @click="stopAllProcesses" :loading="loading">
                          <el-icon><VideoPause /></el-icon>
                          全部停止
                        </el-button>
                        <el-button type="info" size="small" @click="refreshDashboard" :loading="loading">
                          <el-icon><Refresh /></el-icon>
                          刷新
                        </el-button>
                      </div>
                    </div>
                  </template>
                  <el-table :data="processes" stripe v-loading="loading">
                    <el-table-column prop="name" label="进程名称" />
                    <el-table-column prop="type" label="类型" />
                    <el-table-column prop="status" label="状态">
                      <template #default="scope">
                        <el-tag :type="scope.row.status === 'running' ? 'success' : 'danger'">
                          {{ scope.row.status === 'running' ? '运行中' : '已停止' }}
                        </el-tag>
                      </template>
                    </el-table-column>
                    <el-table-column prop="cpu_percent" label="CPU%">
                      <template #default="scope">
                        {{ scope.row.cpu_percent ? scope.row.cpu_percent.toFixed(1) : '0.0' }}%
                      </template>
                    </el-table-column>
                    <el-table-column prop="memory_mb" label="内存(MB)">
                      <template #default="scope">
                        {{ scope.row.memory_mb ? scope.row.memory_mb.toFixed(1) : '0.0' }}
                      </template>
                    </el-table-column>
                    <el-table-column label="操作">
                      <template #default="scope">
                        <el-button-group>
                          <el-button size="small" 
                            @click="startProcess(scope.row.name)" 
                            :disabled="scope.row.status === 'running'"
                            :loading="scope.row.loading">
                            启动
                          </el-button>
                          <el-button size="small" 
                            @click="stopProcess(scope.row.name)"
                            :disabled="scope.row.status === 'stopped'"
                            :loading="scope.row.loading">
                            停止
                          </el-button>
                          <el-button size="small" 
                            @click="restartProcess(scope.row.name)"
                            :loading="scope.row.loading">
                            重启
                          </el-button>
                        </el-button-group>
                      </template>
                    </el-table-column>
                  </el-table>
                </el-card>
              </el-col>
            </el-row>
          </div>

          <!-- Data Viewer Content -->
          <div v-show="activeTab === 'data'" class="tab-content">
            <DataViewerContent />
          </div>

          <!-- Config Manager Content -->
          <div v-show="activeTab === 'config'" class="tab-content">
            <ConfigManagerContent />
          </div>

          <!-- System Monitor Content -->
          <div v-show="activeTab === 'system'" class="tab-content">
            <SystemMonitorContent />
          </div>
        </el-main>
      </el-container>
    </el-container>
  </div>
</template>

<script>
import { ref, onMounted, onUnmounted, computed } from 'vue'
import DataViewerContent from '../components/data/DataViewerContent.vue'
import ConfigManagerContent from '../components/config/ConfigManagerContent.vue'
import SystemMonitorContent from '../components/system/SystemMonitorContent.vue'
import processApi from '../services/processApi'
import systemApi from '../services/systemApi'
import api from '../services/api'
import { ElMessage } from 'element-plus'

export default {
  name: 'Dashboard',
  components: {
    DataViewerContent,
    ConfigManagerContent,
    SystemMonitorContent
  },
  setup() {
    const currentTime = ref('')
    const activeTab = ref('dashboard')
    const loading = ref(false)
    const processes = ref([])
    const systemMetrics = ref({})
    const dataStats = ref({})
    let timer = null
    
    // Computed properties for statistics
    const runningProcesses = computed(() => 
      processes.value.filter(p => p.status === 'running').length
    )
    
    const stoppedProcesses = computed(() => 
      processes.value.filter(p => p.status === 'stopped').length
    )
    
    const activeDevices = computed(() => dataStats.value.active_devices || 0)
    
    const dataRate = computed(() => dataStats.value.realtime_rate || 0.0)
    
    const handleMenuSelect = (index) => {
      activeTab.value = index
    }
    
    const updateTime = () => {
      const now = new Date()
      currentTime.value = now.toLocaleString('zh-CN')
    }
    
    const loadProcesses = async () => {
      try {
        loading.value = true
        const response = await processApi.getProcesses()
        processes.value = response.processes || []
      } catch (error) {
        console.error('Failed to load processes:', error)
        ElMessage.error('加载进程数据失败')
        processes.value = []
      } finally {
        loading.value = false
      }
    }
    
    const loadSystemMetrics = async () => {
      try {
        const response = await systemApi.getSystemMetrics()
        systemMetrics.value = response
      } catch (error) {
        console.error('Failed to load system metrics:', error)
      }
    }
    
    const loadDataStats = async () => {
      try {
        const response = await api.get('/api/data/statistics')
        dataStats.value = response
      } catch (error) {
        console.error('Failed to load data stats:', error)
      }
    }
    
    const refreshDashboard = async () => {
      await Promise.all([
        loadProcesses(),
        loadSystemMetrics(),
        loadDataStats()
      ])
    }
    
    const startAllProcesses = async () => {
      try {
        loading.value = true
        const response = await processApi.startProcesses([])
        if (response.success) {
          ElMessage.success(response.message)
          await loadProcesses()
        } else {
          ElMessage.error(response.message)
        }
      } catch (error) {
        console.error('Failed to start all processes:', error)
        ElMessage.error('启动所有进程失败')
      } finally {
        loading.value = false
      }
    }
    
    const stopAllProcesses = async () => {
      try {
        loading.value = true
        const response = await processApi.stopProcesses([])
        if (response.success) {
          ElMessage.success(response.message)
          await loadProcesses()
        } else {
          ElMessage.error(response.message)
        }
      } catch (error) {
        console.error('Failed to stop all processes:', error)
        ElMessage.error('停止所有进程失败')
      } finally {
        loading.value = false
      }
    }
    
    const startProcess = async (processName) => {
      try {
        // Set loading state for specific process
        const process = processes.value.find(p => p.name === processName)
        if (process) process.loading = true
        
        const response = await processApi.startProcesses([processName])
        if (response.success) {
          ElMessage.success(`进程 ${processName} 启动成功`)
          await loadProcesses()
        } else {
          ElMessage.error(response.message)
        }
      } catch (error) {
        console.error(`Failed to start process ${processName}:`, error)
        ElMessage.error(`启动进程 ${processName} 失败`)
      } finally {
        const process = processes.value.find(p => p.name === processName)
        if (process) process.loading = false
      }
    }
    
    const stopProcess = async (processName) => {
      try {
        const process = processes.value.find(p => p.name === processName)
        if (process) process.loading = true
        
        const response = await processApi.stopProcesses([processName])
        if (response.success) {
          ElMessage.success(`进程 ${processName} 停止成功`)
          await loadProcesses()
        } else {
          ElMessage.error(response.message)
        }
      } catch (error) {
        console.error(`Failed to stop process ${processName}:`, error)
        ElMessage.error(`停止进程 ${processName} 失败`)
      } finally {
        const process = processes.value.find(p => p.name === processName)
        if (process) process.loading = false
      }
    }
    
    const restartProcess = async (processName) => {
      try {
        const process = processes.value.find(p => p.name === processName)
        if (process) process.loading = true
        
        const response = await processApi.restartProcesses([processName])
        if (response.success) {
          ElMessage.success(`进程 ${processName} 重启成功`)
          await loadProcesses()
        } else {
          ElMessage.error(response.message)
        }
      } catch (error) {
        console.error(`Failed to restart process ${processName}:`, error)
        ElMessage.error(`重启进程 ${processName} 失败`)
      } finally {
        const process = processes.value.find(p => p.name === processName)
        if (process) process.loading = false
      }
    }
    
    const startTimer = () => {
      timer = setInterval(() => {
        updateTime()
        // Refresh metrics every 30 seconds
        if (Date.now() % 30000 < 1000) {
          loadSystemMetrics()
          loadDataStats()
        }
      }, 1000)
    }
    
    const stopTimer = () => {
      if (timer) {
        clearInterval(timer)
        timer = null
      }
    }
    
    onMounted(async () => {
      updateTime()
      startTimer()
      await refreshDashboard()
    })
    
    onUnmounted(() => {
      stopTimer()
    })
    
    return {
      currentTime,
      activeTab,
      loading,
      processes,
      runningProcesses,
      stoppedProcesses,
      activeDevices,
      dataRate,
      handleMenuSelect,
      refreshDashboard,
      startAllProcesses,
      stopAllProcesses,
      startProcess,
      stopProcess,
      restartProcess
    }
  }
}
</script>

<style scoped>
.dashboard {
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

.header-right {
  display: flex;
  align-items: center;
  gap: 20px;
}

.connection-badge {
  margin-right: 10px;
}

.time {
  font-size: 14px;
  color: #666;
}

.sidebar {
  background-color: #304156;
}

.main-content {
  padding: 20px;
  background-color: #f5f5f5;
}

.stats-row {
  margin-bottom: 20px;
}

.stats-card {
  height: 100px;
}

.stats-content {
  display: flex;
  align-items: center;
  height: 100%;
}

.stats-icon {
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

.stats-icon.running {
  background-color: #67c23a;
}

.stats-icon.stopped {
  background-color: #f56c6c;
}

.stats-icon.devices {
  background-color: #409eff;
}

.stats-icon.data-rate {
  background-color: #e6a23c;
}

.stats-info {
  flex: 1;
}

.stats-value {
  font-size: 24px;
  font-weight: bold;
  color: #333;
}

.stats-label {
  font-size: 14px;
  color: #666;
  margin-top: 5px;
}

.charts-row {
  margin-bottom: 20px;
}

.chart-card {
  height: 400px;
}

.chart-container {
  height: 320px;
}

.process-card {
  min-height: 500px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.process-actions {
  display: flex;
  gap: 10px;
}

.tab-content {
  width: 100%;
  height: 100%;
}
</style>