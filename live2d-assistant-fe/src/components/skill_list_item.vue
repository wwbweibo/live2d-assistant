<template>
  <div class="skill-card">
    <div class="skill-header">
      <div class="skill-name">
        <ThunderboltOutlined class="skill-icon" />
        <span>{{ item.name }}</span>
      </div>
      <div class="skill-actions">
        <Button size="small" type="text" @click="$emit('edit', item)">
          <EditOutlined />
        </Button>
        <Popconfirm title="确定删除该技能？" @confirm="$emit('delete', item)">
          <Button size="small" type="text" danger>
            <DeleteOutlined />
          </Button>
        </Popconfirm>
      </div>
    </div>
    <div class="skill-description">{{ item.description }}</div>
    <div v-if="item.instruction" class="skill-instruction">
      {{ item.instruction.length > 120 ? item.instruction.slice(0, 120) + '...' : item.instruction }}
    </div>
  </div>
</template>

<script setup lang="ts">
import { ThunderboltOutlined, EditOutlined, DeleteOutlined } from '@ant-design/icons-vue';
import { Button, Popconfirm } from 'ant-design-vue';
import type { SkillMeta } from '../types/message';

defineProps<{
  item: SkillMeta;
}>();

defineEmits<{
  (e: 'edit', item: SkillMeta): void;
  (e: 'delete', item: SkillMeta): void;
}>();
</script>

<style scoped>
.skill-card {
  background: rgba(255, 255, 255, 0.6);
  backdrop-filter: blur(12px);
  border: 1px solid var(--glass-border);
  border-radius: var(--radius-md);
  padding: var(--space-md);
  transition: all 0.2s ease;
}

.skill-card:hover {
  border-color: var(--color-primary);
  box-shadow: 0 2px 12px rgba(99, 102, 241, 0.12);
}

.skill-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.skill-name {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
  font-size: 14px;
  color: var(--text-primary);
}

.skill-icon {
  color: var(--color-primary);
  font-size: 16px;
}

.skill-actions {
  display: flex;
  gap: 2px;
  opacity: 0;
  transition: opacity 0.2s;
}

.skill-card:hover .skill-actions {
  opacity: 1;
}

.skill-description {
  font-size: 13px;
  color: var(--text-secondary);
  margin-bottom: 6px;
}

.skill-instruction {
  font-size: 12px;
  color: var(--text-tertiary);
  background: rgba(0, 0, 0, 0.03);
  border-radius: var(--radius-sm);
  padding: 8px;
  border-left: 3px solid var(--color-primary);
  line-height: 1.5;
  white-space: pre-wrap;
}
</style>
