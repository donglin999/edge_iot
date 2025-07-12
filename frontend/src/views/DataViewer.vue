<template>
  <div class="data-viewer">
    <el-container>
      <!-- Header -->
      <el-header height="60px" class="header">
        <div class="header-left">
          <h1 class="title">数据查看</h1>
        </div>
        <div class="header-right">
          <el-button type="primary" @click="refreshData">
            <el-icon><Refresh /></el-icon>
            刷新数据
          </el-button>
        </div>
      </el-header>

      <el-main class="main-content">
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
              <el-statistic title="数据点总数" :value="dataStats.totalPoints" />
            </el-card>
          </el-col>
          <el-col :span="6">
            <el-card class="stat-card">
              <el-statistic title="今日数据量" :value="dataStats.todayCount" />
            </el-card>
          </el-col>
        </el-row>

        <!-- Filter Panel -->
        <el-row class="filter-panel">
          <el-col :span="24">
            <el-card>
              <template #header>
                <span>数据筛选</span>
              </template>
              <el-form :model="filterForm" inline>
                <el-form-item label="设备">
                  <el-select v-model="filterForm.device" placeholder="选择设备" style="width: 200px">
                    <el-option label="全部设备" value="" />
                    <el-option
                      v-for="device in devices"
                      :key="device.id"
                      :label="device.name"
                      :value="device.id"
                    />
                  </el-select>
                </el-form-item>
                <el-form-item label="测点">
                  <el-select v-model="filterForm.measurement" placeholder="选择测点" style="width: 200px">
                    <el-option label="全部测点" value="" />
                    <el-option
                      v-for="measurement in measurements"
                      :key="measurement"
                      :label="measurement"
                      :value="measurement"
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
                    style="width: 300px"
                  />
                </el-form-item>
                <el-form-item>
                  <el-button type="primary" @click="queryData">
                    <el-icon><Search /></el-icon>
                    查询
                  </el-button>
                  <el-button @click="resetFilter">重置</el-button>
                  <el-button type="success" @click="exportData">
                    <el-icon><Download /></el-icon>
                    导出
                  </el-button>
                </el-form-item>
              </el-form>
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
              <div class="chart-container">
                <div class="mock-chart">
                  <p>实时数据趋势图</p>
                  <p style="font-size: 12px; color: #999;">
                    时间范围: {{ chartTimeRange }} | 
                    数据点: {{ mockChartData.length }} 个
                  </p>
                </div>
              </div>
            </el-card>
          </el-col>
          
          <el-col :span="12">
            <el-card class="chart-card">
              <template #header>
                <span>设备状态分布</span>
              </template>
              <div class="chart-container">
                <div class="device-status-chart">
                  <div class="status-item">
                    <div class="status-dot online"></div>
                    <span>在线: {{ deviceStats.online }}</span>
                  </div>
                  <div class="status-item">
                    <div class="status-dot offline"></div>
                    <span>离线: {{ deviceStats.offline }}</span>
                  </div>
                  <div class="status-item">
                    <div class="status-dot error"></div>
                    <span>异常: {{ deviceStats.error }}</span>
                  </div>
                </div>
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
                  <span>数据记录</span>
                  <div class="table-controls">
                    <el-input
                      v-model="searchText"
                      placeholder="搜索数据"
                      style="width: 200px"
                      clearable
                    >
                      <template #prefix>
                        <el-icon><Search /></el-icon>
                      </template>
                    </el-input>
                  </div>
                </div>
              </template>
              
              <el-table 
                :data="filteredTableData" 
                stripe 
                v-loading="tableLoading"
                height="400"
              >
                <el-table-column prop="timestamp" label="时间戳" width="180">
                  <template #default="scope">
                    {{ formatTime(scope.row.timestamp) }}
                  </template>
                </el-table-column>
                <el-table-column prop="deviceName" label="设备名称" width="150" />
                <el-table-column prop="measurement" label="测点" width="120" />
                <el-table-column prop="field" label="字段" width="100" />
                <el-table-column prop="value" label="数值" width="100">
                  <template #default="scope">
                    <span :class="getValueClass(scope.row.value)">
                      {{ formatValue(scope.row.value) }}
                    </span>
                  </template>
                </el-table-column>
                <el-table-column prop="unit" label="单位" width="80" />
                <el-table-column prop="quality" label="质量" width="80">
                  <template #default="scope">
                    <el-tag :type="getQualityType(scope.row.quality)" size="small">
                      {{ scope.row.quality }}
                    </el-tag>
                  </template>
                </el-table-column>
                <el-table-column prop="tags" label="标签" min-width="200">
                  <template #default="scope">
                    <el-tag 
                      v-for="(value, key) in scope.row.tags" 
                      :key="key"
                      size="small"
                      style="margin-right: 5px"
                    >
                      {{ key }}: {{ value }}
                    </el-tag>
                  </template>
                </el-table-column>
              </el-table>
              
              <div class="pagination-container">
                <el-pagination
                  v-model:current-page="currentPage"
                  v-model:page-size="pageSize"
                  :page-sizes="[20, 50, 100, 200]"
                  :total="totalRecords"
                  layout="total, sizes, prev, pager, next, jumper"
                  @size-change="handleSizeChange"
                  @current-change="handleCurrentChange"
                />
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

export default {
  name: 'DataViewer',
  setup() {
    const tableLoading = ref(false)
    const searchText = ref('')
    const chartTimeRange = ref('1h')
    const currentPage = ref(1)
    const pageSize = ref(50)
    const totalRecords = ref(1000)

    const deviceStats = ref({
      total: 25,
      online: 18,
      offline: 5,
      error: 2
    })

    const dataStats = ref({
      totalPoints: 156423,
      todayCount: 8934
    })

    const filterForm = ref({
      device: '',
      measurement: '',
      timeRange: []
    })

    const devices = ref([
      { id: 'device_001', name: 'PLC控制器-001' },
      { id: 'device_002', name: 'ModbusTCP设备-002' },
      { id: 'device_003', name: 'OPC UA服务器-003' },
      { id: 'device_004', name: '三菱PLC-004' },
      { id: 'device_005', name: '数据采集器-005' }
    ])

    const measurements = ref([
      'temperature',
      'pressure',
      'humidity',
      'voltage',
      'current',
      'power',
      'speed',
      'level'
    ])

    const mockChartData = ref([
      { time: '10:00', value: 23.5 },
      { time: '10:05', value: 24.1 },
      { time: '10:10', value: 23.8 },
      { time: '10:15', value: 25.2 },
      { time: '10:20', value: 24.7 }
    ])

    // Mock table data
    const tableData = ref([
      {
        timestamp: '2023-12-01 10:30:15',
        deviceName: 'PLC控制器-001',
        measurement: 'temperature',
        field: 'value',
        value: 23.5,
        unit: '°C',
        quality: '良好',
        tags: { location: '车间A', line: '生产线1' }
      },
      {
        timestamp: '2023-12-01 10:30:10',
        deviceName: 'ModbusTCP设备-002',
        measurement: 'pressure',
        field: 'value',
        value: 1.25,
        unit: 'MPa',
        quality: '良好',
        tags: { location: '车间B', line: '生产线2' }
      },
      {
        timestamp: '2023-12-01 10:30:05',
        deviceName: 'OPC UA服务器-003',
        measurement: 'humidity',
        field: 'value',
        value: 65.8,
        unit: '%',
        quality: '良好',
        tags: { location: '车间A', line: '生产线1' }
      },
      {
        timestamp: '2023-12-01 10:30:00',
        deviceName: '三菱PLC-004',
        measurement: 'voltage',
        field: 'value',
        value: 220.5,
        unit: 'V',
        quality: '警告',
        tags: { location: '配电室', line: '主线' }
      },
      {
        timestamp: '2023-12-01 10:29:55',
        deviceName: '数据采集器-005',
        measurement: 'current',
        field: 'value',
        value: 15.2,
        unit: 'A',
        quality: '异常',
        tags: { location: '车间C', line: '生产线3' }
      }
    ])

    const filteredTableData = computed(() => {
      if (!searchText.value) return tableData.value
      return tableData.value.filter(item =>
        item.deviceName.toLowerCase().includes(searchText.value.toLowerCase()) ||
        item.measurement.toLowerCase().includes(searchText.value.toLowerCase()) ||
        item.field.toLowerCase().includes(searchText.value.toLowerCase())
      )
    })

    const formatTime = (timeStr) => {
      return new Date(timeStr).toLocaleString('zh-CN')
    }

    const formatValue = (value) => {
      if (typeof value === 'number') {
        return value.toFixed(2)
      }
      return value
    }

    const getValueClass = (value) => {
      if (typeof value === 'number') {
        if (value > 100) return 'high-value'
        if (value < 10) return 'low-value'
      }
      return 'normal-value'
    }

    const getQualityType = (quality) => {
      switch (quality) {
        case '良好': return 'success'
        case '警告': return 'warning'
        case '异常': return 'danger'
        default: return 'info'
      }
    }

    const refreshData = async () => {
      tableLoading.value = true
      try {
        // 模拟API调用
        await new Promise(resolve => setTimeout(resolve, 1000))
        ElMessage.success('数据已刷新')
      } catch (error) {
        ElMessage.error('刷新失败')
      } finally {
        tableLoading.value = false
      }
    }

    const queryData = () => {
      tableLoading.value = true
      setTimeout(() => {
        tableLoading.value = false
        ElMessage.success('查询完成')
      }, 1000)
    }

    const resetFilter = () => {
      filterForm.value = {
        device: '',
        measurement: '',
        timeRange: []
      }
      ElMessage.info('筛选条件已重置')
    }

    const exportData = () => {
      ElMessage.success('数据导出功能开发中...')
    }

    const handleSizeChange = (newSize) => {
      pageSize.value = newSize
      currentPage.value = 1
    }

    const handleCurrentChange = (newPage) => {
      currentPage.value = newPage
    }

    onMounted(() => {
      refreshData()
    })

    return {
      tableLoading,
      searchText,
      chartTimeRange,
      currentPage,
      pageSize,
      totalRecords,
      deviceStats,
      dataStats,
      filterForm,
      devices,
      measurements,
      mockChartData,
      tableData,
      filteredTableData,
      formatTime,
      formatValue,
      getValueClass,
      getQualityType,
      refreshData,
      queryData,
      resetFilter,
      exportData,
      handleSizeChange,
      handleCurrentChange
    }
  }
}
</script>

<style scoped>
.data-viewer {
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

.stats-row {
  margin-bottom: 20px;
}

.stat-card {
  text-align: center;
}

.stat-card.active :deep(.el-statistic__number) {
  color: #67c23a;
}

.filter-panel {
  margin-bottom: 20px;
}

.charts-row {
  margin-bottom: 20px;
}

.chart-card {
  height: 350px;
}

.chart-container {
  height: 270px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.mock-chart {
  text-align: center;
  color: #666;
}

.device-status-chart {
  display: flex;
  flex-direction: column;
  gap: 20px;
  align-items: center;
}

.status-item {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 16px;
}

.status-dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
}

.status-dot.online {
  background-color: #67c23a;
}

.status-dot.offline {
  background-color: #909399;
}

.status-dot.error {
  background-color: #f56c6c;
}

.data-table-card {
  min-height: 600px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.chart-controls {
  display: flex;
  gap: 10px;
}

.table-controls {
  display: flex;
  gap: 10px;
}

.pagination-container {
  display: flex;
  justify-content: center;
  margin-top: 20px;
}

.high-value {
  color: #f56c6c;
  font-weight: bold;
}

.low-value {
  color: #e6a23c;
}

.normal-value {
  color: #333;
}
</style>