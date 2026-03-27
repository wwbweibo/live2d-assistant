<template>
    <div class="agent-list-item">
        <div class="agent-list-item-header">
            <div class="agent-list-item-header-title">
                <div class="agent-name">{{ item.name }}</div>
            </div>
            <div class="agent-actions">
                <EditOutlined class="action-icon" @click.stop="$emit('edit', item)" />
                <DeleteOutlined class="action-icon danger" @click.stop="$emit('delete', item)" />
            </div>
        </div>

        <div class="agent-list-item-body">
            <div class="agent-list-item-body-description">
                <label>职责:</label>
                {{ item.duty }}
            </div>
            <div class="agent-list-item-body-prompt">
                <label>提示词:</label>
                {{ item.system_prompt }}
            </div>
        </div>
    </div>
</template>

<script setup lang="ts">
import type { AgentMeta } from '../types/message';
import { EditOutlined, DeleteOutlined } from '@ant-design/icons-vue';

defineProps<{
    item: AgentMeta;
}>();

defineEmits<{
    (e: 'edit', item: AgentMeta): void;
    (e: 'delete', item: AgentMeta): void;
}>();
</script>

<style scoped>
.agent-list-item {
    display: flex;
    flex-direction: column;
    gap: 10px;
    border: 1px solid rgba(0, 0, 0, 0.06);
    border-radius: 12px;
    padding: 16px;
    margin-bottom: 10px;
    background: rgba(255, 255, 255, 0.6);
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
    transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1);
    position: relative;
    overflow: hidden;
}

.agent-list-item::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 2px;
    background: linear-gradient(90deg, #6366f1, #a78bfa);
    opacity: 0;
    transition: opacity 0.25s ease;
}

.agent-list-item:hover {
    border-color: rgba(99, 102, 241, 0.15);
    box-shadow: 0 4px 16px rgba(99, 102, 241, 0.08);
    transform: translateY(-1px);
}

.agent-list-item:hover::before {
    opacity: 1;
}

.agent-list-item-header {
    display: flex;
    flex-direction: row;
    gap: 10px;
    align-items: center;
    justify-content: space-between;
}

.agent-list-item-header-title {
    display: flex;
    flex-direction: row;
    gap: 10px;
    align-items: center;
    font-size: 15px;
    font-weight: 600;
    color: #1e1b4b;
}

.agent-list-item-body {
    display: flex;
    flex-direction: column;
    gap: 8px;
}

.agent-list-item-body-description {
    font-size: 13px;
    color: #64748b;
    line-height: 1.5;
}

.agent-list-item-body-prompt {
    font-size: 12px;
    color: #94a3b8;
    font-style: italic;
    padding: 8px 12px;
    background: rgba(0, 0, 0, 0.02);
    border-radius: 8px;
    border-left: 2px solid rgba(99, 102, 241, 0.3);
}

.agent-list-item-body-description label,
.agent-list-item-body-prompt label {
    font-weight: 600;
    color: #64748b;
    margin-right: 4px;
    font-style: normal;
}

.agent-name {
    background: linear-gradient(135deg, #6366f1, #a78bfa);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}

.agent-actions {
    display: flex;
    gap: 4px;
    opacity: 0;
    transition: opacity 0.2s ease;
}

.agent-list-item:hover .agent-actions {
    opacity: 1;
}

.action-icon {
    width: 28px;
    height: 28px;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 6px;
    cursor: pointer;
    color: #94a3b8;
    font-size: 14px;
    transition: all 0.2s ease;
}

.action-icon:hover {
    background: rgba(99, 102, 241, 0.1);
    color: var(--color-primary);
}

.action-icon.danger:hover {
    background: rgba(239, 68, 68, 0.1);
    color: #ef4444;
}
</style>
