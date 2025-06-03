<template>
    <!-- 标签页 -->
    <div class="tab-container">
      <div v-for="tab in tabs" :key="tab.id" :class="['tab-item', { active: currentTab === tab.id }]"
        @click="currentTab = tab.id">
        <a-tooltip :title="tab.tooltip">
          <div class="tab-content">
            {{ tab.name }}
          </div>
        </a-tooltip>
      </div>
    </div>
    <!-- 设置内容区域 -->
    <div class="settings-content">
      <div v-show="currentTab === 'system'" class="tab-content">
        <SystemSettings :systemSettings="settings" :onChange="handleSystemSettingsChange" />
      </div>
    </div>
</template>

<script setup lang="ts">
import { ref, defineProps, defineEmits } from 'vue'
import { Modal as AModal, Tooltip as ATooltip } from 'ant-design-vue'
import { SystemSettings as Settings } from '../types/message'
import SystemSettings from './system_settings.vue'
import { PropType } from 'vue'

const props = defineProps({
  settings: { type: Object as PropType<Settings>, required: true },
  updateSettings: { type: Function, required: true },
})
const emit = defineEmits(['update:visible'])

const currentTab = ref('system')
const tabs = [
  { id: 'system', name: '系统设置',  tooltip: '系统相关的基础设置' },
]

function handleSystemSettingsChange(settings) {
  props.updateSettings(settings)
}
function handleClose() {
  emit('update:visible', false)
}
</script>

<style scoped>
.tab-container {
  display: flex;
  gap: 2px;
  background: #f5f7fa;
  padding: 4px;
  border-radius: 10px;
  margin-bottom: 20px;
  box-shadow: inset 0 1px 3px rgba(0, 0, 0, 0.05);
}

.tab-item {
  flex: 1;
  padding: 10px 16px;
  text-align: center;
  cursor: pointer;
  border-radius: 8px;
  color: #666;
  transition: all 0.3s;
  font-weight: 500;
}

.tab-item:hover:not(.active) {
  background: rgba(255, 255, 255, 0.8);
  color: #444;
}

.tab-item.active {
  background: white;
  color: #1890ff;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  font-weight: 600;
}

.tab-content {
  animation: fadeIn 0.3s ease-in-out;
  padding: 0 4px;
}

.settings-content {
  padding: 0 10px;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px);}
  to { opacity: 1; transform: translateY(0);}
}
</style>