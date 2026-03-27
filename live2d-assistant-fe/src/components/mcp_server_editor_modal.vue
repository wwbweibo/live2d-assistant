<template>
  <Modal
    :open="open"
    :title="isEdit ? '编辑 MCP Server' : '新建 MCP Server'"
    :width="640"
    @cancel="$emit('update:open', false)"
    @ok="handleSave"
    :confirmLoading="saving"
    ok-text="保存"
    cancel-text="取消"
  >
    <div class="mcp-editor">
      <!-- 基础信息 -->
      <div class="editor-section">
        <div class="section-title">基础信息</div>
        <div class="form-row">
          <div class="form-item">
            <label>名称 <span class="required">*</span></label>
            <Input
              v-model:value="form.name"
              placeholder="例如：filesystem"
              :status="errors.name ? 'error' : undefined"
              @change="() => (errors.name = '')"
            />
            <div v-if="errors.name" class="error-msg">{{ errors.name }}</div>
          </div>
          <div class="form-item">
            <label>传输方式 <span class="required">*</span></label>
            <Select
              v-model:value="form.transport"
              :options="transportOptions"
              placeholder="选择传输方式"
              :status="errors.transport ? 'error' : undefined"
              @change="() => (errors.transport = '')"
            />
            <div v-if="errors.transport" class="error-msg">{{ errors.transport }}</div>
          </div>
        </div>
      </div>

      <!-- stdio 配置 -->
      <div v-if="form.transport === 'stdio'" class="editor-section">
        <div class="section-title">stdio 配置</div>
        <div class="form-item">
          <label>命令 <span class="required">*</span></label>
          <Input
            v-model:value="form.command"
            placeholder="例如：npx, uvx, python"
          />
        </div>
        <div class="form-item">
          <label>参数</label>
          <Input
            v-model:value="argsText"
            placeholder="空格分隔，例如：-m mcp_server --port 3000"
          />
          <div class="form-hint">多个参数用空格分隔</div>
        </div>
        <div class="form-item">
          <label>工作目录</label>
          <Input v-model:value="form.cwd" placeholder="可选，命令执行的工作目录" />
        </div>
        <div class="form-item">
          <label>环境变量</label>
          <Textarea
            v-model:value="envText"
            placeholder="KEY=VALUE 格式，每行一个"
            :rows="3"
          />
          <div class="form-hint">每行一个，格式：KEY=VALUE</div>
        </div>
      </div>

      <!-- sse/streamable-http 配置 -->
      <div v-if="form.transport === 'sse' || form.transport === 'streamable-http'" class="editor-section">
        <div class="section-title">远程配置</div>
        <div class="form-item">
          <label>URL <span class="required">*</span></label>
          <Input
            v-model:value="form.url"
            placeholder="例如：http://localhost:3000/sse"
          />
        </div>
        <div class="form-item">
          <label>认证 Token</label>
          <Input v-model:value="form.auth" placeholder="可选，Bearer Token" />
        </div>
        <div class="form-item">
          <label>自定义 Headers</label>
          <Textarea
            v-model:value="headersText"
            placeholder="KEY: VALUE 格式，每行一个"
            :rows="3"
          />
          <div class="form-hint">每行一个，格式：KEY: VALUE</div>
        </div>
      </div>
    </div>
  </Modal>
</template>

<script setup lang="ts">
import { ref, reactive, computed, watch } from 'vue';
import { Modal, Input, Select } from 'ant-design-vue';
import { Textarea } from 'ant-design-vue';
import type { MCPServerConfig } from '../types/message';

const props = defineProps<{
  open: boolean;
  server: MCPServerConfig | null;
}>();

const emit = defineEmits<{
  (e: 'update:open', v: boolean): void;
  (e: 'save', server: MCPServerConfig): void;
}>();

const saving = ref(false);
const errors = reactive({ name: '', transport: '' });

const transportOptions = [
  { label: 'stdio', value: 'stdio' },
  { label: 'SSE', value: 'sse' },
  { label: 'Streamable HTTP', value: 'streamable-http' },
];

const isEdit = computed(() => !!props.server);

const form = reactive({
  name: '',
  transport: 'stdio',
  command: '',
  cwd: '',
  url: '',
  auth: '',
});

// 辅助文本字段
const argsText = ref('');
const envText = ref('');
const headersText = ref('');

watch(
  () => props.open,
  (v) => {
    if (v) {
      errors.name = '';
      errors.transport = '';
      if (props.server) {
        Object.assign(form, {
          name: props.server.name,
          transport: props.server.transport,
          command: props.server.command || '',
          cwd: props.server.cwd || '',
          url: props.server.url || '',
          auth: props.server.auth || '',
        });
        argsText.value = (props.server.args || []).join(' ');
        envText.value = Object.entries(props.server.env || {}).map(([k, v]) => `${k}=${v}`).join('\n');
        headersText.value = Object.entries(props.server.headers || {}).map(([k, v]) => `${k}: ${v}`).join('\n');
      } else {
        Object.assign(form, { name: '', transport: 'stdio', command: '', cwd: '', url: '', auth: '' });
        argsText.value = '';
        envText.value = '';
        headersText.value = '';
      }
    }
  }
);

const parseEnv = (text: string): Record<string, string> | undefined => {
  if (!text.trim()) return undefined;
  const env: Record<string, string> = {};
  for (const line of text.split('\n')) {
    const idx = line.indexOf('=');
    if (idx > 0) {
      env[line.slice(0, idx).trim()] = line.slice(idx + 1).trim();
    }
  }
  return Object.keys(env).length > 0 ? env : undefined;
};

const parseHeaders = (text: string): Record<string, string> | undefined => {
  if (!text.trim()) return undefined;
  const headers: Record<string, string> = {};
  for (const line of text.split('\n')) {
    const idx = line.indexOf(':');
    if (idx > 0) {
      headers[line.slice(0, idx).trim()] = line.slice(idx + 1).trim();
    }
  }
  return Object.keys(headers).length > 0 ? headers : undefined;
};

const handleSave = () => {
  errors.name = '';
  errors.transport = '';
  if (!form.name.trim()) { errors.name = '名称不能为空'; return; }
  if (!form.transport) { errors.transport = '请选择传输方式'; return; }

  const config: MCPServerConfig = {
    name: form.name.trim(),
    transport: form.transport,
  };

  if (form.transport === 'stdio') {
    if (form.command.trim()) config.command = form.command.trim();
    const args = argsText.value.trim().split(/\s+/).filter(Boolean);
    if (args.length > 0) config.args = args;
    if (form.cwd.trim()) config.cwd = form.cwd.trim();
    const env = parseEnv(envText.value);
    if (env) config.env = env;
  } else {
    if (form.url.trim()) config.url = form.url.trim();
    if (form.auth.trim()) config.auth = form.auth.trim();
    const headers = parseHeaders(headersText.value);
    if (headers) config.headers = headers;
  }

  emit('save', config);
  saving.value = true;
  setTimeout(() => { saving.value = false; }, 200);
};
</script>

<style scoped>
.mcp-editor {
  display: flex;
  flex-direction: column;
  gap: var(--space-md);
}

.editor-section {
  border: 1px solid var(--glass-border);
  border-radius: var(--radius-md);
  padding: var(--space-md);
  background: rgba(255, 255, 255, 0.5);
}

.section-title {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-secondary);
  margin-bottom: var(--space-sm);
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--space-md);
  margin-bottom: var(--space-md);
}

.form-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
  margin-bottom: var(--space-md);
}

.form-item:last-child {
  margin-bottom: 0;
}

.form-item label {
  font-size: 13px;
  font-weight: 500;
  color: var(--text-secondary);
}

.required {
  color: #ef4444;
}

.error-msg {
  font-size: 12px;
  color: #ef4444;
}

.form-hint {
  font-size: 12px;
  color: var(--text-tertiary);
  margin-top: 2px;
}
</style>
