<template>
  <div class="settings-section">
    <div class="setting-item">
      <label>模型路径：</label>
      <input 
        v-model="settings.modelPath" 
        type="text" 
        @change="updateSettings"
      >
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
          @input="updateSettings"
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
          @input="updateSettings"
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
          @input="updateSettings"
        >
        <span>{{ settings.scale }}x</span>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'ModelSettings',
  props: {
    modelSettings: {
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
      settings: { ...this.modelSettings }
    }
  },
  methods: {
    updateSettings() {
      this.onChange(this.settings)
    },
    resetOffset(axis) {
      if (axis === 'x') {
        this.settings.offsetX = 0
      } else {
        this.settings.offsetY = 0
      }
      this.updateSettings()
    },
    resetScale() {
      this.settings.scale = 0.5
      this.updateSettings()
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

.setting-header {
  display: flex;
  justify-content: space-between;
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

input[type="range"] {
  flex: 1;
}

.reset-button {
  padding: 4px 8px;
  background: #ff4d4f;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
}

.reset-button:hover {
  background: #ff7875;
}
</style> 