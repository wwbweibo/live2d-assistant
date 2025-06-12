<template>
  <div class="tool-call-card">
    <div class="tool-call-header">
      <div class="tool-call-icon">
        <CodeOutlined />
      </div>
      <div class="tool-call-title">
        工具调用
      </div>
    </div>
    <div class="tool-call-section">
      <span class="tool-call-label">函数名：</span>
      <span class="tool-call-func">{{ function_name }}</span>
    </div>
    <div class="tool-call-section">
      <span class="tool-call-label">参数：</span>
      <span class="collapse-toggle" @click="showArgs = !showArgs">
        {{ showArgs ? '收起 ▲' : '展开 ▼' }}
      </span>
      <pre class="tool-call-args" v-if="showArgs">{{ formatArgs(function_args) }}</pre>
    </div>
    <div class="tool-call-section">
      <span class="tool-call-label">响应：</span>
      <span class="collapse-toggle" @click="showResponse = !showResponse">
        {{ showResponse ? '收起 ▲' : '展开 ▼' }}
      </span>
      <pre class="tool-call-response" v-if="showResponse">{{ response }}</pre>
    </div>
  </div>
</template>

<script setup lang="ts">
import { CodeOutlined } from '@ant-design/icons-vue';
import { ref } from 'vue';
const props = defineProps({
  function_name: {
    type: String,
    required: true
  },
  function_args: {
    type: Object,
    required: true
  },
  response: {
    type: String,
    required: true
  }
})

const showArgs = ref(false)
const showResponse = ref(false)
function formatArgs(args: object) {
//   try {
//     return JSON.stringify(args, null, 2)
//   } catch {
//     return String(args)
//   }
return args
}
</script>

<style scoped>
.tool-call-card {
  background: #fff;
  border-radius: 16px;
  padding: 22px 26px;
  margin: 20px 0;
  max-width: 600px;
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: 14px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.06);
  border: 1px solid rgba(0, 0, 0, 0.03);
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.tool-call-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(0, 0, 0, 0.08);
}

.tool-call-header {
  display: flex;
  align-items: center;
  margin-bottom: 10px;
}

.tool-call-icon {
  background: #f0f5ff;
  border-radius: 50%;
  width: 48px;
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  color: #1890ff;
  margin-right: 14px;
  box-shadow: 0 2px 8px rgba(24, 144, 255, 0.15);
}

.tool-call-title {
  font-size: 18px;
  font-weight: 600;
  color: #222;
  letter-spacing: 0.3px;
}

.tool-call-section {
  display: flex;
  align-items: flex-start;
  margin-bottom: 6px;
  flex-wrap: wrap;
}

.tool-call-label {
  font-weight: 600;
  color: #555;
  min-width: 60px;
  margin-right: 4px;
}

.tool-call-func {
  font-family: 'Fira Mono', 'Consolas', monospace;
  color: #1890ff;
  font-size: 15px;
  margin-left: 4px;
  padding: 2px 6px;
  background: rgba(24, 144, 255, 0.08);
  border-radius: 4px;
}

.tool-call-args, .tool-call-response {
  background: #f9fafc;
  border-radius: 8px;
  padding: 12px 16px;
  font-family: 'Fira Mono', 'Consolas', monospace;
  font-size: 14px;
  color: #333;
  margin: 8px 0 0;
  white-space: pre-wrap;
  word-break: break-all;
  flex: 1;
  max-width: 100%;
  overflow-x: auto;
  border: 1px solid #eaedf1;
  line-height: 1.5;
}

.collapse-toggle {
  cursor: pointer;
  color: #1890ff;
  margin-left: 10px;
  font-size: 13px;
  user-select: none;
  transition: opacity 0.2s ease;
  padding: 2px 6px;
  border-radius: 4px;
  background: rgba(24, 144, 255, 0.08);
}

.collapse-toggle:hover {
  opacity: 0.8;
  background: rgba(24, 144, 255, 0.15);
}
</style>