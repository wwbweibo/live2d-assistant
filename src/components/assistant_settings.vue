<template>
  <div class="settings-section">
    <div class="setting-item">
      <label>助手名称：</label>
      <input v-model="settings.name" type="text" @change="updateSettings">
    </div>

    <div class="setting-item">
      <label>AI模型：</label>
      <select v-model="settings.model" @change="updateSettings">
        <option v-for="item in models" :value="item">{{ item }}</option>
      </select>
    </div>

    <div class="setting-item">
      <label>Ollama地址：</label>
      <input v-model="settings.ollamaHost" type="text" @change="updateSettings">
    </div>
    <div class="setting-item">
      <div class="setting-header">
        <el-tooltip content="系统提示词，用于设置助手的默认行为和风格。" placement="top">
          <template #content>
            <div>系统提示词，用于设置助手的默认行为和风格。</div>
          </template>
          <el-icon>
            <question-filled />
          </el-icon>
        </el-tooltip>
        <label>系统提示词：</label>
      </div>
      <el-input type="textarea" rows="5" class="system-prompt-textarea" v-model="settings.systemPrompt"
        placeholder="请输入系统提示词" @change="updateSettings"></el-input>
    </div>
    <div class="setting-item">
      <label>是否启用TTS：</label>
      <el-switch v-model="settings.ttsEnabled" @change="updateSettings"></el-switch>
    </div>
  </div>
</template>

<script>
import { ElTooltip, ElInput, ElSwitch, ElIcon } from 'element-plus'
import { QuestionFilled } from '@element-plus/icons-vue'
import 'element-plus/dist/index.css'

export default {
  name: 'AssistantSettings',
  components: {
    ElTooltip,
    ElInput,
    ElSwitch,
    ElIcon,
    QuestionFilled
  },
  props: {
    assistantSettings: {
      type: Object,
      required: true
    },
    onChange: {
      type: Function,
      required: true
    }
  },
  data() {
    return {
      settings: { ...this.assistantSettings },
      models: [],
    }
  },
  methods: {
    updateSettings() {
      console.log(this.settings)
      this.onChange(this.settings)
    },
    getAvailableModels() {
      fetch(this.assistantSettings.ollamaHost + '/api/tags')
        .then(response => response.json())
        .then(data => {
          console.log(data['models'])
          data['models'].map(model => {
            this.models.push(model['name'])
          })
        })
        .catch(error => {
          console.error('Error fetching available models:', error)
        })
    }
  },
  mounted() {
    this.getAvailableModels()
  }
}
</script>

<style scoped>
.settings-section {
  background: #f8f9fa;
  border-radius: 8px;
}

.setting-item {
  margin-bottom: 15px;
}

label {
  display: block;
  margin-bottom: 8px;
  color: #555;
}

input[type="text"],
select {
  width: 100%;
  padding: 8px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
}

select {
  background-color: white;
  cursor: pointer;
}

select:hover {
  border-color: #40a9ff;
}

.system-prompt-textarea {
  width: 100%;
  height: 100px;
}

.setting-header {
  display: flex;
  align-items: center;
  margin-bottom: 8px;
}
</style>
