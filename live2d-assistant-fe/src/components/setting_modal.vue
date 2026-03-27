<template>
  <!-- 标签页 -->
  <div class="tab-container">
    <div
      v-for="tab in tabs"
      :key="tab.id"
      :class="['tab-item', { active: currentTab === tab.id }]"
      @click="currentTab = tab.id"
    >
      <component :is="tab.icon" class="tab-icon" />
      <span>{{ tab.name }}</span>
    </div>
  </div>
  <!-- 设置内容区域 -->
  <div class="settings-content">
    <div v-show="currentTab === 'system'" class="tab-pane">
      <SystemSettings :systemSettings="settings" :onChange="handleSystemSettingsChange" />
    </div>
    <div v-show="currentTab === 'llm'" class="tab-pane">
      <LLMSettings :settings="settings" :onChange="handleLLMSettingsChange" />
    </div>
    <div v-show="currentTab === 'agents'" class="tab-pane">
      <AgentOrchestration :settings="settings" @update="onAgentsUpdate" />
    </div>
    <div v-show="currentTab === 'skills'" class="tab-pane">
      <SkillOrchestration />
    </div>
    <div v-show="currentTab === 'mcp'" class="tab-pane">
      <McpServerOrchestration />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { SettingOutlined, RobotOutlined, CloudOutlined, ThunderboltOutlined, ApiOutlined } from '@ant-design/icons-vue'
import type { SystemSettings as SystemSettingsType } from '../types/message'
import SystemSettings from './system_settings.vue'
import AgentOrchestration from './agent_orchestration.vue'
import SkillOrchestration from './skill_orchestration.vue'
import McpServerOrchestration from './mcp_server_orchestration.vue'
import LLMSettings from './llm_settings.vue'

const props = defineProps<{
  settings: SystemSettingsType
  updateSettings: (settings: SystemSettingsType) => void
  onAgentsUpdate: (agents: any[]) => void
}>()

const currentTab = ref('system')

const tabs = [
  { id: 'system',  name: '系统设置',  icon: SettingOutlined },
  { id: 'llm',     name: 'LLM 设置',  icon: CloudOutlined   },
  { id: 'agents',  name: 'Agent 编排', icon: RobotOutlined  },
  { id: 'skills',  name: '技能管理',  icon: ThunderboltOutlined },
  { id: 'mcp',     name: 'MCP 服务',  icon: ApiOutlined },
]

const handleSystemSettingsChange = (s: SystemSettingsType) => {
  props.updateSettings(s)
}

const handleLLMSettingsChange = (s: SystemSettingsType) => {
  props.updateSettings(s)
}
</script>

<style scoped>
.tab-container {
  display: flex;
  gap: var(--space-xs);
  background: rgba(99, 102, 241, 0.06);
  backdrop-filter: blur(12px) saturate(180%);
  -webkit-backdrop-filter: blur(12px) saturate(180%);
  padding: 4px;
  border-radius: var(--radius-full);
  margin-bottom: var(--space-lg);
  border: 1px solid rgba(99, 102, 241, 0.10);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  width: fit-content;
}

.tab-item {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px var(--space-md);
  border-radius: var(--radius-full);
  color: var(--text-secondary);
  cursor: pointer;
  transition: all var(--duration-fast) var(--ease-out);
  font-weight: 500;
  font-size: 13px;
  min-width: 80px;
  justify-content: center;
}

.tab-icon {
  font-size: 14px;
}

.tab-item:hover:not(.active) {
  color: var(--text-primary);
  background: rgba(255, 255, 255, 0.6);
}

.tab-item.active {
  background: #fff;
  color: var(--color-primary);
  box-shadow: 0 2px 12px rgba(99, 102, 241, 0.15), 0 0 0 1px rgba(var(--color-primary-rgb), 0.12);
  font-weight: 600;
}

.tab-pane {
  animation: fadeIn 0.2s var(--ease-out);
  max-height: 60vh;
  overflow-y: auto;
  padding-right: 4px;
}

.settings-content {
  padding: 0 var(--space-xs);
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(6px); }
  to   { opacity: 1; transform: translateY(0); }
}
</style>
