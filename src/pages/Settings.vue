<template>
  <div class="settings">
    <h2>模型设置</h2>
    
    <div class="setting-section">
      <h3>大小设置</h3>
      <div class="setting-item">
        <label>缩放比例：</label>
        <input 
          type="range" 
          v-model="scale" 
          min="0.5" 
          max="2" 
          step="0.1"
          @change="updateSettings"
        >
        <span>{{ scale }}x</span>
      </div>
    </div>

    <div class="setting-section">
      <h3>位置设置</h3>
      <div class="setting-item">
        <label>水平位置：</label>
        <select v-model="position.horizontal" @change="updateSettings">
          <option value="left">左侧</option>
          <option value="center">居中</option>
          <option value="right">右侧</option>
        </select>
      </div>
      <div class="setting-item">
        <label>垂直位置：</label>
        <select v-model="position.vertical" @change="updateSettings">
          <option value="top">顶部</option>
          <option value="middle">中间</option>
          <option value="bottom">底部</option>
        </select>
      </div>
    </div>

    <div class="setting-section">
      <h3>模型路径设置</h3>
      <div class="setting-item">
        <label>模型目录：</label>
        <input 
          type="text" 
          v-model="modelPath" 
          placeholder="/models/live2d/"
          @change="updateSettings"
        >
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

const scale = ref(1)
const position = ref({
  horizontal: 'right',
  vertical: 'bottom'
})
const modelPath = ref('/models/live2d/')

const updateSettings = () => {
  // 保存设置到 localStorage
  const settings = {
    scale: scale.value,
    position: position.value,
    modelPath: modelPath.value
  }
  localStorage.setItem('live2dSettings', JSON.stringify(settings))
}

// 初始化时加载保存的设置
const loadSettings = () => {
  const savedSettings = localStorage.getItem('live2dSettings')
  if (savedSettings) {
    const settings = JSON.parse(savedSettings)
    scale.value = settings.scale
    position.value = settings.position
    modelPath.value = settings.modelPath
  }
}

loadSettings()
</script>

<style scoped>
.settings {
  max-width: 800px;
  margin: 0 auto;
  padding: 20px;
}

.setting-section {
  margin-bottom: 30px;
  padding: 20px;
  border: 1px solid #eee;
  border-radius: 8px;
}

.setting-item {
  margin: 15px 0;
  display: flex;
  align-items: center;
  gap: 10px;
}

label {
  min-width: 100px;
}

input[type="range"] {
  flex: 1;
  max-width: 200px;
}

input[type="text"] {
  flex: 1;
  padding: 5px;
  border: 1px solid #ddd;
  border-radius: 4px;
}

select {
  padding: 5px;
  border: 1px solid #ddd;
  border-radius: 4px;
}
</style> 