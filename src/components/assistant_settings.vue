<template>
  <div class="settings-section">
    <div class="setting-item">
      <label>助手名称：</label>
      <input 
        v-model="settings.name" 
        type="text" 
        @change="updateSettings"
      >
    </div>

    <div class="setting-item">
      <label>AI模型：</label>
      <select 
        v-model="settings.model" 
        @change="updateSettings"
      >
        <option value="qwen2.5">通义千问2.5</option>
        <option value="llama2">Llama2</option>
        <option value="gemma">Gemma</option>
      </select>
    </div>

    <div class="setting-item">
      <label>Ollama地址：</label>
      <input 
        v-model="settings.ollamaHost" 
        type="text" 
        @change="updateSettings"
      >
    </div>
  </div>
</template>

<script>
export default {
  name: 'AssistantSettings',
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
      settings: { ...this.assistantSettings }
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
  padding: 20px;
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
</style> 