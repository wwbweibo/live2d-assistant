<template>
  <div class="skill-orchestration">
    <div class="skill-orchestration-header">
      <div class="header-title">
        <ThunderboltOutlined class="header-icon" />
        <span>技能管理</span>
      </div>
      <div class="header-actions">
        <Button type="primary" @click="openEditor()">
          <PlusOutlined />新建 Skill
        </Button>
      </div>
    </div>

    <div class="skill-orchestration-content">
      <div v-if="loading" class="loading">
        <span>加载中...</span>
      </div>

      <template v-else>
        <div v-if="skills.length === 0" class="empty-state">
          <ThunderboltOutlined class="empty-icon" />
          <p>暂无技能，请点击右上角「新建 Skill」开始创建</p>
          <p class="empty-hint">技能定义了 Agent 可以使用的能力和工作流程</p>
        </div>
        <div v-else class="skill-cards">
          <SkillListItem
            v-for="skill in skills"
            :key="skill.name"
            :item="skill"
            @edit="openEditor(skill)"
            @delete="handleDelete(skill.name)"
          />
        </div>
      </template>
    </div>

    <SkillEditorModal
      v-model:open="editorVisible"
      :skill="editingSkill"
      @save="saveSkill"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { ThunderboltOutlined, PlusOutlined } from '@ant-design/icons-vue';
import { Button, message } from 'ant-design-vue';
import type { SkillMeta } from '../types/message';
import SkillListItem from './skill_list_item.vue';
import SkillEditorModal from './skill_editor_modal.vue';
import { getSkillsConfig, upsertSkill, deleteSkillByName } from '../utils/configApi';

const editorVisible = ref(false);
const editingSkill = ref<SkillMeta | null>(null);
const loading = ref(true);
const skills = ref<SkillMeta[]>([]);

const loadSkills = async () => {
  loading.value = true;
  try {
    skills.value = await getSkillsConfig();
  } catch (e) {
    console.error('Failed to load skills:', e);
    message.error('加载技能配置失败');
  } finally {
    loading.value = false;
  }
};

onMounted(loadSkills);

const openEditor = (skill?: SkillMeta) => {
  editingSkill.value = skill ? { ...skill } : null;
  editorVisible.value = true;
};

const saveSkill = async (skill: SkillMeta) => {
  try {
    await upsertSkill(skill);
    await loadSkills();
    editorVisible.value = false;
    message.success('保存成功');
  } catch (e) {
    console.error('Failed to save skill:', e);
    message.error('保存技能失败');
  }
};

const handleDelete = async (name: string) => {
  try {
    await deleteSkillByName(name);
    await loadSkills();
    message.success('已删除');
  } catch (e) {
    console.error('Failed to delete skill:', e);
    message.error('删除技能失败');
  }
};
</script>

<style scoped>
.skill-orchestration {
  display: flex;
  flex-direction: column;
  height: 100%;
  padding: var(--space-md);
  gap: var(--space-md);
}

.skill-orchestration-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
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
  gap: 8px;
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
}

.header-icon {
  color: var(--color-primary);
  font-size: 20px;
}

.skill-orchestration-content {
  flex: 1;
  overflow-y: auto;
  background: rgba(255, 255, 255, 0.7);
  backdrop-filter: blur(12px);
  border: 1px solid var(--glass-border);
  border-radius: var(--radius-lg);
  padding: var(--space-md);
}

.skill-cards {
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
}

.loading {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 120px;
  color: var(--text-secondary);
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 200px;
  color: var(--text-tertiary);
  text-align: center;
}

.empty-icon {
  font-size: 48px;
  margin-bottom: var(--space-md);
  opacity: 0.3;
}

.empty-state p {
  margin: 2px 0;
}

.empty-hint {
  font-size: 12px;
  opacity: 0.7;
}
</style>
