<template>
  <div class="llm-settings">
    <div class="llm-settings-header">
      <div class="header-title">
        <CloudOutlined class="header-icon" />
        <span>LLM 设置</span>
      </div>
    </div>

    <div class="llm-settings-content">
      <!-- 加载状态 -->
      <div v-if="loading" class="loading">
        <span>加载配置中...</span>
      </div>

      <template v-else>
      <!-- Provider -->
      <div class="setting-section">
        <div class="section-label">模型供应商</div>
        <div class="provider-tabs">
          <div
            v-for="p in providers"
            :key="p.id"
            :class="['provider-tab', { active: form.provider === p.id }]"
            @click="form.provider = p.id; onProviderChange()"
          >
            <component :is="p.icon" class="provider-icon" />
            <span>{{ p.name }}</span>
          </div>
        </div>
      </div>

      <!-- 连接配置 -->
      <div class="setting-section">
        <div class="section-label">连接配置</div>
        <div class="form-grid">
          <div class="form-item">
            <label>Base URL</label>
            <input
              v-model="form.baseUrl"
              type="text"
              :placeholder="defaultBaseUrl"
              @change="save"
            />
          </div>
          <div class="form-item">
            <label>API Key</label>
            <input
              v-model="form.apiKey"
              type="password"
              placeholder="sk-..."
              @change="save"
            />
          </div>
        </div>
      </div>

      <!-- 模型 -->
      <div class="setting-section">
        <div class="section-label">模型</div>
        <div class="form-item">
          <label>模型名称</label>
          <input
            v-model="form.model"
            type="text"
            :placeholder="defaultModel"
            @change="save"
          />
        </div>
        <div v-if="modelOptions.length" class="model-presets">
          <div
            v-for="m in modelOptions"
            :key="m"
            :class="['model-chip', { active: form.model === m }]"
            @click="form.model = m; save()"
          >
            {{ m }}
          </div>
        </div>
      </div>

      <!-- 测试连接 -->
      <div class="setting-section">
        <Button :loading="testing" type="primary" ghost @click="testConnection">
          <SendOutlined /> 测试连接
        </Button>
        <div v-if="testResult" :class="['test-result', testResult.ok ? 'ok' : 'error']">
          <CheckCircleFilled v-if="testResult.ok" />
          <CloseCircleFilled v-else />
          {{ testResult.msg }}
        </div>
      </div>
    </template>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue';
import { Button, message } from 'ant-design-vue';
import { SendOutlined, CheckCircleFilled, CloseCircleFilled, CloudOutlined } from '@ant-design/icons-vue';
import { CloudServerOutlined, AmazonOutlined } from '@ant-design/icons-vue';
import { getLLMConfig, updateLLMConfig } from '../utils/configApi';

const loading = ref(true);
const testing = ref(false);
const testResult = ref<{ ok: boolean; msg: string } | null>(null);

type Provider = 'openai' | 'anthropic' | 'openai_compatible';

const providers = [
  { id: 'openai' as Provider, name: 'OpenAI', icon: CloudServerOutlined, defaultBaseUrl: 'https://api.openai.com/v1', defaultModel: 'gpt-4o' },
  { id: 'anthropic' as Provider, name: 'Anthropic', icon: AmazonOutlined, defaultBaseUrl: 'https://api.anthropic.com/v1', defaultModel: 'claude-sonnet-4-20250514' },
  { id: 'openai_compatible' as Provider, name: 'OpenAI 兼容', icon: CloudServerOutlined, defaultBaseUrl: 'http://localhost:11434/v1', defaultModel: 'qwen2.5' },
];

const currentProvider = computed(() => providers.find(p => p.id === form.provider) || providers[2]);
const defaultBaseUrl = computed(() => form.baseUrl || currentProvider.value.defaultBaseUrl);
const defaultModel = computed(() => currentProvider.value.defaultModel);

const modelOptions = computed(() => {
  switch (form.provider) {
    case 'openai':
      return ['gpt-4o', 'gpt-4o-mini', 'gpt-4-turbo', 'gpt-3.5-turbo'];
    case 'anthropic':
      return ['claude-sonnet-4-20250514', 'claude-3-5-sonnet-20241022', 'claude-3-5-haiku-20241022', 'claude-opus-4-20250514'];
    case 'openai_compatible':
      return ['qwen2.5', 'qwen2', 'llama3', 'llama3.1', 'mistral', 'deepseek-v3', 'deepseek-chat'];
    default:
      return [];
  }
});

const form = reactive({
  provider: 'openai_compatible' as Provider,
  baseUrl: '',
  apiKey: '',
  model: '',
});

// 加载配置
onMounted(async () => {
  try {
    const config = await getLLMConfig();
    form.provider = (config.provider as Provider) || 'openai_compatible';
    form.baseUrl = config.base_url || '';
    form.apiKey = config.api_key || '';
    form.model = config.model || defaultModel.value;
  } catch (e) {
    console.error('Failed to load LLM config:', e);
    message.error('加载配置失败');
  } finally {
    loading.value = false;
  }
});

// Provider 变化时更新默认值
const onProviderChange = () => {
  if (!form.baseUrl) {
    form.baseUrl = currentProvider.value.defaultBaseUrl;
  }
  if (!form.model) {
    form.model = currentProvider.value.defaultModel;
  }
  save();
};

// 保存配置到后端
const save = async () => {
  try {
    await updateLLMConfig({
      provider: form.provider,
      api_key: form.apiKey,
      model: form.model || defaultModel.value,
      base_url: form.baseUrl || defaultBaseUrl.value,
    });
  } catch (e) {
    console.error('Failed to save LLM config:', e);
    message.error('保存配置失败');
  }
};

// 测试连接
const testConnection = async () => {
  testing.value = true;
  testResult.value = null;
  try {
    const resp = await fetch(`${form.baseUrl || defaultBaseUrl.value}/models`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${form.apiKey}`,
      },
    });
    if (resp.ok) {
      testResult.value = { ok: true, msg: '连接成功' };
    } else {
      const error = await resp.text();
      testResult.value = { ok: false, msg: `连接失败 (${resp.status})` };
    }
  } catch (e: any) {
    testResult.value = { ok: false, msg: `连接失败: ${e.message}` };
  } finally {
    testing.value = false;
  }
};
</script>

<style scoped>
.llm-settings {
  display: flex;
  flex-direction: column;
  height: 100%;
  padding: var(--space-md);
  gap: var(--space-md);
}

.llm-settings-header {
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

.llm-settings-content {
  flex: 1;
  overflow-y: auto;
  background: rgba(255, 255, 255, 0.7);
  backdrop-filter: blur(12px);
  border: 1px solid var(--glass-border);
  border-radius: var(--radius-lg);
  padding: var(--space-md);
  display: flex;
  flex-direction: column;
  gap: var(--space-lg);
}

.loading {
  text-align: center;
  padding: var(--space-xl);
  color: var(--text-secondary);
}

.setting-section {
  background: rgba(255, 255, 255, 0.6);
  border: 1px solid var(--glass-border);
  border-radius: var(--radius-md);
  padding: var(--space-md);
}

.section-label {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-secondary);
  margin-bottom: var(--space-sm);
  display: flex;
  align-items: center;
  gap: var(--space-sm);
}

/* Provider tabs */
.provider-tabs {
  display: flex;
  gap: var(--space-sm);
}

.provider-tab {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  border: 1.5px solid var(--glass-border);
  border-radius: var(--radius-md);
  cursor: pointer;
  font-size: 13px;
  font-weight: 500;
  color: var(--text-secondary);
  transition: all 0.2s ease;
  background: rgba(255,255,255,0.6);
}

.provider-tab:hover {
  border-color: var(--color-primary);
  color: var(--color-primary);
}

.provider-tab.active {
  border-color: var(--color-primary);
  background: rgba(99, 102, 241, 0.08);
  color: var(--color-primary);
}

.provider-icon {
  font-size: 16px;
}

/* Form */
.form-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--space-md);
  margin-bottom: var(--space-sm);
}

.form-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.form-item label {
  font-size: 12px;
  font-weight: 500;
  color: var(--text-secondary);
}

.form-item input {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid rgba(0, 0, 0, 0.10);
  border-radius: var(--radius-sm);
  font-size: 13px;
  color: var(--text-primary);
  background: rgba(255, 255, 255, 0.9);
  outline: none;
  transition: border-color 0.2s;
  box-sizing: border-box;
}

.form-item input:focus {
  border-color: var(--color-primary);
  box-shadow: 0 0 0 2px rgba(99, 102, 241, 0.12);
}

.form-item:last-child {
  margin-bottom: 0;
}

.model-presets {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: var(--space-sm);
}

.model-chip {
  padding: 4px 12px;
  border: 1px solid var(--glass-border);
  border-radius: 20px;
  font-size: 12px;
  cursor: pointer;
  color: var(--text-secondary);
  transition: all 0.2s ease;
  background: rgba(255,255,255,0.7);
}

.model-chip:hover {
  border-color: var(--color-primary);
  color: var(--color-primary);
}

.model-chip.active {
  border-color: var(--color-primary);
  background: var(--color-primary);
  color: #fff;
}

/* Test result */
.test-result {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-top: var(--space-sm);
  font-size: 13px;
  font-weight: 500;
}

.test-result.ok {
  color: #52c41a;
}

.test-result.error {
  color: #ff4d4f;
}
</style>
