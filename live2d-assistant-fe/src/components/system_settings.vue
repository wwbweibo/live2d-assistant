<template>
  <div class="system-settings">
    <div class="system-settings-header">
      <div class="header-title">
        <SettingOutlined class="header-icon" />
        <span>系统设置</span>
      </div>
    </div>
    <div class="system-settings-content">
      <Collapse v-model:activeKey="collapseActiveKey">
        <CollapsePanel header="Live2D 设置" key="live2d">
                <div class="setting-item">
                    <label>背景图片</label>
                    <div class="setting-control">
                        <input v-model="settings.backgroundPath" type="text" @change="updateSettings">
                        <button class="reset-button" @click="">重置</button>
                    </div>
                </div>
                <div class="setting-item">
                    <label>Live2D 模型</label>
                    <div class="setting-control">
                        <input v-model="settings.live2DSettings.modelPath" type="text" @change="updateSettings">
                        <button class="reset-button" @click="">重置</button>
                    </div>
                </div>
                <div class="setting-item">
                    <label>模型横向偏移</label>
                    <Slider v-model:value="settings.live2DSettings.offsetX" @change="updateSettings" :min="-100"
                        :max="100" :step="1" />
                </div>
                <div class="setting-item">
                    <label>模型纵向偏移</label>
                    <Slider v-model:value="settings.live2DSettings.offsetY" @change="updateSettings" :min="-100"
                        :max="100" :step="1" />
                </div>
                <div class="setting-item">
                    <label>模型缩放</label>
                    <Slider v-model:value="settings.live2DSettings.scale" @change="updateSettings" :min="0.1" :max="1"
                        :step="0.1" />
                </div>
                <div class="setting-item">
                    <label>主题颜色</label>
                    <div class="setting-control">
                        <ColorPicker v-model:pureColor="settings.live2DSettings.themeColor" @pureColorChange="updateSettings"/>
                    </div>
                </div>
        </CollapsePanel>
      </Collapse>
    </div>
  </div>
</template>

<script setup lang="ts">
import { PropType, ref } from 'vue';
import { SystemSettings } from '../types/message';
import { Collapse, CollapsePanel, Slider } from 'ant-design-vue';
import { SettingOutlined } from '@ant-design/icons-vue';
import { ColorPicker } from "vue3-colorpicker";
import "vue3-colorpicker/style.css";

const props = defineProps({
    systemSettings: {
        type: Object as PropType<SystemSettings>,
        required: true
    },
    onChange: {
        type: Function,
        required: true
    }
})

const settings = ref<SystemSettings>(props.systemSettings)
const collapseActiveKey = ref<string[]>(['basic'])

const updateSettings = () => {
    props.onChange(settings.value)
}
</script>

<style scoped>
/* ─── 整体布局 ────────────────────────────────── */
.system-settings {
  display: flex;
  flex-direction: column;
  height: 100%;
  padding: var(--space-md);
  gap: var(--space-md);
}

.system-settings-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--space-sm) var(--space-md);
  background: rgba(255, 255, 255, 0.92);
  backdrop-filter: blur(var(--blur-amount)) saturate(180%);
  border: 1px solid var(--glass-border);
  border-radius: var(--radius-lg);
  box-shadow: var(--glass-shadow-sm);
}

.header-title {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
}

.header-icon {
  font-size: 20px;
  color: var(--color-primary);
}

.system-settings-content {
  flex: 1;
  overflow-y: auto;
  background: rgba(255, 255, 255, 0.7);
  backdrop-filter: blur(12px);
  border: 1px solid var(--glass-border);
  border-radius: var(--radius-lg);
  padding: var(--space-md);
}

/* ─── 设置项 ─────────────────────────────────────── */
.setting-item {
  margin-bottom: var(--space-lg);
}
.setting-item:last-child {
  margin-bottom: 0;
}

.setting-item label {
  display: block;
  margin-bottom: var(--space-sm);
  color: var(--text-secondary);
  font-weight: 500;
  font-size: 13px;
}

/* ─── 输入框 ─────────────────────────────────────── */
.setting-item input[type="text"],
.setting-item select {
  width: 100%;
  padding: var(--space-sm) var(--space-md);
  border: 1px solid rgba(0, 0, 0, 0.10);
  border-radius: var(--radius-sm);
  font-family: var(--font-sans);
  font-size: 14px;
  color: var(--text-primary);
  background: rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
  transition: all var(--duration-fast) var(--ease-out);
  outline: none;
  appearance: none;
}
.setting-item input[type="text"]:hover,
.setting-item select:hover {
  border-color: var(--color-primary);
  box-shadow: 0 0 0 2px rgba(var(--color-primary-rgb), 0.08);
}
.setting-item input[type="text"]:focus,
.setting-item select:focus {
  border-color: var(--color-primary);
  box-shadow: 0 0 0 3px rgba(var(--color-primary-rgb), 0.15);
  background: rgba(255, 255, 255, 0.98);
}

/* Select with arrow */
.setting-item select {
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 24 24' fill='none' stroke='%236b7280' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M6 9l6 6 6-6'/%3E%3C/svg%3E");
  background-repeat: no-repeat;
  background-position: right var(--space-md) center;
  padding-right: 36px;
  cursor: pointer;
}

/* ─── 控件行（input + button） ─────────────────── */
.setting-control {
  display: flex;
  gap: var(--space-sm);
  align-items: center;
}
.setting-control input[type="text"] {
  flex: 1;
}

/* ─── 重置按钮 ──────────────────────────────────── */
.reset-button {
  padding: 6px var(--space-md);
  background: transparent;
  color: var(--color-danger);
  border: 1.5px solid var(--color-danger);
  border-radius: var(--radius-sm);
  cursor: pointer;
  font-size: 13px;
  font-weight: 500;
  white-space: nowrap;
  transition: all var(--duration-fast) var(--ease-out);
  flex-shrink: 0;
}
.reset-button:hover {
  background: var(--color-danger);
  color: #fff;
  box-shadow: 0 4px 12px rgba(248, 113, 113, 0.35);
}
.reset-button:active {
  transform: scale(0.97);
}
</style>
