<template>
  <div class="config-manager">
    <el-container>
      <!-- Header -->
      <el-header height="60px" class="header">
        <div class="header-left">
          <h1 class="title">配置管理</h1>
        </div>
        <div class="header-right">
          <el-button type="primary" @click="refreshConfigs">
            <el-icon><Refresh /></el-icon>
            刷新配置
          </el-button>
        </div>
      </el-header>

      <el-main class="main-content">
        <!-- Config Upload -->
        <el-row class="upload-section">
          <el-col :span="24">
            <el-card>
              <template #header>
                <span>配置文件上传</span>
              </template>
              <el-upload
                ref="uploadRef"
                class="upload-demo"
                drag
                :auto-upload="false"
                :on-change="handleFileChange"
                :before-upload="beforeUpload"
                accept=".xlsx,.xls"
              >
                <el-icon class="el-icon--upload"><upload-filled /></el-icon>
                <div class="el-upload__text">
                  将Excel配置文件拖到此处，或<em>点击上传</em>
                </div>
                <template #tip>
                  <div class="el-upload__tip">
                    只能上传 xlsx/xls 文件，且不超过 10MB
                  </div>
                </template>
              </el-upload>
              
              <div v-if="selectedFile" class="file-info">
                <h4>已选择文件：</h4>
                <p><strong>文件名：</strong>{{ selectedFile.name }}</p>
                <p><strong>文件大小：</strong>{{ formatFileSize(selectedFile.size) }}</p>
                <p><strong>修改时间：</strong>{{ formatTime(selectedFile.lastModified) }}</p>
                
                <el-form :model="uploadForm" style="margin-top: 20px;">
                  <el-form-item label="描述信息">
                    <el-input 
                      v-model="uploadForm.description" 
                      placeholder="请输入配置文件描述"
                      type="textarea"
                      rows="3"
                    />
                  </el-form-item>
                  <el-form-item>
                    <el-checkbox v-model="uploadForm.applyImmediately">
                      上传后立即应用此配置
                    </el-checkbox>
                  </el-form-item>
                  <el-form-item>
                    <el-button type="primary" @click="uploadConfig" :loading="uploadLoading">
                      <el-icon><Upload /></el-icon>
                      上传配置
                    </el-button>
                    <el-button @click="clearFile">取消</el-button>
                  </el-form-item>
                </el-form>
              </div>
            </el-card>
          </el-col>
        </el-row>

        <!-- Current Config -->
        <el-row class="current-config">
          <el-col :span="24">
            <el-card>
              <template #header>
                <div class="card-header">
                  <span>当前配置</span>
                  <el-tag :type="currentConfig.status === 'active' ? 'success' : 'warning'">
                    {{ currentConfig.status === 'active' ? '已激活' : '未激活' }}
                  </el-tag>
                </div>
              </template>
              <el-descriptions :column="2" border>
                <el-descriptions-item label="配置文件名">
                  {{ currentConfig.filename }}
                </el-descriptions-item>
                <el-descriptions-item label="版本号">
                  {{ currentConfig.version }}
                </el-descriptions-item>
                <el-descriptions-item label="上传时间">
                  {{ formatTime(currentConfig.uploadTime) }}
                </el-descriptions-item>
                <el-descriptions-item label="文件大小">
                  {{ formatFileSize(currentConfig.fileSize) }}
                </el-descriptions-item>
                <el-descriptions-item label="设备数量">
                  {{ currentConfig.deviceCount }}
                </el-descriptions-item>
                <el-descriptions-item label="测点数量">
                  {{ currentConfig.pointCount }}
                </el-descriptions-item>
                <el-descriptions-item label="描述信息" :span="2">
                  {{ currentConfig.description || '无描述' }}
                </el-descriptions-item>
              </el-descriptions>
              
              <div class="config-actions" style="margin-top: 20px;">
                <el-button type="success" @click="validateConfig(currentConfig.id)">
                  <el-icon><Check /></el-icon>
                  验证配置
                </el-button>
                <el-button type="primary" @click="downloadConfig(currentConfig.id)">
                  <el-icon><Download /></el-icon>
                  下载配置
                </el-button>
                <el-button type="warning" @click="backupConfig">
                  <el-icon><DocumentCopy /></el-icon>
                  备份配置
                </el-button>
              </div>
            </el-card>
          </el-col>
        </el-row>

        <!-- Config History -->
        <el-row>
          <el-col :span="24">
            <el-card class="history-card">
              <template #header>
                <div class="card-header">
                  <span>配置历史</span>
                  <el-input
                    v-model="searchText"
                    placeholder="搜索配置"
                    style="width: 200px"
                    clearable
                  >
                    <template #prefix>
                      <el-icon><Search /></el-icon>
                    </template>
                  </el-input>
                </div>
              </template>
              
              <el-table :data="filteredConfigs" stripe v-loading="tableLoading">
                <el-table-column prop="filename" label="文件名" min-width="200" />
                <el-table-column prop="version" label="版本" width="100" />
                <el-table-column prop="status" label="状态" width="100">
                  <template #default="scope">
                    <el-tag :type="getStatusType(scope.row.status)">
                      {{ getStatusText(scope.row.status) }}
                    </el-tag>
                  </template>
                </el-table-column>
                <el-table-column prop="uploadTime" label="上传时间" width="180">
                  <template #default="scope">
                    {{ formatTime(scope.row.uploadTime) }}
                  </template>
                </el-table-column>
                <el-table-column prop="fileSize" label="文件大小" width="100">
                  <template #default="scope">
                    {{ formatFileSize(scope.row.fileSize) }}
                  </template>
                </el-table-column>
                <el-table-column prop="deviceCount" label="设备数" width="80" />
                <el-table-column prop="pointCount" label="测点数" width="80" />
                <el-table-column prop="description" label="描述" min-width="150" />
                <el-table-column label="操作" width="250" fixed="right">
                  <template #default="scope">
                    <el-button-group>
                      <el-button 
                        size="small" 
                        type="primary"
                        :disabled="scope.row.status === 'active'"
                        @click="applyConfig(scope.row)"
                      >
                        应用
                      </el-button>
                      <el-button 
                        size="small" 
                        @click="validateConfig(scope.row.id)"
                      >
                        验证
                      </el-button>
                      <el-button 
                        size="small" 
                        @click="downloadConfig(scope.row.id)"
                      >
                        下载
                      </el-button>
                      <el-button 
                        size="small" 
                        type="danger"
                        :disabled="scope.row.status === 'active'"
                        @click="deleteConfig(scope.row)"
                      >
                        删除
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

    <!-- Validation Dialog -->
    <el-dialog
      v-model="validationDialogVisible"
      title="配置验证结果"
      width="60%"
    >
      <div v-if="validationResult">
        <el-alert
          :title="validationResult.isValid ? '配置验证通过' : '配置验证失败'"
          :type="validationResult.isValid ? 'success' : 'error'"
          show-icon
          :closable="false"
        />
        
        <div v-if="validationResult.errors.length > 0" style="margin-top: 20px;">
          <h4>错误信息：</h4>
          <el-tag type="danger" v-for="error in validationResult.errors" :key="error" style="margin: 5px;">
            {{ error }}
          </el-tag>
        </div>
        
        <div v-if="validationResult.warnings.length > 0" style="margin-top: 20px;">
          <h4>警告信息：</h4>
          <el-tag type="warning" v-for="warning in validationResult.warnings" :key="warning" style="margin: 5px;">
            {{ warning }}
          </el-tag>
        </div>
        
        <div v-if="validationResult.summary" style="margin-top: 20px;">
          <h4>配置摘要：</h4>
          <el-descriptions :column="2" border>
            <el-descriptions-item label="设备总数">
              {{ validationResult.summary.deviceCount }}
            </el-descriptions-item>
            <el-descriptions-item label="测点总数">
              {{ validationResult.summary.pointCount }}
            </el-descriptions-item>
            <el-descriptions-item label="协议类型">
              {{ validationResult.summary.protocols?.join(', ') }}
            </el-descriptions-item>
          </el-descriptions>
        </div>
      </div>
      
      <template #footer>
        <el-button @click="validationDialogVisible = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script>
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'

export default {
  name: 'ConfigManager',
  setup() {
    const uploadRef = ref()
    const uploadLoading = ref(false)
    const tableLoading = ref(false)
    const searchText = ref('')
    const selectedFile = ref(null)
    const validationDialogVisible = ref(false)
    const validationResult = ref(null)

    const uploadForm = ref({
      description: '',
      applyImmediately: false
    })

    const currentConfig = ref({
      id: 'config_001',
      filename: 'production_config_v2.3.xlsx',
      version: 'v2.3',
      status: 'active',
      uploadTime: '2023-12-01 09:30:00',
      fileSize: 2048576,
      deviceCount: 25,
      pointCount: 156,
      description: '生产环境主配置文件，包含车间A、B、C的所有设备配置'
    })

    const configHistory = ref([
      {
        id: 'config_001',
        filename: 'production_config_v2.3.xlsx',
        version: 'v2.3',
        status: 'active',
        uploadTime: '2023-12-01 09:30:00',
        fileSize: 2048576,
        deviceCount: 25,
        pointCount: 156,
        description: '生产环境主配置文件'
      },
      {
        id: 'config_002',
        filename: 'production_config_v2.2.xlsx',
        version: 'v2.2',
        status: 'backup',
        uploadTime: '2023-11-28 14:20:00',
        fileSize: 1985674,
        deviceCount: 23,
        pointCount: 142,
        description: '上一版本的生产配置'
      },
      {
        id: 'config_003',
        filename: 'test_config_v1.5.xlsx',
        version: 'v1.5',
        status: 'invalid',
        uploadTime: '2023-11-25 10:15:00',
        fileSize: 1756423,
        deviceCount: 18,
        pointCount: 89,
        description: '测试环境配置文件'
      }
    ])

    const filteredConfigs = computed(() => {
      if (!searchText.value) return configHistory.value
      return configHistory.value.filter(config =>
        config.filename.toLowerCase().includes(searchText.value.toLowerCase()) ||
        config.description.toLowerCase().includes(searchText.value.toLowerCase())
      )
    })

    const handleFileChange = (file) => {
      selectedFile.value = file.raw
    }

    const beforeUpload = (file) => {
      const isExcel = file.type === 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' ||
                     file.type === 'application/vnd.ms-excel'
      const isLt10M = file.size / 1024 / 1024 < 10

      if (!isExcel) {
        ElMessage.error('只能上传 Excel 文件!')
        return false
      }
      if (!isLt10M) {
        ElMessage.error('文件大小不能超过 10MB!')
        return false
      }
      return true
    }

    const uploadConfig = async () => {
      if (!selectedFile.value) {
        ElMessage.error('请先选择文件')
        return
      }

      uploadLoading.value = true
      try {
        // 模拟上传过程
        await new Promise(resolve => setTimeout(resolve, 2000))
        
        ElMessage.success('配置文件上传成功!')
        clearFile()
        refreshConfigs()
      } catch (error) {
        ElMessage.error('上传失败')
      } finally {
        uploadLoading.value = false
      }
    }

    const clearFile = () => {
      selectedFile.value = null
      uploadForm.value = {
        description: '',
        applyImmediately: false
      }
      uploadRef.value?.clearFiles()
    }

    const formatFileSize = (bytes) => {
      if (bytes === 0) return '0 B'
      const k = 1024
      const sizes = ['B', 'KB', 'MB', 'GB']
      const i = Math.floor(Math.log(bytes) / Math.log(k))
      return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
    }

    const formatTime = (timeStr) => {
      if (!timeStr) return '-'
      return new Date(timeStr).toLocaleString('zh-CN')
    }

    const getStatusType = (status) => {
      switch (status) {
        case 'active': return 'success'
        case 'backup': return 'info'
        case 'invalid': return 'danger'
        default: return 'warning'
      }
    }

    const getStatusText = (status) => {
      switch (status) {
        case 'active': return '已激活'
        case 'backup': return '备份'
        case 'invalid': return '无效'
        default: return '未知'
      }
    }

    const refreshConfigs = async () => {
      tableLoading.value = true
      try {
        await new Promise(resolve => setTimeout(resolve, 1000))
        ElMessage.success('配置列表已刷新')
      } catch (error) {
        ElMessage.error('刷新失败')
      } finally {
        tableLoading.value = false
      }
    }

    const applyConfig = async (config) => {
      try {
        await ElMessageBox.confirm(
          `确定要应用配置 "${config.filename}" 吗？这将替换当前的生产配置。`,
          '确认应用配置',
          {
            confirmButtonText: '确定',
            cancelButtonText: '取消',
            type: 'warning'
          }
        )
        
        ElMessage.success(`配置 ${config.filename} 应用成功`)
      } catch (error) {
        if (error !== 'cancel') {
          ElMessage.error('应用配置失败')
        }
      }
    }

    const validateConfig = (configId) => {
      // 模拟验证结果
      validationResult.value = {
        isValid: Math.random() > 0.3,
        errors: Math.random() > 0.7 ? ['设备IP地址冲突', '无效的测点配置'] : [],
        warnings: ['建议更新设备固件版本', '部分测点响应时间较长'],
        summary: {
          deviceCount: 25,
          pointCount: 156,
          protocols: ['ModbusTCP', 'OPC UA', 'MelsoftA1E']
        }
      }
      validationDialogVisible.value = true
    }

    const downloadConfig = (configId) => {
      ElMessage.success('配置文件下载中...')
    }

    const backupConfig = () => {
      ElMessage.success('当前配置已备份')
    }

    const deleteConfig = async (config) => {
      try {
        await ElMessageBox.confirm(
          `确定要删除配置 "${config.filename}" 吗？此操作不可恢复。`,
          '确认删除',
          {
            confirmButtonText: '确定',
            cancelButtonText: '取消',
            type: 'error'
          }
        )
        
        ElMessage.success(`配置 ${config.filename} 已删除`)
      } catch (error) {
        if (error !== 'cancel') {
          ElMessage.error('删除失败')
        }
      }
    }

    onMounted(() => {
      refreshConfigs()
    })

    return {
      uploadRef,
      uploadLoading,
      tableLoading,
      searchText,
      selectedFile,
      validationDialogVisible,
      validationResult,
      uploadForm,
      currentConfig,
      configHistory,
      filteredConfigs,
      handleFileChange,
      beforeUpload,
      uploadConfig,
      clearFile,
      formatFileSize,
      formatTime,
      getStatusType,
      getStatusText,
      refreshConfigs,
      applyConfig,
      validateConfig,
      downloadConfig,
      backupConfig,
      deleteConfig
    }
  }
}
</script>

<style scoped>
.config-manager {
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

.upload-section {
  margin-bottom: 20px;
}

.current-config {
  margin-bottom: 20px;
}

.file-info {
  margin-top: 20px;
  padding: 20px;
  background-color: #f9f9f9;
  border-radius: 6px;
}

.config-actions {
  display: flex;
  gap: 10px;
}

.history-card {
  min-height: 500px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.upload-demo {
  margin-bottom: 20px;
}
</style>