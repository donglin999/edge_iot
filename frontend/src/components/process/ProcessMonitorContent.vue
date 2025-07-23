<template>
  <div class="process-monitor-content">
    <!-- Control Panel -->
    <el-row class="control-panel">
      <el-col :span="24">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>批量操作</span>
              <el-button type="primary" @click="refreshProcesses">
                <el-icon><Refresh /></el-icon>
                刷新进程
              </el-button>
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
        <el-card class="stat-card">
          <el-statistic title="运行中" :value="runningProcesses" />
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <el-statistic title="已停止" :value="stoppedProcesses" />
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <el-statistic title="CPU使用率" :value="avgCpuUsage" suffix="%" />
        </el-card>
      </el-col>
    </el-row>

    <!-- Process List -->
    <el-row>
      <el-col :span="24">
        <el-card class="process-list-card">
          <template #header>
            <div class="card-header">
              <span>进程详情</span>
            </div>
          </template>
          <el-table :data="processes" stripe>
            <el-table-column prop="name" label="进程名称" />
            <el-table-column prop="type" label="类型" />
            <el-table-column prop="status" label="状态">
              <template #default="scope">
                <el-tag :type="scope.row.status === 'running' ? 'success' : 'danger'">
                  {{ scope.row.status === 'running' ? '运行中' : '已停止' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="cpu" label="CPU%" />
            <el-table-column prop="memory" label="内存(MB)" />
            <el-table-column prop="startTime" label="启动时间" />
            <el-table-column label="操作" width="200">
              <template #default="scope">
                <el-button-group>
                  <el-button size="small" type="success" @click="startProcess(scope.row)">启动</el-button>
                  <el-button size="small" type="warning" @click="stopProcess(scope.row)">停止</el-button>
                  <el-button size="small" type="info" @click="restartProcess(scope.row)">重启</el-button>
                </el-button-group>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import processApi from '../../services/processApi'

export default {
  name: 'ProcessMonitorContent',
  setup() {
    const processes = ref([])
    let refreshTimer = null

    const totalProcesses = computed(() => processes.value.length)
    const runningProcesses = computed(() => processes.value.filter(p => p.status === 'running').length)
    const stoppedProcesses = computed(() => processes.value.filter(p => p.status === 'stopped').length)
    const avgCpuUsage = computed(() => {
      const running = processes.value.filter(p => p.status === 'running')
      if (running.length === 0) return 0
      const total = running.reduce((sum, p) => {
        const cpuStr = typeof p.cpu === 'string' ? p.cpu.replace('%', '') : p.cpu
        return sum + parseFloat(cpuStr || 0)
      }, 0)
      return (total / running.length).toFixed(1)
    })

    const loadProcesses = async () => {
      try {
        const response = await processApi.getProcesses()
        processes.value = response.processes || []
      } catch (error) {
        console.error('Failed to load processes:', error)
        ElMessage.error('加载进程数据失败')
      }
    }

    const refreshProcesses = async () => {
      try {
        await loadProcesses()
        ElMessage.success('进程状态已刷新')
      } catch (error) {
        ElMessage.error('刷新失败')
      }
    }

    const startAllProcesses = async () => {
      try {
        await ElMessageBox.confirm('确定要启动所有进程吗？', '确认操作', {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'info'
        })
        
        const response = await processApi.startProcesses()
        await loadProcesses()
        
        if (response.success) {
          ElMessage.success(response.message || '所有进程启动成功')
        } else {
          ElMessage.error(response.message || '启动失败')
        }
      } catch (error) {
        if (error !== 'cancel') {
          console.error('Failed to start all processes:', error)
          let errorMessage = '启动失败'
          if (error.response && error.response.data) {
            errorMessage = error.response.data.message || errorMessage
          }
          ElMessage.error(errorMessage)
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
        
        await processApi.stopProcesses()
        await loadProcesses()
        ElMessage.success('所有进程停止成功')
      } catch (error) {
        if (error !== 'cancel') {
          console.error('Failed to stop all processes:', error)
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
        
        await processApi.restartProcesses()
        await loadProcesses()
        ElMessage.success('所有进程重启成功')
      } catch (error) {
        if (error !== 'cancel') {
          console.error('Failed to restart all processes:', error)
          ElMessage.error('重启失败')
        }
      }
    }

    const startProcess = async (process) => {
      try {
        const response = await processApi.startProcesses([process.name])
        await loadProcesses()
        
        if (response.success) {
          ElMessage.success(response.message || `进程 ${process.name} 启动成功`)
        } else {
          ElMessage.error(response.message || `启动进程 ${process.name} 失败`)
        }
      } catch (error) {
        console.error('Failed to start process:', error)
        let errorMessage = `启动进程 ${process.name} 失败`
        if (error.response && error.response.data) {
          errorMessage = error.response.data.message || errorMessage
        }
        ElMessage.error(errorMessage)
      }
    }

    const stopProcess = async (process) => {
      try {
        await processApi.stopProcesses([process.name])
        await loadProcesses()
        ElMessage.success(`进程 ${process.name} 停止成功`)
      } catch (error) {
        console.error('Failed to stop process:', error)
        ElMessage.error(`停止进程 ${process.name} 失败`)
      }
    }

    const restartProcess = async (process) => {
      try {
        await processApi.restartProcesses([process.name])
        await loadProcesses()
        ElMessage.success(`进程 ${process.name} 重启成功`)
      } catch (error) {
        console.error('Failed to restart process:', error)
        ElMessage.error(`重启进程 ${process.name} 失败`)
      }
    }

    onMounted(() => {
      loadProcesses()
      // 设置定时刷新
      refreshTimer = setInterval(() => {
        loadProcesses()
      }, 10000) // 每10秒刷新进程状态
    })

    onUnmounted(() => {
      if (refreshTimer) {
        clearInterval(refreshTimer)
      }
    })

    return {
      processes,
      totalProcesses,
      runningProcesses,
      stoppedProcesses,
      avgCpuUsage,
      refreshProcesses,
      startAllProcesses,
      stopAllProcesses,
      restartAllProcesses,
      startProcess,
      stopProcess,
      restartProcess
    }
  }
}
</script>

<style scoped>
.process-monitor-content {
  width: 100%;
}

.control-panel {
  margin-bottom: 20px;
}

.control-buttons {
  display: flex;
  gap: 20px;
  justify-content: center;
  padding: 20px 0;
}

.stats-row {
  margin-bottom: 20px;
}

.stat-card {
  text-align: center;
}

.process-list-card {
  min-height: 400px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>