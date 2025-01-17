<template>
  <div class="settings-container">
    <!-- 标题栏和标签页 -->
    <div class="settings-header">
      <h2>设置</h2>
      <div class="tab-container">
        <div 
          v-for="tab in tabs" 
          :key="tab.id"
          :class="['tab-item', { active: currentTab === tab.id }]"
          @click="currentTab = tab.id"
        >
          {{ tab.name }}
        </div>
      </div>
    </div>

    <!-- 设置内容区域 -->
    <div class="settings-content">
      <div v-show="currentTab === 'model'" class="tab-content">
        <ModelSettings 
          :modelSettings="modelSettings"
          :onChange="handleModelSettingsChange"
        />
      </div>

      <div v-show="currentTab === 'assistant'" class="tab-content">
        <AssistantSettings 
          :assistantSettings="assistantSettings"
          :onChange="handleAssistantSettingsChange"
        />
      </div>

      <div v-show="currentTab === 'background'" class="tab-content">
        <BackgroundSettings 
          :backgroundSettings="modelSettings"
          :onChange="handleModelSettingsChange"
        />
      </div>
    </div>
  </div>
</template>

<script>
import ModelSettings from './model_settings.vue'
import AssistantSettings from './assistant_settings.vue'
import BackgroundSettings from './background_settings.vue'

export default {
  name: 'SettingModal',
  components: {
    ModelSettings,
    AssistantSettings,
    BackgroundSettings
  },
  props: {
    modelSettings: {
      type: Object,
      required: true
    },
    assistantSettings: {
      type: Object,
      required: true
    }
  },
  emits: ['updateModelSettings', 'updateAssistantSettings'],
  data() {
    return {
      currentTab: 'model',
      tabs: [
        { id: 'model', name: '模型设置' },
        { id: 'assistant', name: '助手设置' },
        { id: 'background', name: '背景设置' }
      ]
    }
  },
  methods: {
    handleModelSettingsChange(settings) {
      this.$emit('updateModelSettings', settings)
    },
    handleAssistantSettingsChange(settings) {
      this.$emit('updateAssistantSettings', settings)
    }
  }
}
</script>

<style scoped>
.settings-container {
  height: 100%;
  display: flex;
  flex-direction: column;
  padding: 20px;
}

.settings-header {
  margin-bottom: 20px;
}

.settings-header h2 {
  margin: 0 0 15px 0;
  color: #333;
}

.tab-container {
  display: flex;
  gap: 2px;
  background: #eee;
  padding: 2px;
  border-radius: 6px;
}

.tab-item {
  flex: 1;
  padding: 8px 16px;
  text-align: center;
  cursor: pointer;
  border-radius: 4px;
  color: #666;
  transition: all 0.3s;
}

.tab-item:hover {
  background: rgba(255, 255, 255, 0.5);
}

.tab-item.active {
  background: white;
  color: #333;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.settings-content {
  flex: 1;
  overflow-y: auto;
  padding-right: 10px;
}

.tab-content {
  animation: fadeIn 0.3s ease-in-out;
}

/* 自定义滚动条样式 */
.settings-content::-webkit-scrollbar {
  width: 6px;
}

.settings-content::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 3px;
}

.settings-content::-webkit-scrollbar-thumb {
  background: #888;
  border-radius: 3px;
}

.settings-content::-webkit-scrollbar-thumb:hover {
  background: #555;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>