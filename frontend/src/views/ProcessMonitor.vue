<template>
  <div class="process-monitor">
    <el-container>
      <!-- Header -->
      <el-header height="60px" class="header">
        <div class="header-left">
          <h1 class="title">进程监控</h1>
        </div>
        <div class="header-right">
          <el-button type="primary" @click="refreshProcesses">
            <el-icon><Refresh /></el-icon>
            刷新进程
          </el-button>
        </div>
      </el-header>

      <el-main class="main-content">
        <!-- Control Panel -->
        <el-row class="control-panel">
          <el-col :span="24">
            <el-card>
              <template #header>
                <div class="card-header">
                  <span>批量操作</span>
                </div>
              </template>
              <div class="control-buttons">
                <el-button type="success" size="large" @click="startAllProcesses">
                  <el-icon><VideoPlay /></el-icon>
                  启动所有进程
                </el-button>
                <el-button type="warning" size="large" @click="stopAllProcesses">
                  <el-icon><VideoPause /></el-icon>
                  停止所有进程
                </el-button>
                <el-button type="info" size="large" @click="restartAllProcesses">
                  <el-icon><RefreshRight /></el-icon>
                  重启所有进程
                </el-button>
              </div>
            </el-card>
          </el-col>
        </el-row>

        <!-- Process Statistics -->
        <el-row :gutter="20" class="stats-row">
          <el-col :span="6">
            <el-card class="stat-card">
              <el-statistic title="总进程数" :value="totalProcesses" />
            </el-card>
          </el-col>
          <el-col :span="6">
            <el-card class="stat-card running">
              <el-statistic title="运行中" :value="runningProcesses" />
            </el-card>
          </el-col>
          <el-col :span="6">
            <el-card class="stat-card stopped">
              <el-statistic title="已停止" :value="stoppedProcesses" />
            </el-card>
          </el-col>
          <el-col :span="6">
            <el-card class="stat-card error">
              <el-statistic title="错误状态" :value="errorProcesses" />
            </el-card>
          </el-col>
        </el-row>

        <!-- Process Table -->
        <el-row>
          <el-col :span="24">
            <el-card class="process-table-card">
              <template #header>
                <div class="card-header">
                  <span>进程详情</span>
                  <el-input
                    v-model="searchText"
                    placeholder="搜索进程名称"
                    style="width: 200px"
                    clearable
                  >
                    <template #prefix>
                      <el-icon><Search /></el-icon>
                    </template>
                  </el-input>
                </div>
              </template>
              
              <el-table :data="filteredProcesses" stripe v-loading="loading">
                <el-table-column prop="name" label="进程名称" min-width="150" />
                <el-table-column prop="type" label="类型" width="120" />
                <el-table-column prop="pid" label="PID" width="80" />
                <el-table-column prop="status" label="状态" width="100">
                  <template #default="scope">
                    <el-tag :type="getStatusType(scope.row.status)">
                      {{ getStatusText(scope.row.status) }}
                    </el-tag>
                  </template>
                </el-table-column>
                <el-table-column prop="cpu" label="CPU%" width="80" />
                <el-table-column prop="memory" label="内存" width="100" />
                <el-table-column prop="uptime" label="运行时间" width="120" />
                <el-table-column prop="startTime" label="启动时间" width="160">
                  <template #default="scope">
                    {{ formatTime(scope.row.startTime) }}
                  </template>
                </el-table-column>
                <el-table-column label="操作" width="200" fixed="right">
                  <template #default="scope">
                    <el-button-group>
                      <el-button 
                        size="small" 
                        type="success" 
                        :disabled="scope.row.status === 'running'"
                        @click="startProcess(scope.row)"
                      >
                        启动
                      </el-button>
                      <el-button 
                        size="small" 
                        type="warning"
                        :disabled="scope.row.status === 'stopped'"
                        @click="stopProcess(scope.row)"
                      >
                        停止
                      </el-button>
                      <el-button 
                        size="small" 
                        type="info"
                        @click="restartProcess(scope.row)"
                      >
                        重启
                      </el-button>
                      <el-button 
                        size="small" 
                        @click="viewLogs(scope.row)"
                      >
                        日志
                      </el-button>
                    </el-button-group>
                  </template>
                </el-table-column>
              </el-table>
            </el-card>
          </el-col>
        </el-row>
      </el-main>
    </el-container>

    <!-- Log Dialog -->
    <el-dialog
      v-model="logDialogVisible"
      :title="`${selectedProcess?.name} - 进程日志`"
      width="70%"
      top="5vh"
    >
      <div class="log-container">
        <el-scrollbar height="400px">
          <pre class="log-content">{{ processLogs }}</pre>
        </el-scrollbar>
      </div>
      <template #footer>
        <el-button @click="logDialogVisible = false">关闭</el-button>
        <el-button type="primary" @click="refreshLogs">刷新日志</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script>
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'

export default {
  name: 'ProcessMonitor',
  setup() {
    const loading = ref(false)
    const searchText = ref('')
    const logDialogVisible = ref(false)
    const selectedProcess = ref(null)
    const processLogs = ref('')
    
    // Mock data - 在实际项目中应该从API获取
    const processes = ref([
      {
        name: 'modbus_tcp_collector',
        type: 'ModbusTCP',
        pid: 1234,
        status: 'running',
        cpu: '2.5%',
        memory: '45.2MB',
        uptime: '2h 35m',
        startTime: '2023-12-01 10:30:00'
      },
      {
        name: 'opcua_collector',
        type: 'OPC UA',
        pid: 1235,
        status: 'running',
        cpu: '3.1%',
        memory: '52.8MB',
        uptime: '2h 30m',
        startTime: '2023-12-01 10:35:00'
      },
      {
        name: 'melsoft_a1e_collector',
        type: 'MelsoftA1E',
        pid: null,
        status: 'stopped',
        cpu: '0%',
        memory: '0MB',
        uptime: '0m',
        startTime: null
      },
      {
        name: 'generic_plc_collector',
        type: 'GenericPLC',
        pid: 1237,
        status: 'running',
        cpu: '1.8%',
        memory: '38.5MB',
        uptime: '1h 45m',
        startTime: '2023-12-01 11:20:00'
      },
      {
        name: 'data_processor',
        type: 'DataProcessor',
        pid: null,
        status: 'error',
        cpu: '0%',
        memory: '0MB',
        uptime: '0m',
        startTime: null
      }
    ])

    const filteredProcesses = computed(() => {
      if (!searchText.value) return processes.value
      return processes.value.filter(process =>
        process.name.toLowerCase().includes(searchText.value.toLowerCase())
      )
    })

    const totalProcesses = computed(() => processes.value.length)
    const runningProcesses = computed(() => 
      processes.value.filter(p => p.status === 'running').length
    )
    const stoppedProcesses = computed(() => 
      processes.value.filter(p => p.status === 'stopped').length
    )
    const errorProcesses = computed(() => 
      processes.value.filter(p => p.status === 'error').length
    )

    const getStatusType = (status) => {
      switch (status) {
        case 'running': return 'success'
        case 'stopped': return 'info'
        case 'error': return 'danger'
        default: return 'warning'
      }
    }

    const getStatusText = (status) => {
      switch (status) {
        case 'running': return '运行中'
        case 'stopped': return '已停止'
        case 'error': return '错误'
        default: return '未知'
      }
    }

    const formatTime = (timeStr) => {
      if (!timeStr) return '-'
      return new Date(timeStr).toLocaleString('zh-CN')
    }

    const refreshProcesses = async () => {
      loading.value = true
      try {
        // 模拟API调用
        await new Promise(resolve => setTimeout(resolve, 1000))
        ElMessage.success('进程状态已刷新')
      } catch (error) {
        ElMessage.error('刷新失败')
      } finally {
        loading.value = false
      }
    }

    const startAllProcesses = async () => {
      try {
        await ElMessageBox.confirm('确定要启动所有进程吗？', '确认操作', {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'info'
        })
        
        ElMessage.success('所有进程启动成功')
      } catch (error) {
        if (error !== 'cancel') {
          ElMessage.error('启动失败')
        }
      }
    }

    const stopAllProcesses = async () => {
      try {
        await ElMessageBox.confirm('确定要停止所有进程吗？', '确认操作', {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'warning'
        })
        
        ElMessage.success('所有进程停止成功')
      } catch (error) {
        if (error !== 'cancel') {
          ElMessage.error('停止失败')
        }
      }
    }

    const restartAllProcesses = async () => {
      try {
        await ElMessageBox.confirm('确定要重启所有进程吗？', '确认操作', {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'info'
        })
        
        ElMessage.success('所有进程重启成功')
      } catch (error) {
        if (error !== 'cancel') {
          ElMessage.error('重启失败')
        }
      }
    }

    const startProcess = (process) => {
      ElMessage.success(`进程 ${process.name} 启动成功`)
    }

    const stopProcess = (process) => {
      ElMessage.success(`进程 ${process.name} 停止成功`)
    }

    const restartProcess = (process) => {
      ElMessage.success(`进程 ${process.name} 重启成功`)
    }

    const viewLogs = (process) => {
      selectedProcess.value = process
      processLogs.value = `[2023-12-01 10:30:00] INFO: 进程 ${process.name} 启动
[2023-12-01 10:30:01] INFO: 连接到设备 192.168.1.100
[2023-12-01 10:30:02] INFO: 开始数据采集
[2023-12-01 10:30:10] INFO: 成功采集 100 个数据点
[2023-12-01 10:30:20] INFO: 数据已写入InfluxDB
[2023-12-01 10:30:30] INFO: 心跳检测正常`
      logDialogVisible.value = true
    }

    const refreshLogs = () => {
      if (selectedProcess.value) {
        processLogs.value += `\n[${new Date().toLocaleString()}] INFO: 日志已刷新`
      }
    }

    onMounted(() => {
      refreshProcesses()
    })

    return {
      loading,
      searchText,
      logDialogVisible,
      selectedProcess,
      processLogs,
      processes,
      filteredProcesses,
      totalProcesses,
      runningProcesses,
      stoppedProcesses,
      errorProcesses,
      getStatusType,
      getStatusText,
      formatTime,
      refreshProcesses,
      startAllProcesses,
      stopAllProcesses,
      restartAllProcesses,
      startProcess,
      stopProcess,
      restartProcess,
      viewLogs,
      refreshLogs
    }
  }
}
</script>

<style scoped>
.process-monitor {
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

.control-panel {
  margin-bottom: 20px;
}

.control-buttons {
  display: flex;
  gap: 20px;
  justify-content: center;
}

.stats-row {
  margin-bottom: 20px;
}

.stat-card {
  text-align: center;
}

.stat-card.running :deep(.el-statistic__number) {
  color: #67c23a;
}

.stat-card.stopped :deep(.el-statistic__number) {
  color: #909399;
}

.stat-card.error :deep(.el-statistic__number) {
  color: #f56c6c;
}

.process-table-card {
  min-height: 600px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.log-container {
  background-color: #f5f5f5;
  border-radius: 4px;
  padding: 10px;
}

.log-content {
  font-family: 'Courier New', monospace;
  font-size: 12px;
  line-height: 1.5;
  color: #333;
  margin: 0;
  white-space: pre-wrap;
}
</style>