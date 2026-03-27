<template>
  <div class="mcp-card" :class="{ 'mcp-connected': item.connected, 'mcp-disconnected': !item.connected }">
    <div class="mcp-header">
      <div class="mcp-name">
        <ApiOutlined class="mcp-icon" />
        <span>{{ item.name }}</span>
        <span class="mcp-transport">{{ item.transport }}</span>
        <span class="mcp-status" :class="item.connected ? 'status-ok' : 'status-err'">
          {{ item.connected ? '已连接' : '未连接' }}
        </span>
      </div>
      <div class="mcp-actions">
        <Button size="small" type="text" @click="$emit('edit', item)">
          <EditOutlined />
        </Button>
        <Popconfirm title="确定删除该 MCP Server？" @confirm="$emit('delete', item)">
          <Button size="small" type="text" danger>
            <DeleteOutlined />
          </Button>
        </Popconfirm>
      </div>
    </div>
    <div class="mcp-info">
      <template v-if="item.transport === 'stdio'">
        <span v-if="item.command" class="info-tag">{{ item.command }} {{ (item.args || []).join(' ') }}</span>
        <span v-if="item.cwd" class="info-tag secondary">{{ item.cwd }}</span>
      </template>
      <template v-else>
        <span v-if="item.url" class="info-tag">{{ item.url }}</span>
      </template>
    </div>
    <div v-if="item.tools && item.tools.length > 0" class="mcp-tools">
      <span class="tools-label">工具 ({{ item.tools.length }}):</span>
      <span v-for="t in item.tools" :key="t" class="tool-tag">{{ t }}</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ApiOutlined, EditOutlined, DeleteOutlined } from '@ant-design/icons-vue';
import { Button, Popconfirm } from 'ant-design-vue';
import type { MCPServerResp } from '../types/message';

defineProps<{
  item: MCPServerResp;
}>();

defineEmits<{
  (e: 'edit', item: MCPServerResp): void;
  (e: 'delete', item: MCPServerResp): void;
}>();
</script>

<style scoped>
.mcp-card {
  background: rgba(255, 255, 255, 0.6);
  backdrop-filter: blur(12px);
  border: 1px solid var(--glass-border);
  border-radius: var(--radius-md);
  padding: var(--space-md);
  transition: all 0.2s ease;
}

.mcp-card:hover {
  border-color: var(--color-primary);
  box-shadow: 0 2px 12px rgba(99, 102, 241, 0.12);
}

.mcp-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.mcp-name {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
  font-size: 14px;
  color: var(--text-primary);
}

.mcp-icon {
  color: var(--color-primary);
  font-size: 16px;
}

.mcp-transport {
  font-size: 11px;
  font-weight: 500;
  background: rgba(99, 102, 241, 0.1);
  color: var(--color-primary);
  padding: 1px 8px;
  border-radius: 10px;
}

.mcp-actions {
  display: flex;
  gap: 2px;
  opacity: 0;
  transition: opacity 0.2s;
}

.mcp-card:hover .mcp-actions {
  opacity: 1;
}

.mcp-info {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.info-tag {
  font-size: 12px;
  color: var(--text-secondary);
  background: rgba(0, 0, 0, 0.03);
  border-radius: var(--radius-sm);
  padding: 2px 8px;
  font-family: 'SF Mono', Monaco, monospace;
}

.info-tag.secondary {
  color: var(--text-tertiary);
}

.mcp-status {
  font-size: 11px;
  font-weight: 500;
  padding: 1px 8px;
  border-radius: 10px;
}

.status-ok {
  background: rgba(34, 197, 94, 0.1);
  color: #16a34a;
}

.status-err {
  background: rgba(239, 68, 68, 0.1);
  color: #dc2626;
}

.mcp-tools {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 4px;
  margin-top: 6px;
}

.tools-label {
  font-size: 11px;
  color: var(--text-tertiary);
  margin-right: 2px;
}

.tool-tag {
  font-size: 11px;
  color: var(--color-primary);
  background: rgba(99, 102, 241, 0.08);
  border-radius: 6px;
  padding: 1px 6px;
  font-family: 'SF Mono', Monaco, monospace;
}
</style>
