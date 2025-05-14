<template>
    <div class="settings-section">
        <div class="setting-item">
            <label>服务器地址：</label>
            <input v-model="settings.serverUrl" type="text" @change="updateSettings">
        </div>
        <div class="setting-item">
            <label>背景图片：</label>
            <div class="setting-control">
                <input v-model="settings.backgroundPath" type="text" @change="updateSettings">
                <button class="reset-button" @click="">重置</button>
            </div>
        </div>
        <!-- 助手设置 -->
        <div class="setting-item">
            <label>助手名称：</label>
            <input v-model="settings.assistantSettings.assistantName" type="text" @change="updateSettings">
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
            <el-input type="textarea" class="system-prompt-textarea" v-model="settings.assistantSettings.sysPrompt"
                placeholder="请输入系统提示词" @change="updateSettings">
            </el-input>
        </div>
    </div>
</template>

<script setup lang="ts">
import { ElSwitch } from 'element-plus'
import { QuestionFilled } from '@element-plus/icons-vue'
import 'element-plus/dist/index.css'
import { PropType, ref } from 'vue';
import { SystemSettings } from '../models/message.vue';

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
const updateSettings = () => {
    props.onChange(settings.value)
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

.setting-control {
    display: flex;
    gap: 10px;
    align-items: center;
}

label {
    display: block;
    margin-bottom: 8px;
    color: #555;
}

input[type="text"] {
    width: 100%;
    padding: 8px;
    border: 1px solid #ddd;
    border-radius: 4px;
    font-size: 14px;
}

.reset-button {
    padding: 4px 8px;
    background: #ff4d4f;
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    font-size: 12px;
    white-space: nowrap;
}

.reset-button:hover {
    background: #ff7875;
}
</style>
