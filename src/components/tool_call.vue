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
  border-radius: 12px;
  /* box-shadow: 0 2px 12px rgba(0,0,0,0.08); */
  padding: 20px 24px;
  margin: 16px 0;
  max-width: 600px;
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.tool-call-header {
  display: flex;
  align-items: center;
  margin-bottom: 8px;
}

.tool-call-icon {
  background: #f5f7fa;
  border-radius: 50%;
  width: 44px;
  height: 44px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 28px;
  color: #1890ff;
  margin-right: 12px;
}

.tool-call-title {
  font-size: 20px;
  font-weight: bold;
  color: #222;
}

.tool-call-section {
  display: flex;
  align-items: flex-start;
  margin-bottom: 4px;
}

.tool-call-label {
  font-weight: bold;
  color: #666;
  min-width: 56px;
}

.tool-call-func {
  font-family: 'Fira Mono', 'Consolas', monospace;
  color: #333;
  font-size: 16px;
  margin-left: 4px;
}

.tool-call-args, .tool-call-response {
  background: #f6f8fa;
  border-radius: 6px;
  padding: 8px 12px;
  font-family: 'Fira Mono', 'Consolas', monospace;
  font-size: 14px;
  color: #444;
  margin: 0 0 0 4px;
  white-space: pre-wrap;
  word-break: break-all;
  flex: 1;
  max-width: 100%;
  overflow-x: auto;
}
.collapse-toggle {
  cursor: pointer;
  color: #1890ff;
  margin-left: 8px;
  font-size: 13px;
  user-select: none;
}
</style>