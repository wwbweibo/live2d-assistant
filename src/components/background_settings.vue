<template>
  <div class="settings-section">
    <div class="setting-item">
      <label>背景图片：</label>
      <div class="setting-control">
        <input 
          v-model="settings.backgroundPath" 
          type="text" 
          @change="updateSettings"
        >
        <button class="reset-button" @click="resetBackground">重置</button>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'BackgroundSettings',
  props: {
    backgroundSettings: {
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
      settings: { ...this.backgroundSettings }
    }
  },
  methods: {
    updateSettings() {
      this.onChange(this.settings)
    },
    resetBackground() {
      this.settings.backgroundPath = 'assets/background.jpg'
      this.updateSettings()
    }
  }
}
</script>

<style scoped>
.settings-section {
  background: #f8f9fa;
  border-radius: 8px;
  padding: 20px;
}

.setting-item {
  margin-bottom: 15px;
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