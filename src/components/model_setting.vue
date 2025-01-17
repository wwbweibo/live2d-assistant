<template>
    <h3>模型设置</h3>
    
    <div class="setting-item">
        <label>模型路径：</label>
        <input v-model="settings.modelPath" type="text" @change="updateModel">
    </div>

    <div class="setting-item">
        <div class="setting-header">
        <label>横向偏移：</label>
        <button class="reset-button" @click="resetOffset('x')">重置</button>
        </div>
        <div class="setting-control">
        <input 
            v-model="settings.offsetX" 
            type="range" 
            min="-100" 
            max="100" 
            @input="updatePosition"
        >
        <span>{{ settings.offsetX }}%</span>
        </div>
    </div>

    <div class="setting-item">
        <div class="setting-header">
        <label>纵向偏移：</label>
        <button class="reset-button" @click="resetOffset('y')">重置</button>
        </div>
        <div class="setting-control">
        <input 
            v-model="settings.offsetY" 
            type="range" 
            min="-100" 
            max="100" 
            @input="updatePosition"
        >
        <span>{{ settings.offsetY }}%</span>
        </div>
    </div>

    <div class="setting-item">
        <div class="setting-header">
        <label>缩放比例：</label>
        <button class="reset-button" @click="resetScale">重置</button>
        </div>
        <div class="setting-control">
        <input 
            v-model="settings.scale" 
            type="range" 
            min="0.1" 
            max="2" 
            step="0.1" 
            @input="updateScale"
        >
        <span>{{ settings.scale }}x</span>
        </div>
    </div>

    <div class="setting-item">
        <label>背景图片：</label>
        <div class="setting-control">
        <input 
            v-model="settings.backgroundPath" 
            type="text" 
            @change="updateBackground"
        >
        <button class="reset-button" @click="resetBackground">重置</button>
        </div>
    </div>
</template>

<script>
export default {
    name: 'ModelSetting',
    props: {
        onSettingsChange: {
            type: Function,
            required: true
        },
    },
    data() {
        return {
            settings: {
                modelPath: '',
                offsetX: 0,
                offsetY: 0,
                scale: 1,
                backgroundPath: ''
            },
            defaultSettings: {
                modelPath: '',
                offsetX: 0,
                offsetY: 0,
                scale: 1,
                backgroundPath: ''
            }
        }
    },
}
</script>

<style scoped>
.setting-item {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.setting-item label {
  font-size: 14px;
  color: #666;
}

.setting-item input {
  width: 100%;
  padding: 8px;
  border: 1px solid #ddd;
  border-radius: 4px;
}

.setting-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.setting-control {
  display: flex;
  gap: 10px;
  align-items: center;
}

.setting-control input[type="range"] {
  flex: 1;
}

.setting-control span {
  min-width: 45px;
  text-align: right;
}

.reset-button {
  padding: 4px 8px;
  font-size: 12px;
  background: #f0f0f0;
  border: 1px solid #ddd;
  border-radius: 4px;
  cursor: pointer;
  color: #666;
}

.reset-button:hover {
  background: #e0e0e0;
}
</style>