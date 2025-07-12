<template>
  <div class="data-viewer-content">
    <!-- Data Statistics -->
    <el-row :gutter="20" class="stats-row">
      <el-col :span="6">
        <el-card class="stat-card">
          <el-statistic title="设备总数" :value="deviceStats.total" />
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card active">
          <el-statistic title="在线设备" :value="deviceStats.online" />
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <el-statistic title="今日数据点" :value="dataStats.todayPoints" />
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="database-status">
            <div class="status-title">数据库状态</div>
            <div class="status-content">
              <el-icon :class="['status-icon', databaseStatus.type]">
                <component :is="databaseStatus.icon" />
              </el-icon>
              <span :class="['status-text', databaseStatus.type]">
                {{ databaseStatus.text }}
              </span>
            </div>
            <div class="status-detail">
              InfluxDB
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- Filter Panel -->
    <el-row class="filter-panel">
      <el-col :span="24">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>数据筛选</span>
              <el-button type="primary" @click="refreshData">
                <el-icon><Refresh /></el-icon>
                刷新数据
              </el-button>
            </div>
          </template>
          <div class="filter-controls">
            <el-form :inline="true" :model="filterForm">
              <el-form-item label="设备">
                <el-select v-model="filterForm.device" placeholder="选择设备">
                  <el-option label="全部" value="" />
                  <el-option label="PLC-001" value="PLC-001" />
                  <el-option label="PLC-002" value="PLC-002" />
                  <el-option label="PLC-003" value="PLC-003" />
                </el-select>
              </el-form-item>
              <el-form-item label="测点">
                <el-select 
                  v-model="filterForm.tags" 
                  placeholder="选择测点"
                  multiple
                  collapse-tags
                  collapse-tags-tooltip
                  style="width: 200px;"
                >
                  <el-option label="温度" value="temperature" />
                  <el-option label="压力" value="pressure" />
                  <el-option label="转速" value="speed" />
                  <el-option label="电流" value="current" />
                  <el-option label="电压" value="voltage" />
                  <el-option label="流量" value="flow" />
                  <el-option label="液位" value="level" />
                  <el-option label="功率" value="power" />
                </el-select>
              </el-form-item>
              <el-form-item label="时间范围">
                <el-date-picker
                  v-model="filterForm.timeRange"
                  type="datetimerange"
                  range-separator="至"
                  start-placeholder="开始时间"
                  end-placeholder="结束时间"
                />
              </el-form-item>
              <el-form-item>
                <el-button type="primary" @click="applyFilter">查询</el-button>
                <el-button @click="resetFilter">重置</el-button>
              </el-form-item>
            </el-form>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- Data Charts -->
    <el-row :gutter="20" class="charts-row">
      <el-col :span="12">
        <el-card class="chart-card">
          <template #header>
            <span>实时数据趋势</span>
          </template>
          <div class="chart-container">
            <p style="text-align: center; margin-top: 100px;">实时数据图表区域</p>
          </div>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card class="chart-card">
          <template #header>
            <span>设备状态分布</span>
          </template>
          <div class="chart-container">
            <p style="text-align: center; margin-top: 100px;">设备状态饼图区域</p>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- Data Table -->
    <el-row>
      <el-col :span="24">
        <el-card class="data-table-card">
          <template #header>
            <div class="card-header">
              <span>实时数据</span>
              <div class="table-actions">
                <el-button type="success" size="small" @click="exportData">
                  <el-icon><Download /></el-icon>
                  导出数据
                </el-button>
              </div>
            </div>
          </template>
          <el-table :data="dataList" stripe height="400">
            <el-table-column prop="timestamp" label="时间戳" width="180" />
            <el-table-column prop="device" label="设备名称" />
            <el-table-column prop="parameter" label="参数名称" />
            <el-table-column prop="value" label="数值" />
            <el-table-column prop="status" label="状态">
              <template #default="scope">
                <el-tag :type="scope.row.status === 'normal' ? 'success' : 'warning'">
                  {{ scope.row.status === 'normal' ? '正常' : '异常' }}
                </el-tag>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script>
import { ref, reactive, onMounted } from 'vue'

export default {
  name: 'DataViewerContent',
  setup() {
    const deviceStats = ref({
      total: 12,
      online: 10,
      offline: 2
    })

    const dataStats = ref({
      todayPoints: 25670,
      realtimeRate: 156.2
    })

    // 数据库连接状态 - 这个数据应该从后端获取
    const databaseStatus = ref({
      type: 'connected', // connected, disconnected, error
      text: '已连接',
      icon: 'SuccessFilled'
    })

    const filterForm = reactive({
      device: '',
      tags: [],
      timeRange: []
    })

    const dataList = ref([
      { timestamp: '2024-01-15 14:30:00', device: 'PLC-001', parameter: '温度', value: '23.5', status: 'normal' },
      { timestamp: '2024-01-15 14:30:01', device: 'PLC-001', parameter: '压力', value: '1.25', status: 'normal' },
      { timestamp: '2024-01-15 14:30:02', device: 'PLC-002', parameter: '转速', value: '1500', status: 'normal' },
      { timestamp: '2024-01-15 14:30:03', device: 'PLC-002', parameter: '电流', value: '12.8', status: 'warning' },
      { timestamp: '2024-01-15 14:30:04', device: 'PLC-003', parameter: '电压', value: '380.2', status: 'normal' }
    ])

    const refreshData = () => {
      console.log('刷新数据')
      fetchDatabaseStatus()
    }

    // 获取数据库状态 - 实际应该调用后端API
    const fetchDatabaseStatus = async () => {
      try {
        // 模拟API调用
        // const response = await fetch('/api/database/status')
        // const data = await response.json()
        
        // 模拟不同状态
        const statuses = [
          { type: 'connected', text: '已连接', icon: 'SuccessFilled' },
          { type: 'disconnected', text: '连接断开', icon: 'CircleClose' },
          { type: 'error', text: '连接异常', icon: 'Warning' }
        ]
        
        // 随机选择一个状态用于演示
        const randomStatus = statuses[Math.floor(Math.random() * statuses.length)]
        databaseStatus.value = randomStatus
        
      } catch (error) {
        console.error('获取数据库状态失败:', error)
        databaseStatus.value = {
          type: 'error',
          text: '获取状态失败',
          icon: 'Warning'
        }
      }
    }

    // 组件挂载时获取数据库状态
    onMounted(() => {
      fetchDatabaseStatus()
      // 可以设置定时器定期检查状态
      setInterval(fetchDatabaseStatus, 30000) // 每30秒检查一次
    })

    const applyFilter = () => {
      console.log('应用筛选:', filterForm)
    }

    const resetFilter = () => {
      filterForm.device = ''
      filterForm.tags = []
      filterForm.timeRange = []
    }

    const exportData = () => {
      console.log('导出数据')
    }

    return {
      deviceStats,
      dataStats,
      databaseStatus,
      filterForm,
      dataList,
      refreshData,
      fetchDatabaseStatus,
      applyFilter,
      resetFilter,
      exportData
    }
  }
}
</script>

<style scoped>
.data-viewer-content {
  width: 100%;
}

.stats-row {
  margin-bottom: 20px;
}

.stat-card {
  text-align: center;
}

.stat-card.active {
  border-color: #409eff;
}

.filter-panel {
  margin-bottom: 20px;
}

.filter-controls {
  padding: 10px 0;
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

.data-table-card {
  min-height: 500px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.table-actions {
  display: flex;
  gap: 10px;
}

.database-status {
  text-align: center;
  padding: 20px 10px;
}

.status-title {
  font-size: 14px;
  color: #666;
  margin-bottom: 10px;
}

.status-content {
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 8px;
}

.status-icon {
  font-size: 20px;
  margin-right: 8px;
}

.status-icon.connected {
  color: #67c23a;
}

.status-icon.disconnected {
  color: #f56c6c;
}

.status-icon.error {
  color: #e6a23c;
}

.status-text {
  font-size: 16px;
  font-weight: bold;
}

.status-text.connected {
  color: #67c23a;
}

.status-text.disconnected {
  color: #f56c6c;
}

.status-text.error {
  color: #e6a23c;
}

.status-detail {
  font-size: 12px;
  color: #909399;
}
</style>