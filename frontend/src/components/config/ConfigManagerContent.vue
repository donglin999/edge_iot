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
                <el-upload
                  ref="uploadRef"
                  action="#"
                  :auto-upload="false"
                  :on-change="handleFileSelect"
                  :show-file-list="false"
                  accept=".xlsx,.xls"
                >
                  <el-button type="primary">
                    <el-icon><Upload /></el-icon>
                    导入Excel配置
                  </el-button>
                </el-upload>
                <el-button type="success" @click="applyConfig" :disabled="!selectedConfig" :loading="applying">
                  <el-icon><Check /></el-icon>
                  应用配置
                </el-button>
                <el-button type="info" @click="refreshConfigs" :loading="loading">
                  <el-icon><Refresh /></el-icon>
                  刷新
                </el-button>
              </div>
            </div>
          </template>
          
          <!-- Excel Upload Dialog -->
          <el-dialog
            v-model="uploadDialogVisible"
            title="导入Excel配置文件"
            width="600px"
          >
            <div v-if="selectedFile">
              <p><strong>文件名：</strong>{{ selectedFile.name }}</p>
              <p><strong>文件大小：</strong>{{ (selectedFile.size / 1024).toFixed(2) }}KB</p>
              
              <el-form :model="uploadForm" label-width="100px">
                <el-form-item label="描述">
                  <el-input v-model="uploadForm.description" placeholder="请输入配置描述"></el-input>
                </el-form-item>
                <el-form-item label="立即应用">
                  <el-switch v-model="uploadForm.apply_immediately"></el-switch>
                </el-form-item>
              </el-form>
            </div>
            
            <template #footer>
              <span class="dialog-footer">
                <el-button @click="uploadDialogVisible = false">取消</el-button>
                <el-button type="primary" @click="uploadConfig" :loading="uploading">
                  上传并解析
                </el-button>
              </span>
            </template>
          </el-dialog>
        </el-card>
      </el-col>
    </el-row>

    <!-- Config Tabs -->
    <el-row>
      <el-col :span="24">
        <el-card class="config-tabs-card">
          <el-tabs v-model="activeConfigTab" type="border-card">
            <el-tab-pane label="配置历史" name="history">
              <div class="config-section">
                <div class="section-header">
                  <h3>配置文件历史</h3>
                </div>
                <el-table :data="configHistory" stripe v-loading="loading" @row-click="selectConfig">
                  <el-table-column prop="filename" label="文件名" />
                  <el-table-column prop="upload_time" label="上传时间">
                    <template #default="scope">
                      {{ new Date(scope.row.upload_time).toLocaleString() }}
                    </template>
                  </el-table-column>
                  <el-table-column prop="file_size" label="文件大小">
                    <template #default="scope">
                      {{ (scope.row.file_size / 1024).toFixed(2) }}KB
                    </template>
                  </el-table-column>
                  <el-table-column prop="status" label="状态">
                    <template #default="scope">
                      <el-tag :type="getStatusType(scope.row.status)">
                        {{ getStatusText(scope.row.status) }}
                      </el-tag>
                    </template>
                  </el-table-column>
                  <el-table-column prop="description" label="描述" />
                  <el-table-column label="操作" width="200">
                    <template #default="scope">
                      <el-button size="small" @click="validateConfig(scope.row.id)" :loading="scope.row.validating">
                        验证
                      </el-button>
                      <el-button size="small" type="success" @click="selectAndApplyConfig(scope.row)" 
                        :disabled="scope.row.status === 'invalid'" :loading="scope.row.applying">
                        应用
                      </el-button>
                    </template>
                  </el-table-column>
                </el-table>
              </div>
            </el-tab-pane>

            <el-tab-pane label="当前配置" name="current">
              <div class="config-section">
                <div class="section-header">
                  <h3>当前生效配置</h3>
                </div>
                <el-descriptions :column="2" border v-if="currentConfig">
                  <el-descriptions-item label="配置文件">{{ currentConfig.filename }}</el-descriptions-item>
                  <el-descriptions-item label="版本">{{ currentConfig.version }}</el-descriptions-item>
                  <el-descriptions-item label="最后更新">{{ new Date(currentConfig.last_updated).toLocaleString() }}</el-descriptions-item>
                  <el-descriptions-item label="设备数量">{{ currentConfig.devices }}</el-descriptions-item>
                  <el-descriptions-item label="数据点数量">{{ currentConfig.points }}</el-descriptions-item>
                </el-descriptions>
                <el-empty v-else description="暂无配置" />
              </div>
            </el-tab-pane>

            <el-tab-pane label="配置验证" name="validation">
              <div class="config-section">
                <div class="section-header">
                  <h3>配置验证结果</h3>
                </div>
                <div v-if="validationResult">
                  <el-alert
                    :title="validationResult.is_valid ? '配置验证通过' : '配置验证失败'"
                    :type="validationResult.is_valid ? 'success' : 'error'"
                    :closable="false"
                    style="margin-bottom: 20px;"
                  />
                  
                  <el-descriptions :column="1" border v-if="validationResult.summary">
                    <el-descriptions-item label="设备总数">{{ validationResult.summary.total_devices || 0 }}</el-descriptions-item>
                    <el-descriptions-item label="数据点总数">{{ validationResult.summary.total_points || 0 }}</el-descriptions-item>
                    <el-descriptions-item label="支持协议">{{ (validationResult.summary.protocols || []).join(', ') }}</el-descriptions-item>
                  </el-descriptions>
                  
                  <div v-if="validationResult.errors && validationResult.errors.length > 0" style="margin-top: 20px;">
                    <h4>错误信息:</h4>
                    <ul>
                      <li v-for="error in validationResult.errors" :key="error" style="color: #f56c6c;">{{ error }}</li>
                    </ul>
                  </div>
                  
                  <div v-if="validationResult.warnings && validationResult.warnings.length > 0" style="margin-top: 20px;">
                    <h4>警告信息:</h4>
                    <ul>
                      <li v-for="warning in validationResult.warnings" :key="warning" style="color: #e6a23c;">{{ warning }}</li>
                    </ul>
                  </div>
                </div>
                <el-empty v-else description="请先选择配置文件进行验证" />
              </div>
            </el-tab-pane>
          </el-tabs>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script>
import { ref, reactive, onMounted } from 'vue'
import api from '../../services/api'
import { ElMessage } from 'element-plus'

export default {
  name: 'ConfigManagerContent',
  setup() {
    const loading = ref(false)
    const uploading = ref(false)
    const applying = ref(false)
    const uploadDialogVisible = ref(false)
    const selectedFile = ref(null)
    const selectedConfig = ref(null)
    
    const configStats = ref({
      totalConfigs: 0,
      activeConfigs: 0,
      lastUpdate: '-'
    })

    const activeConfigTab = ref('history')
    const configHistory = ref([])
    const currentConfig = ref(null)
    const validationResult = ref(null)
    
    const uploadForm = reactive({
      description: '',
      apply_immediately: false
    })

    // Load configuration data
    const loadConfigHistory = async () => {
      try {
        loading.value = true
        const response = await api.get('/api/config/history')
        configHistory.value = response.configs || []
        configStats.value.totalConfigs = response.total_count || 0
        configStats.value.activeConfigs = configHistory.value.filter(c => c.status === 'active').length
      } catch (error) {
        console.error('Failed to load config history:', error)
        ElMessage.error('加载配置历史失败')
      } finally {
        loading.value = false
      }
    }
    
    const loadCurrentConfig = async () => {
      try {
        const response = await api.get('/api/config/current')
        currentConfig.value = response
        if (response.last_updated) {
          configStats.value.lastUpdate = new Date(response.last_updated).toLocaleString()
        }
      } catch (error) {
        console.error('Failed to load current config:', error)
        currentConfig.value = null
      }
    }
    
    const refreshConfigs = async () => {
      await Promise.all([
        loadConfigHistory(),
        loadCurrentConfig()
      ])
    }

    // File upload handling
    const handleFileSelect = (uploadFile) => {
      selectedFile.value = uploadFile.raw
      uploadDialogVisible.value = true
    }
    
    const uploadConfig = async () => {
      if (!selectedFile.value) {
        ElMessage.error('请选择文件')
        return
      }
      
      try {
        uploading.value = true
        const formData = new FormData()
        formData.append('file', selectedFile.value)
        formData.append('description', uploadForm.description)
        formData.append('apply_immediately', uploadForm.apply_immediately)
        
        const response = await api.post('/api/config/upload', formData, {
          headers: {
            'Content-Type': 'multipart/form-data'
          }
        })
        
        if (response.success) {
          ElMessage.success(response.message)
          uploadDialogVisible.value = false
          selectedFile.value = null
          uploadForm.description = ''
          uploadForm.apply_immediately = false
          
          // Show validation result
          if (response.validation) {
            validationResult.value = response.validation
            activeConfigTab.value = 'validation'
          }
          
          await refreshConfigs()
        } else {
          ElMessage.error(response.message)
        }
      } catch (error) {
        console.error('Failed to upload config:', error)
        ElMessage.error('上传配置失败')
      } finally {
        uploading.value = false
      }
    }
    
    // Config management
    const selectConfig = (config) => {
      selectedConfig.value = config
    }
    
    const validateConfig = async (configId) => {
      try {
        const config = configHistory.value.find(c => c.id === configId)
        if (config) config.validating = true
        
        const response = await api.get(`/api/config/validate/${configId}`)
        validationResult.value = response
        activeConfigTab.value = 'validation'
        
        ElMessage.success('配置验证完成')
      } catch (error) {
        console.error('Failed to validate config:', error)
        ElMessage.error('配置验证失败')
      } finally {
        const config = configHistory.value.find(c => c.id === configId)
        if (config) config.validating = false
      }
    }
    
    const applyConfig = async () => {
      if (!selectedConfig.value) {
        ElMessage.error('请先选择配置')
        return
      }
      
      try {
        applying.value = true
        const response = await api.post('/api/config/apply', {
          config_id: selectedConfig.value.id,
          force: false,
          backup_current: true
        })
        
        if (response.success) {
          ElMessage.success(response.message)
          await refreshConfigs()
          activeConfigTab.value = 'current'
        } else {
          ElMessage.error(response.message)
        }
      } catch (error) {
        console.error('Failed to apply config:', error)
        ElMessage.error('应用配置失败')
      } finally {
        applying.value = false
      }
    }
    
    const selectAndApplyConfig = async (config) => {
      selectedConfig.value = config
      await applyConfig()
    }
    
    // Helper functions
    const getStatusType = (status) => {
      switch (status) {
        case 'active': return 'success'
        case 'pending': return 'warning'
        case 'invalid': return 'danger'
        case 'backup': return 'info'
        default: return 'info'
      }
    }
    
    const getStatusText = (status) => {
      switch (status) {
        case 'active': return '已激活'
        case 'pending': return '待应用'
        case 'invalid': return '无效'
        case 'backup': return '备份'
        default: return '未知'
      }
    }
    
    onMounted(async () => {
      await refreshConfigs()
    })

    return {
      loading,
      uploading,
      applying,
      uploadDialogVisible,
      selectedFile,
      selectedConfig,
      configStats,
      activeConfigTab,
      configHistory,
      currentConfig,
      validationResult,
      uploadForm,
      refreshConfigs,
      handleFileSelect,
      uploadConfig,
      selectConfig,
      validateConfig,
      applyConfig,
      selectAndApplyConfig,
      getStatusType,
      getStatusText
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