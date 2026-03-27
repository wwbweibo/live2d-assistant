<template>
  <div class="mcp-orchestration">
    <div class="mcp-orchestration-header">
      <div class="header-title">
        <ApiOutlined class="header-icon" />
        <span>MCP 服务管理</span>
      </div>
      <div class="header-actions">
        <Button type="primary" @click="openEditor()">
          <PlusOutlined />新建 MCP Server
        </Button>
      </div>
    </div>

    <div class="mcp-orchestration-content">
      <div v-if="loading" class="loading">
        <span>加载中...</span>
      </div>

      <template v-else>
        <div v-if="servers.length === 0" class="empty-state">
          <ApiOutlined class="empty-icon" />
          <p>暂无 MCP Server，请点击右上角「新建 MCP Server」开始创建</p>
          <p class="empty-hint">MCP Server 为 Agent 提供外部工具和数据源连接</p>
        </div>
        <div v-else class="mcp-cards">
          <McpServerListItem
            v-for="server in servers"
            :key="server.name"
            :item="server"
            @edit="openEditor(server)"
            @delete="handleDelete(server.name)"
          />
        </div>
      </template>
    </div>

    <McpServerEditorModal
      v-model:open="editorVisible"
      :server="editingServer"
      @save="saveServer"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { ApiOutlined, PlusOutlined } from '@ant-design/icons-vue';
import { Button, message } from 'ant-design-vue';
import type { MCPServerConfig, MCPServerResp } from '../types/message';
import McpServerListItem from './mcp_server_list_item.vue';
import McpServerEditorModal from './mcp_server_editor_modal.vue';
import { getMcpServersConfig, upsertMcpServer, deleteMcpServerByName } from '../utils/configApi';

const editorVisible = ref(false);
const editingServer = ref<MCPServerConfig | null>(null);
const loading = ref(true);
const servers = ref<MCPServerResp[]>([]);

const loadServers = async () => {
  loading.value = true;
  try {
    servers.value = await getMcpServersConfig();
  } catch (e) {
    console.error('Failed to load MCP servers:', e);
    message.error('加载 MCP Server 配置失败');
  } finally {
    loading.value = false;
  }
};

onMounted(loadServers);

const openEditor = (server?: MCPServerConfig) => {
  editingServer.value = server ? { ...server } : null;
  editorVisible.value = true;
};

const saveServer = async (server: MCPServerConfig) => {
  try {
    await upsertMcpServer(server);
    await loadServers();
    editorVisible.value = false;
    message.success('保存成功');
  } catch (e) {
    console.error('Failed to save MCP server:', e);
    message.error('保存 MCP Server 失败');
  }
};

const handleDelete = async (name: string) => {
  try {
    await deleteMcpServerByName(name);
    await loadServers();
    message.success('已删除');
  } catch (e) {
    console.error('Failed to delete MCP server:', e);
    message.error('删除 MCP Server 失败');
  }
};
</script>

<style scoped>
.mcp-orchestration {
  display: flex;
  flex-direction: column;
  height: 100%;
  padding: var(--space-md);
  gap: var(--space-md);
}

.mcp-orchestration-header {
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

.mcp-orchestration-content {
  flex: 1;
  overflow-y: auto;
  background: rgba(255, 255, 255, 0.7);
  backdrop-filter: blur(12px);
  border: 1px solid var(--glass-border);
  border-radius: var(--radius-lg);
  padding: var(--space-md);
}

.mcp-cards {
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
