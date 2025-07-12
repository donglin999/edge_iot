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
import { ref, computed } from 'vue'

export default {
  name: 'ProcessMonitorContent',
  setup() {
    const processes = ref([
      { name: 'modbus_collector', type: 'ModbusTCP', status: 'running', cpu: '2.5%', memory: '45.2MB', startTime: '2024-01-15 09:30:00' },
      { name: 'opcua_collector', type: 'OPC UA', status: 'running', cpu: '3.1%', memory: '52.8MB', startTime: '2024-01-15 09:30:15' },
      { name: 'melsoft_collector', type: 'MelsoftA1E', status: 'stopped', cpu: '0%', memory: '0MB', startTime: '-' },
      { name: 'generic_plc', type: 'GenericPLC', status: 'running', cpu: '1.8%', memory: '38.5MB', startTime: '2024-01-15 09:31:00' },
      { name: 'data_processor', type: 'DataProcessor', status: 'running', cpu: '4.2%', memory: '67.3MB', startTime: '2024-01-15 09:32:00' }
    ])

    const totalProcesses = computed(() => processes.value.length)
    const runningProcesses = computed(() => processes.value.filter(p => p.status === 'running').length)
    const stoppedProcesses = computed(() => processes.value.filter(p => p.status === 'stopped').length)
    const avgCpuUsage = computed(() => {
      const running = processes.value.filter(p => p.status === 'running')
      if (running.length === 0) return 0
      const total = running.reduce((sum, p) => sum + parseFloat(p.cpu.replace('%', '')), 0)
      return (total / running.length).toFixed(1)
    })

    const refreshProcesses = () => {
      console.log('刷新进程列表')
    }

    const startAllProcesses = () => {
      console.log('启动所有进程')
    }

    const stopAllProcesses = () => {
      console.log('停止所有进程')
    }

    const restartAllProcesses = () => {
      console.log('重启所有进程')
    }

    const startProcess = (process) => {
      console.log('启动进程:', process.name)
    }

    const stopProcess = (process) => {
      console.log('停止进程:', process.name)
    }

    const restartProcess = (process) => {
      console.log('重启进程:', process.name)
    }

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