<template>
  <Modal
    :open="open"
    :title="isEdit ? '编辑 Skill' : '新建 Skill'"
    :width="640"
    @cancel="$emit('update:open', false)"
    @ok="handleSave"
    :confirmLoading="saving"
    ok-text="保存"
    cancel-text="取消"
  >
    <div class="skill-editor">
      <div class="editor-section">
        <div class="section-title">基础信息</div>
        <div class="form-item">
          <label>技能名称 <span class="required">*</span></label>
          <Input
            v-model:value="form.name"
            placeholder="例如：web_search"
            :status="errors.name ? 'error' : undefined"
            @change="() => (errors.name = '')"
          />
          <div v-if="errors.name" class="error-msg">{{ errors.name }}</div>
        </div>
        <div class="form-item">
          <label>描述 <span class="required">*</span></label>
          <Input
            v-model:value="form.description"
            placeholder="简要描述该技能的用途"
            :status="errors.description ? 'error' : undefined"
            @change="() => (errors.description = '')"
          />
          <div v-if="errors.description" class="error-msg">{{ errors.description }}</div>
        </div>
      </div>

      <div class="editor-section">
        <div class="section-title">技能指令</div>
        <div class="form-item">
          <label>Instruction <span class="required">*</span></label>
          <Textarea
            v-model:value="form.instruction"
            placeholder="详细描述该技能的使用方法和工作流程..."
            :rows="8"
            :status="errors.instruction ? 'error' : undefined"
            @change="() => (errors.instruction = '')"
          />
          <div v-if="errors.instruction" class="error-msg">{{ errors.instruction }}</div>
          <div class="form-hint">支持 Markdown 格式，Agent 在调用 lookup_skill 时会获取此内容</div>
        </div>
      </div>
    </div>
  </Modal>
</template>

<script setup lang="ts">
import { ref, reactive, computed, watch } from 'vue';
import { Modal, Input } from 'ant-design-vue';
import { Textarea } from 'ant-design-vue';
import type { SkillMeta } from '../types/message';

const props = defineProps<{
  open: boolean;
  skill: SkillMeta | null;
}>();

const emit = defineEmits<{
  (e: 'update:open', v: boolean): void;
  (e: 'save', skill: SkillMeta): void;
}>();

const saving = ref(false);
const errors = reactive({ name: '', description: '', instruction: '' });

const isEdit = computed(() => !!props.skill);

const form = reactive({
  name: '',
  description: '',
  instruction: '',
});

watch(
  () => props.open,
  (v) => {
    if (v) {
      errors.name = '';
      errors.description = '';
      errors.instruction = '';
      if (props.skill) {
        Object.assign(form, {
          name: props.skill.name,
          description: props.skill.description,
          instruction: props.skill.instruction || '',
        });
      } else {
        Object.assign(form, { name: '', description: '', instruction: '' });
      }
    }
  }
);

const handleSave = () => {
  errors.name = '';
  errors.description = '';
  errors.instruction = '';
  if (!form.name.trim()) { errors.name = '技能名称不能为空'; return; }
  if (!form.description.trim()) { errors.description = '描述不能为空'; return; }
  if (!form.instruction.trim()) { errors.instruction = '技能指令不能为空'; return; }

  emit('save', {
    name: form.name.trim(),
    description: form.description.trim(),
    instruction: form.instruction.trim(),
  });
  saving.value = true;
  setTimeout(() => { saving.value = false; }, 200);
};
</script>

<style scoped>
.skill-editor {
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
