<template>
  <Modal
    :open="open"
    :title="isEdit ? '编辑 Agent' : '新建 Agent'"
    :width="640"
    @cancel="$emit('update:open', false)"
    @ok="handleSave"
    :confirmLoading="saving"
    ok-text="保存"
    cancel-text="取消"
  >
    <div class="agent-editor">
      <!-- 基础信息 -->
      <div class="editor-section">
        <div class="section-title">基础信息</div>
        <div class="form-row">
          <div class="form-item">
            <label>Agent 名称 <span class="required">*</span></label>
            <Input
              v-model:value="form.name"
              placeholder="例如：ResearchAgent"
              :status="errors.name ? 'error' : undefined"
              @change="() => (errors.name = '')"
            />
            <div v-if="errors.name" class="error-msg">{{ errors.name }}</div>
          </div>
          <div class="form-item">
            <label>职责描述 <span class="required">*</span></label>
            <Input
              v-model:value="form.duty"
              placeholder="描述该 Agent 的职责"
              :status="errors.duty ? 'error' : undefined"
              @change="() => (errors.duty = '')"
            />
            <div v-if="errors.duty" class="error-msg">{{ errors.duty }}</div>
          </div>
        </div>
        <div class="form-item">
          <label>系统提示词 <span class="required">*</span></label>
          <Textarea
            v-model:value="form.system_prompt"
            placeholder="描述该 Agent 的行为规范..."
            :rows="4"
            :status="errors.system_prompt ? 'error' : undefined"
            @change="() => (errors.system_prompt = '')"
          />
          <div v-if="errors.system_prompt" class="error-msg">{{ errors.system_prompt }}</div>
        </div>
      </div>

      <!-- 技能 -->
      <div class="editor-section">
        <div class="section-title">技能</div>
        <Select
          v-model:value="form.skills"
          mode="multiple"
          placeholder="选择该 Agent 可使用的技能"
          :options="availableSkillOptions"
          style="width: 100%"
          :loading="skillsLoading"
          optionFilterProp="label"
        />
        <div v-if="availableSkillOptions.length === 0 && !skillsLoading" class="form-hint">
          暂无可用技能，请先在「技能管理」中创建
        </div>
      </div>

      <!-- MCP Servers -->
      <div class="editor-section">
        <div class="section-title">MCP Servers</div>
        <Select
          v-model:value="form.mcp_servers"
          mode="multiple"
          placeholder="选择该 Agent 使用的 MCP Server"
          :options="availableMcpOptions"
          style="width: 100%"
          :loading="mcpLoading"
          optionFilterProp="label"
        />
        <div v-if="availableMcpOptions.length === 0 && !mcpLoading" class="form-hint">
          暂无可用 MCP Server，请先在「MCP 服务」中创建
        </div>
      </div>
    </div>
  </Modal>
</template>

<script setup lang="ts">
import { ref, reactive, computed, watch } from 'vue';
import { Modal, Input, Select } from 'ant-design-vue';
import { Textarea } from 'ant-design-vue';
import type { AgentMeta, SkillMeta, MCPServerConfig } from '../types/message';
import { getSkillsConfig, getMcpServersConfig } from '../utils/configApi';

const props = defineProps<{
  open: boolean;
  agent: AgentMeta | null;
}>();

const emit = defineEmits<{
  (e: 'update:open', v: boolean): void;
  (e: 'save', agent: AgentMeta): void;
}>();

const saving = ref(false);
const errors = reactive({ name: '', duty: '', system_prompt: '' });

// 系统已有技能
const availableSkills = ref<SkillMeta[]>([]);
const skillsLoading = ref(false);
const availableSkillOptions = computed(() =>
  availableSkills.value.map(s => ({ label: s.name, value: s.name, title: s.description }))
);

// 系统已有 MCP Servers
const availableMcpServers = ref<MCPServerConfig[]>([]);
const mcpLoading = ref(false);
const availableMcpOptions = computed(() =>
  availableMcpServers.value.map(s => ({ label: `${s.name} (${s.transport})`, value: s.name }))
);

const isEdit = computed(() => !!props.agent);

const form = reactive({
  name: '',
  duty: '',
  skills: [] as string[],
  system_prompt: '',
  mcp_servers: [] as string[],
});

watch(
  () => props.open,
  async (v) => {
    if (v) {
      errors.name = '';
      errors.duty = '';
      errors.system_prompt = '';
      // 加载系统已有技能
      skillsLoading.value = true;
      try {
        availableSkills.value = await getSkillsConfig();
      } catch (e) {
        console.error('Failed to load skills:', e);
      } finally {
        skillsLoading.value = false;
      }
      // 加载系统已有 MCP Servers
      mcpLoading.value = true;
      try {
        availableMcpServers.value = await getMcpServersConfig();
      } catch (e) {
        console.error('Failed to load MCP servers:', e);
      } finally {
        mcpLoading.value = false;
      }
      if (props.agent) {
        Object.assign(form, {
          name: props.agent.name,
          duty: props.agent.duty,
          skills: [...(props.agent.skills || [])],
          system_prompt: props.agent.system_prompt || '',
          mcp_servers: [...(props.agent.mcp_servers || [])],
        });
      } else {
        Object.assign(form, { name: '', duty: '', skills: [], system_prompt: '', mcp_servers: [] });
      }
    }
  }
);

const handleSave = () => {
  errors.name = '';
  errors.duty = '';
  errors.system_prompt = '';
  if (!form.name.trim()) { errors.name = 'Agent 名称不能为空'; return; }
  if (!form.duty.trim()) { errors.duty = '职责描述不能为空'; return; }
  if (!form.system_prompt.trim()) { errors.system_prompt = '系统提示词不能为空'; return; }

  emit('save', {
    name: form.name.trim(),
    duty: form.duty.trim(),
    skills: form.skills,
    system_prompt: form.system_prompt.trim(),
    mcp_servers: form.mcp_servers,
  });
  saving.value = true;
  setTimeout(() => { saving.value = false; }, 200);
};
</script>

<style scoped>
.agent-editor {
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
  margin-top: 4px;
}
</style>
