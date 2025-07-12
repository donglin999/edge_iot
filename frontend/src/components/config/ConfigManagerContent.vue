<template>
  <div class="config-manager-content">
    <!-- Config Overview -->
    <el-row :gutter="20" class="stats-row">
      <el-col :span="8">
        <el-card class="stat-card">
          <el-statistic title="配置文件数量" :value="configStats.totalConfigs" />
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card class="stat-card">
          <el-statistic title="活跃配置" :value="configStats.activeConfigs" />
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card class="stat-card">
          <el-statistic title="最后更新" :value="configStats.lastUpdate" />
        </el-card>
      </el-col>
    </el-row>

    <!-- Config Actions -->
    <el-row class="action-panel">
      <el-col :span="24">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>配置管理</span>
              <div class="action-buttons">
                <el-button type="primary" @click="addConfig">
                  <el-icon><Plus /></el-icon>
                  新增配置
                </el-button>
                <el-button type="success" @click="importConfig">
                  <el-icon><Upload /></el-icon>
                  导入配置
                </el-button>
                <el-button type="info" @click="refreshConfigs">
                  <el-icon><Refresh /></el-icon>
                  刷新
                </el-button>
              </div>
            </div>
          </template>
        </el-card>
      </el-col>
    </el-row>

    <!-- Config Tabs -->
    <el-row>
      <el-col :span="24">
        <el-card class="config-tabs-card">
          <el-tabs v-model="activeConfigTab" type="border-card">
            <el-tab-pane label="设备配置" name="device">
              <div class="config-section">
                <div class="section-header">
                  <h3>设备连接配置</h3>
                  <el-button type="primary" size="small" @click="saveDeviceConfig">保存配置</el-button>
                </div>
                <el-table :data="deviceConfigs" stripe>
                  <el-table-column prop="name" label="设备名称" />
                  <el-table-column prop="type" label="设备类型" />
                  <el-table-column prop="address" label="地址" />
                  <el-table-column prop="port" label="端口" />
                  <el-table-column prop="status" label="状态">
                    <template #default="scope">
                      <el-tag :type="scope.row.status === 'connected' ? 'success' : 'danger'">
                        {{ scope.row.status === 'connected' ? '已连接' : '未连接' }}
                      </el-tag>
                    </template>
                  </el-table-column>
                  <el-table-column label="操作" width="200">
                    <template #default="scope">
                      <el-button size="small" @click="editDevice(scope.row)">编辑</el-button>
                      <el-button size="small" type="danger" @click="deleteDevice(scope.row)">删除</el-button>
                    </template>
                  </el-table-column>
                </el-table>
              </div>
            </el-tab-pane>

            <el-tab-pane label="系统配置" name="system">
              <div class="config-section">
                <div class="section-header">
                  <h3>系统设置</h3>
                  <el-button type="primary" size="small" @click="saveSystemConfig">保存配置</el-button>
                </div>
                <el-form :model="systemConfig" label-width="120px">
                  <el-form-item label="日志级别">
                    <el-select v-model="systemConfig.logLevel">
                      <el-option label="DEBUG" value="debug" />
                      <el-option label="INFO" value="info" />
                      <el-option label="WARNING" value="warning" />
                      <el-option label="ERROR" value="error" />
                    </el-select>
                  </el-form-item>
                  <el-form-item label="最大日志文件">
                    <el-input-number v-model="systemConfig.maxLogFiles" :min="1" :max="100" />
                  </el-form-item>
                  <el-form-item label="自动备份">
                    <el-switch v-model="systemConfig.autoBackup" />
                  </el-form-item>
                  <el-form-item label="监控端口">
                    <el-input-number v-model="systemConfig.monitorPort" :min="1024" :max="65535" />
                  </el-form-item>
                </el-form>
              </div>
            </el-tab-pane>
          </el-tabs>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script>
import { ref, reactive } from 'vue'

export default {
  name: 'ConfigManagerContent',
  setup() {
    const configStats = ref({
      totalConfigs: 15,
      activeConfigs: 12,
      lastUpdate: '2小时前'
    })

    const activeConfigTab = ref('device')

    const deviceConfigs = ref([
      { name: 'PLC-001', type: 'ModbusTCP', address: '192.168.1.100', port: 502, status: 'connected' },
      { name: 'PLC-002', type: 'OPC UA', address: '192.168.1.101', port: 4840, status: 'connected' },
      { name: 'PLC-003', type: 'MelsoftA1E', address: '192.168.1.102', port: 5007, status: 'disconnected' }
    ])

    const systemConfig = reactive({
      logLevel: 'info',
      maxLogFiles: 10,
      autoBackup: true,
      monitorPort: 8080
    })

    const addConfig = () => {
      console.log('新增配置')
    }

    const importConfig = () => {
      console.log('导入配置')
    }

    const refreshConfigs = () => {
      console.log('刷新配置')
    }

    const saveDeviceConfig = () => {
      console.log('保存设备配置')
    }

    const saveSystemConfig = () => {
      console.log('保存系统配置', systemConfig)
    }

    const editDevice = (device) => {
      console.log('编辑设备:', device)
    }

    const deleteDevice = (device) => {
      console.log('删除设备:', device)
    }

    return {
      configStats,
      activeConfigTab,
      deviceConfigs,
      systemConfig,
      addConfig,
      importConfig,
      refreshConfigs,
      saveDeviceConfig,
      saveSystemConfig,
      editDevice,
      deleteDevice
    }
  }
}
</script>

<style scoped>
.config-manager-content {
  width: 100%;
}

.stats-row {
  margin-bottom: 20px;
}

.stat-card {
  text-align: center;
}

.action-panel {
  margin-bottom: 20px;
}

.action-buttons {
  display: flex;
  gap: 10px;
}

.config-tabs-card {
  min-height: 600px;
}

.config-section {
  padding: 20px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding-bottom: 10px;
  border-bottom: 1px solid #eee;
}

.section-header h3 {
  margin: 0;
  color: #333;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.success {
  color: #67c23a;
  font-weight: bold;
}

.error {
  color: #f56c6c;
  font-weight: bold;
}

.info {
  color: #909399;
  font-weight: bold;
}
</style>