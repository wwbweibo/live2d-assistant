<template>
    <div class="settings-section">
        <div class="setting-item">
            <label>服务器地址：</label>
            <input v-model="settings.serverUrl" type="text" @change="updateSettings">
        </div>
        <div class="setting-item">
            <label>是否开启Debug：</label>
            <el-switch v-model="settings.debugEnabled" @change="updateSettings"></el-switch>
        </div>
        <div class="setting-item">
            <label>背景图片：</label>
            <div class="setting-control">
                <input v-model="settings.backgroundPath" type="text" @change="updateSettings">
                <button class="reset-button" @click="resetBackground">重置</button>
            </div>
        </div>
    </div>
</template>

<script>
import { ElSwitch } from 'element-plus'
import 'element-plus/dist/index.css'

export default {
    name: 'SystemSettings',
    components: {
        ElSwitch
    },
    props: {
        systemSettings: {
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
            settings: {
                serverUrl: this.systemSettings.serverUrl || 'http://localhost:8000',
                debugEnabled: this.systemSettings.debugEnabled || false
            }
        }
    },
    methods: {
        updateSettings() {
            this.onChange(this.settings)
        }
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
