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
                <el-select v-model="filterForm.device" placeholder="选择设备" @change="handleDeviceChange">
                  <el-option label="全部" value="" />
                  <el-option 
                    v-for="device in deviceList" 
                    :key="device.id" 
                    :label="device.name" 
                    :value="device.id" 
                  />
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
                  <el-option 
                    v-for="tag in tagList" 
                    :key="tag.name" 
                    :label="tag.description || tag.name" 
                    :value="tag.name" 
                  />
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
import { ref, reactive, onMounted, onUnmounted, computed } from 'vue'
import { ElMessage } from 'element-plus'
import dataApi from '../../services/dataApi'
import systemApi from '../../services/systemApi'

export default {
  name: 'DataViewerContent',
  setup() {
    const deviceStats = ref({
      total: 0,
      online: 0,
      offline: 0
    })

    const dataStats = ref({
      todayPoints: 0,
      realtimeRate: 0
    })

    const databaseStatus = ref({
      type: 'connected',
      text: '检查中...',
      icon: 'Loading'
    })

    const deviceList = ref([])
    const tagList = ref([])
    const dataList = ref([])
    let refreshTimer = null

    const filterForm = reactive({
      device: '',
      tags: [],
      timeRange: []
    })

    // API调用函数
    const loadDeviceStats = async () => {
      try {
        const devices = await dataApi.getDevices()
        deviceStats.value = {
          total: devices.length || 0,
          online: devices.filter(d => d.status === 'online').length || 0,
          offline: devices.filter(d => d.status === 'offline').length || 0
        }
        deviceList.value = devices || []
      } catch (error) {
        console.error('Failed to load device stats:', error)
      }
    }

    const loadDataStats = async () => {
      try {
        const stats = await dataApi.getStatistics()
        dataStats.value = {
          todayPoints: stats.today_points || 0,
          realtimeRate: stats.realtime_rate || 0
        }
      } catch (error) {
        console.error('Failed to load data stats:', error)
      }
    }

    const loadDatabaseStatus = async () => {
      try {
        const response = await systemApi.getDatabaseStatus()
        const influxdb = response.databases.find(db => db.name === 'InfluxDB')
        if (influxdb) {
          databaseStatus.value = {
            type: influxdb.status === '已连接' ? 'connected' : 'disconnected',
            text: influxdb.status,
            icon: influxdb.status === '已连接' ? 'SuccessFilled' : 'CircleClose'
          }
        }
      } catch (error) {
        console.error('Failed to load database status:', error)
        databaseStatus.value = {
          type: 'error',
          text: '获取状态失败',
          icon: 'Warning'
        }
      }
    }

    const loadTagList = async () => {
      try {
        const measurements = await dataApi.getMeasurements(filterForm.device)
        tagList.value = measurements || []
      } catch (error) {
        console.error('Failed to load tag list:', error)
      }
    }

    const loadRealTimeData = async () => {
      try {
        const query = {
          device: filterForm.device,
          measurements: filterForm.tags,
          start_time: filterForm.timeRange[0],
          end_time: filterForm.timeRange[1],
          limit: 100
        }
        
        const response = await dataApi.getRealtimeData(query)
        dataList.value = response.data || []
      } catch (error) {
        console.error('Failed to load real-time data:', error)
        ElMessage.error('加载实时数据失败')
      }
    }

    const loadAllData = async () => {
      await Promise.all([
        loadDeviceStats(),
        loadDataStats(),
        loadDatabaseStatus(),
        loadTagList(),
        loadRealTimeData()
      ])
    }

    const refreshData = async () => {
      try {
        await loadAllData()
        ElMessage.success('数据已刷新')
      } catch (error) {
        ElMessage.error('刷新数据失败')
      }
    }

    const applyFilter = async () => {
      try {
        await loadRealTimeData()
        ElMessage.success('筛选条件已应用')
      } catch (error) {
        ElMessage.error('筛选失败')
      }
    }

    const resetFilter = () => {
      filterForm.device = ''
      filterForm.tags = []
      filterForm.timeRange = []
      loadRealTimeData()
    }

    const exportData = async () => {
      try {
        const query = {
          device: filterForm.device,
          measurements: filterForm.tags,
          start_time: filterForm.timeRange[0],
          end_time: filterForm.timeRange[1]
        }
        
        const response = await dataApi.exportData(query, 'csv')
        
        // 创建下载链接
        const blob = new Blob([response], { type: 'text/csv' })
        const url = window.URL.createObjectURL(blob)
        const link = document.createElement('a')
        link.href = url
        link.download = `iot_data_${new Date().toISOString().slice(0, 10)}.csv`
        link.click()
        window.URL.revokeObjectURL(url)
        
        ElMessage.success('数据导出成功')
      } catch (error) {
        console.error('Failed to export data:', error)
        ElMessage.error('数据导出失败')
      }
    }

    // 监听设备变化，更新标签列表
    const handleDeviceChange = () => {
      filterForm.tags = []
      if (filterForm.device) {
        loadTagList()
      }
    }

    onMounted(() => {
      loadAllData()
      // 设置定时刷新
      refreshTimer = setInterval(() => {
        loadDataStats()
        loadDatabaseStatus()
        if (filterForm.tags.length > 0) {
          loadRealTimeData()
        }
      }, 30000) // 每30秒刷新数据
    })

    onUnmounted(() => {
      if (refreshTimer) {
        clearInterval(refreshTimer)
      }
    })

    return {
      deviceStats,
      dataStats,
      databaseStatus,
      deviceList,
      tagList,
      dataList,
      filterForm,
      refreshData,
      applyFilter,
      resetFilter,
      exportData,
      handleDeviceChange
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