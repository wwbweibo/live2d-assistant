<template>
  <div class="knowledge-base-modal">
    <!-- 上传区域 -->
    <div class="upload-section">
      <h3 class="section-title">文件上传</h3>
      <div class="upload-area">
        <Upload
          :file-list="fileList"
          :before-upload="beforeUpload"
          :custom-request="handleUpload"
          :disabled="isUploading || isProcessing"
          accept=".pdf,.doc,.docx,.txt,.jpg,.jpeg,.png,.gif"
          :show-upload-list="false"
        >
          <div class="upload-dragger" :class="{ disabled: isUploading || isProcessing }">
            <p class="upload-icon">
              <InboxOutlined v-if="!isUploading && !isProcessing" />
              <LoadingOutlined v-else />
            </p>
            <p class="upload-text">
              <span v-if="!isUploading && !isProcessing">点击或拖拽文件到此处上传</span>
              <span v-else-if="isUploading">正在上传...</span>
              <span v-else>正在处理...</span>
            </p>
            <p class="upload-hint">支持: PDF, Word, TXT, 图片格式</p>
          </div>
        </Upload>
        
        <!-- 上传进度 -->
        <div v-if="uploadProgress > 0" class="upload-progress">
          <Progress :percent="uploadProgress" :status="uploadStatus" />
          <span class="progress-text">{{ uploadStatusText }}</span>
        </div>
      </div>
    </div>

    <!-- 文件列表 -->
    <div class="file-list-section">
      <h3 class="section-title">
        文件列表
        <span class="file-count">({{ knowledgeFiles.length }})</span>
      </h3>
      
      <div class="file-list" v-if="knowledgeFiles.length > 0">
        <div 
          v-for="file in knowledgeFiles" 
          :key="file.id"
          class="file-item"
          :class="{ active: selectedFile?.id === file.id }"
          @click="selectFile(file)"
        >
          <div class="file-info">
            <div class="file-icon">
              <FileTextOutlined v-if="file.type.includes('text') || file.type.includes('pdf')" />
              <FileWordOutlined v-else-if="file.type.includes('word') || file.type.includes('doc')" />
              <FileImageOutlined v-else-if="file.type.includes('image')" />
              <FileOutlined v-else />
            </div>
            <div class="file-details">
              <div class="file-name">{{ file.name }}</div>
              <div class="file-meta">
                <span class="file-size">{{ formatFileSize(file.size) }}</span>
                <span class="file-date">{{ formatDate(file.uploadTime) }}</span>
              </div>
              <div class="file-status" :class="file.status">
                <span v-if="file.status === 'processing'" class="status-processing">
                  <LoadingOutlined /> 处理中...
                </span>
                <span v-else-if="file.status === 'completed'" class="status-completed">
                  <CheckCircleOutlined /> 已完成
                </span>
                <span v-else-if="file.status === 'failed'" class="status-failed">
                  <ExclamationCircleOutlined /> 处理失败
                </span>
              </div>
            </div>
          </div>
          <div class="file-actions">
            <Button 
              type="text" 
              size="small"
              @click.stop="deleteFile(file.id)"
              :loading="deletingFiles.includes(file.id)"
            >
              <DeleteOutlined />
            </Button>
          </div>
        </div>
      </div>
      
      <Empty v-else description="暂无文件" />
    </div>

    <!-- 文件内容展示 -->
    <div class="file-content-section" v-if="selectedFile">
      <h3 class="section-title">
        文件内容
        <span class="file-title">{{ selectedFile.name }}</span>
      </h3>
      
      <div class="content-area">
        <div v-if="selectedFile.status === 'processing'" class="content-loading">
          <Spin size="large" />
          <p>正在处理文件内容...</p>
        </div>
        
        <div v-else-if="selectedFile.status === 'failed'" class="content-error">
          <ExclamationCircleOutlined />
          <p>文件处理失败</p>
          <p class="error-detail">{{ selectedFile.error || '未知错误' }}</p>
        </div>
        
        <div v-else-if="selectedFile.content" class="content-display">
          <!-- 图片内容 -->
          <div v-if="selectedFile.type.includes('image')" class="image-content">
            <img :src="selectedFile.url" :alt="selectedFile.name" />
          </div>
          
          <!-- 文本内容 -->
          <div v-else class="text-content">
            <div class="content-toolbar">
              <Button size="small" @click="copyContent">
                <CopyOutlined /> 复制内容
              </Button>
            </div>
            <pre class="content-text">{{ selectedFile.content }}</pre>
          </div>
        </div>
        
        <Empty v-else description="无内容" />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import { 
  Upload, Button, Progress, Empty, Spin, message 
} from 'ant-design-vue'
import {
  InboxOutlined,
  LoadingOutlined,
  FileTextOutlined,
  FileWordOutlined,
  FileImageOutlined,
  FileOutlined,
  CheckCircleOutlined,
  ExclamationCircleOutlined,
  DeleteOutlined,
  CopyOutlined
} from '@ant-design/icons-vue'
import type { KnowledgeFile } from '../types/message'

// 响应式数据
const fileList = ref([])
const knowledgeFiles = ref<KnowledgeFile[]>([])
const selectedFile = ref<KnowledgeFile | null>(null)
const isUploading = ref(false)
const isProcessing = ref(false)
const uploadProgress = ref(0)
const uploadStatus = ref<'active' | 'success' | 'exception'>('active')
const deletingFiles = ref<string[]>([])

// 计算属性
const uploadStatusText = computed(() => {
  if (uploadStatus.value === 'active') return '上传中...'
  if (uploadStatus.value === 'success') return '上传完成'
  if (uploadStatus.value === 'exception') return '上传失败'
  return ''
})

// 文件上传前的验证
const beforeUpload = (file: File) => {
  const isValidType = /\.(pdf|doc|docx|txt|jpg|jpeg|png|gif)$/i.test(file.name)
  if (!isValidType) {
    message.error('只支持 PDF、Word、TXT、图片格式的文件')
    return false
  }
  
  const isLt50M = file.size / 1024 / 1024 < 50
  if (!isLt50M) {
    message.error('文件大小不能超过 50MB')
    return false
  }
  
  return true
}

// 自定义上传处理
const handleUpload = async (options: any) => {
  const { file } = options
  
  try {
    isUploading.value = true
    uploadProgress.value = 0
    uploadStatus.value = 'active'
    
    // 模拟上传进度
    const progressInterval = setInterval(() => {
      if (uploadProgress.value < 90) {
        uploadProgress.value += 10
      }
    }, 200)
    
    // 创建FormData
    const formData = new FormData()
    formData.append('file', file)
    
    // 发送上传请求
    const response = await fetch('/api/knowledge/upload', {
      method: 'POST',
      body: formData
    })
    
    clearInterval(progressInterval)
    
    if (response.ok) {
      const result = await response.json()
      uploadProgress.value = 100
      uploadStatus.value = 'success'
      
      // 添加到文件列表
      const newFile: KnowledgeFile = {
        id: result.fileId || Date.now().toString(),
        name: file.name,
        type: file.type,
        size: file.size,
        uploadTime: Date.now(),
        status: 'processing'
      }
      
      knowledgeFiles.value.unshift(newFile)
      message.success('文件上传成功，正在处理中...')
      
      // 开始轮询处理状态
      pollProcessingStatus(newFile.id)
      
    } else {
      throw new Error('上传失败')
    }
    
  } catch (error) {
    uploadStatus.value = 'exception'
    message.error('文件上传失败')
    console.error('Upload error:', error)
  } finally {
    isUploading.value = false
    setTimeout(() => {
      uploadProgress.value = 0
    }, 1000)
  }
}

// 轮询处理状态
const pollProcessingStatus = async (fileId: string) => {
  isProcessing.value = true
  
  const checkStatus = async () => {
    try {
      const response = await fetch(`/api/knowledge/status/${fileId}`)
      if (response.ok) {
        const result = await response.json()
        const fileIndex = knowledgeFiles.value.findIndex(f => f.id === fileId)
        
        if (fileIndex !== -1) {
          knowledgeFiles.value[fileIndex].status = result.status
          
          if (result.status === 'completed') {
            knowledgeFiles.value[fileIndex].content = result.content
            knowledgeFiles.value[fileIndex].url = result.url
            message.success('文件处理完成')
            isProcessing.value = false
            return
          } else if (result.status === 'failed') {
            knowledgeFiles.value[fileIndex].error = result.error
            message.error('文件处理失败')
            isProcessing.value = false
            return
          }
        }
      }
    } catch (error) {
      console.error('Status check error:', error)
    }
    
    // 继续轮询
    setTimeout(checkStatus, 2000)
  }
  
  checkStatus()
}

// 选择文件
const selectFile = (file: KnowledgeFile) => {
  selectedFile.value = file
}

// 删除文件
const deleteFile = async (fileId: string) => {
  try {
    deletingFiles.value.push(fileId)
    
    const response = await fetch(`/api/knowledge/delete/${fileId}`, {
      method: 'DELETE'
    })
    
    if (response.ok) {
      knowledgeFiles.value = knowledgeFiles.value.filter(f => f.id !== fileId)
      if (selectedFile.value?.id === fileId) {
        selectedFile.value = null
      }
      message.success('文件删除成功')
    } else {
      throw new Error('删除失败')
    }
  } catch (error) {
    message.error('文件删除失败')
    console.error('Delete error:', error)
  } finally {
    deletingFiles.value = deletingFiles.value.filter(id => id !== fileId)
  }
}

// 复制内容
const copyContent = async () => {
  if (selectedFile.value?.content) {
    try {
      await navigator.clipboard.writeText(selectedFile.value.content)
      message.success('内容已复制到剪贴板')
    } catch (error) {
      message.error('复制失败')
    }
  }
}

// 格式化文件大小
const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

// 格式化日期
const formatDate = (timestamp: number): string => {
  return new Date(timestamp).toLocaleString('zh-CN')
}

// 加载已有文件列表
const loadFileList = async () => {
  try {
    const response = await fetch('/api/knowledge/files')
    if (response.ok) {
      const files = await response.json()
      knowledgeFiles.value = files
    }
  } catch (error) {
    console.error('Load files error:', error)
  }
}

// 组件挂载时加载文件列表
onMounted(() => {
  loadFileList()
})
</script>

<style scoped>
.knowledge-base-modal {
  display: flex;
  flex-direction: column;
  gap: 24px;
  max-height: 70vh;
  overflow: hidden;
}

.section-title {
  font-size: 16px;
  font-weight: 600;
  color: #333;
  margin-bottom: 16px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.file-count {
  font-size: 14px;
  color: #666;
  font-weight: normal;
}

.file-title {
  font-size: 14px;
  color: #1890ff;
  font-weight: normal;
  background: rgba(24, 144, 255, 0.1);
  padding: 2px 8px;
  border-radius: 4px;
}

/* 上传区域样式 */
.upload-section {
  border-bottom: 1px solid #f0f0f0;
  padding-bottom: 24px;
}

.upload-dragger {
  border: 2px dashed #d9d9d9;
  border-radius: 8px;
  padding: 32px 20px;
  text-align: center;
  background: #fafafa;
  transition: border-color 0.3s;
  cursor: pointer;
}

.upload-dragger:hover:not(.disabled) {
  border-color: #1890ff;
}

.upload-dragger.disabled {
  cursor: not-allowed;
  opacity: 0.6;
}

.upload-icon {
  font-size: 48px;
  color: #999;
  margin-bottom: 8px;
}

.upload-text {
  font-size: 16px;
  color: #666;
  margin-bottom: 4px;
}

.upload-hint {
  font-size: 14px;
  color: #999;
}

.upload-progress {
  margin-top: 16px;
}

.progress-text {
  margin-left: 8px;
  font-size: 14px;
  color: #666;
}

/* 文件列表样式 */
.file-list-section {
  max-height: 300px;
  overflow-y: auto;
  border-bottom: 1px solid #f0f0f0;
  padding-bottom: 24px;
}

.file-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.file-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  border: 1px solid #f0f0f0;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s;
}

.file-item:hover {
  border-color: #1890ff;
  box-shadow: 0 2px 8px rgba(24, 144, 255, 0.1);
}

.file-item.active {
  border-color: #1890ff;
  background: rgba(24, 144, 255, 0.05);
}

.file-info {
  display: flex;
  align-items: center;
  gap: 12px;
  flex: 1;
}

.file-icon {
  font-size: 24px;
  color: #1890ff;
}

.file-details {
  flex: 1;
}

.file-name {
  font-weight: 500;
  color: #333;
  margin-bottom: 4px;
}

.file-meta {
  display: flex;
  gap: 12px;
  font-size: 12px;
  color: #999;
}

.file-status {
  margin-top: 4px;
  font-size: 12px;
}

.status-processing {
  color: #1890ff;
}

.status-completed {
  color: #52c41a;
}

.status-failed {
  color: #ff4d4f;
}

.file-actions {
  display: flex;
  gap: 8px;
}

/* 文件内容样式 */
.file-content-section {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.content-area {
  flex: 1;
  border: 1px solid #f0f0f0;
  border-radius: 8px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.content-loading,
.content-error {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px;
  color: #666;
}

.content-error {
  color: #ff4d4f;
}

.error-detail {
  font-size: 12px;
  color: #999;
  margin-top: 8px;
}

.content-display {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.image-content {
  padding: 20px;
  text-align: center;
}

.image-content img {
  max-width: 100%;
  max-height: 400px;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.text-content {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.content-toolbar {
  padding: 8px 16px;
  border-bottom: 1px solid #f0f0f0;
  background: #fafafa;
}

.content-text {
  flex: 1;
  padding: 16px;
  margin: 0;
  font-family: 'Consolas', 'Monaco', monospace;
  font-size: 13px;
  line-height: 1.6;
  color: #333;
  background: #fff;
  overflow: auto;
  white-space: pre-wrap;
  word-break: break-word;
}

/* 滚动条样式 */
.file-list-section::-webkit-scrollbar,
.content-text::-webkit-scrollbar {
  width: 6px;
}

.file-list-section::-webkit-scrollbar-track,
.content-text::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 3px;
}

.file-list-section::-webkit-scrollbar-thumb,
.content-text::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 3px;
}

.file-list-section::-webkit-scrollbar-thumb:hover,
.content-text::-webkit-scrollbar-thumb:hover {
  background: #a8a8a8;
}
</style> 