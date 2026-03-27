<template>
  <div class="agent-orchestration">
    <div class="agent-orchestration-header">
      <div class="header-title">
        <RobotOutlined class="header-icon" />
        <span>Agent 编排</span>
      </div>
      <div class="header-actions">
        <Button type="primary" @click="openEditor()">
          <PlusOutlined />新建 Agent
        </Button>
      </div>
    </div>

    <div class="agent-orchestration-content">
      <!-- 加载状态 -->
      <div v-if="loading" class="loading">
        <span>加载中...</span>
      </div>

      <template v-else>
        <!-- Agent 列表 + 可视化切换 -->
        <div class="view-tabs">
          <div
            :class="['view-tab', { active: viewMode === 'list' }]"
            @click="viewMode = 'list'"
          >
            <UnorderedListOutlined /> 列表视图
          </div>
          <div
            :class="['view-tab', { active: viewMode === 'graph' }]"
            @click="viewMode = 'graph'"
          >
            <ApartmentOutlined /> 拓扑视图
          </div>
        </div>

        <!-- 列表视图 -->
        <div v-if="viewMode === 'list'" class="agent-list">
          <div v-if="agents.length === 0" class="empty-state">
            <RobotOutlined class="empty-icon" />
            <p>暂无 Agent，请点击右上角「新建 Agent」开始创建</p>
          </div>
          <div v-else class="agent-cards">
            <AgentListItem
              v-for="agent in agents"
              :key="agent.name"
              :item="agent"
              @edit="openEditor(agent)"
              @delete="deleteAgentByName(agent.name)"
            />
          </div>
        </div>

        <!-- 拓扑视图 -->
        <div v-if="viewMode === 'graph'" class="agent-graph">
          <div class="graph-container">
            <div class="router-node">
              <div class="node router">
                <RobotOutlined />
                <span>Router</span>
                <p class="node-desc">入口接待员</p>
              </div>
              <div class="router-lines">
                <div
                  v-for="agent in agents"
                  :key="agent.name"
                  class="line-to-agent"
                >
                  <div class="line"></div>
                </div>
              </div>
            </div>
            <div class="agents-row">
              <div
                v-for="agent in agents"
                :key="agent.name"
                :class="['agent-node', { selected: selectedAgent?.name === agent.name }]"
                @click="selectedAgent = agent"
              >
                <div class="node agent">
                  <UserSwitchOutlined />
                  <span>{{ agent.name }}</span>
                  <p class="node-desc">{{ agent.duty }}</p>
                </div>
              </div>
            </div>
          </div>
          <div v-if="selectedAgent" class="agent-detail-panel">
            <div class="detail-header">
              <span>{{ selectedAgent.name }}</span>
              <CloseOutlined @click="selectedAgent = null" />
            </div>
            <div class="detail-body">
              <div class="detail-item">
                <label>职责</label>
                <p>{{ selectedAgent.duty }}</p>
              </div>
              <div class="detail-item" v-if="selectedAgent.skills?.length">
                <label>技能</label>
                <div class="skills-tags">
                  <Tag v-for="s in selectedAgent.skills" :key="s" color="blue">{{ s }}</Tag>
                </div>
              </div>
              <div class="detail-item" v-if="selectedAgent.system_prompt">
                <label>系统提示词</label>
                <div class="prompt-box">{{ selectedAgent.system_prompt }}</div>
              </div>
              <div class="detail-item" v-if="selectedAgent.mcp_servers?.length">
                <label>MCP Servers</label>
                <div class="skills-tags">
                  <Tag v-for="s in selectedAgent.mcp_servers" :key="s" color="purple">{{ s }}</Tag>
                </div>
              </div>
            </div>
          </div>
        </div>
      </template>
    </div>

    <!-- Agent 编辑器弹窗 -->
    <AgentEditorModal
      v-model:open="editorVisible"
      :agent="editingAgent"
      @save="saveAgent"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import {
  RobotOutlined,
  PlusOutlined,
  UnorderedListOutlined,
  ApartmentOutlined,
  UserSwitchOutlined,
  CloseOutlined
} from '@ant-design/icons-vue';
import { Button, Tag, message } from 'ant-design-vue';
import type { AgentMeta, AgentConfig } from '../types/message';
import AgentListItem from './agent_list_item.vue';
import AgentEditorModal from './agent_editor_modal.vue';
import { getAgentsConfig, updateAgentsConfig, deleteAgentByName as deleteAgentApi } from '../utils/configApi';

const viewMode = ref<'list' | 'graph'>('list');
const selectedAgent = ref<AgentMeta | null>(null);
const editorVisible = ref(false);
const editingAgent = ref<AgentMeta | null>(null);
const loading = ref(true);

const agentConfig = ref<AgentConfig>({ metadata: {}, agents: [], mcp_servers: [] });
const agents = ref<AgentMeta[]>([]);

// 加载 agents 从后端
const loadAgents = async () => {
  loading.value = true;
  try {
    const data = await getAgentsConfig();
    agentConfig.value = data;
    agents.value = data.agents || [];
  } catch (e) {
    console.error('Failed to load agents:', e);
    message.error('加载 Agent 配置失败');
  } finally {
    loading.value = false;
  }
};

onMounted(loadAgents);

const openEditor = (agent?: AgentMeta) => {
  editingAgent.value = agent ? { ...agent } : null;
  editorVisible.value = true;
};

// 保存 Agent（更新或新增到 agentConfig.agents）
const saveAgent = async (agent: AgentMeta) => {
  try {
    const config = { ...agentConfig.value };
    const idx = config.agents.findIndex(a => a.name === agent.name);
    if (idx >= 0) {
      config.agents[idx] = agent;
    } else {
      config.agents.push(agent);
    }
    await updateAgentsConfig(config);
    await loadAgents();
    editorVisible.value = false;
    message.success('保存成功');
  } catch (e) {
    console.error('Failed to save agent:', e);
    message.error('保存 Agent 失败');
  }
};

// 删除 Agent
const deleteAgentByName = async (name: string) => {
  try {
    await deleteAgentApi(name);
    await loadAgents();
    message.success('已删除');
  } catch (e) {
    console.error('Failed to delete agent:', e);
    message.error('删除 Agent 失败');
  }
};
</script>

<style scoped>
.agent-orchestration {
  display: flex;
  flex-direction: column;
  height: 100%;
  padding: var(--space-md);
  gap: var(--space-md);
}

.agent-orchestration-header {
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

.agent-orchestration-content {
  flex: 1;
  overflow: auto;
  background: rgba(255, 255, 255, 0.7);
  backdrop-filter: blur(12px);
  border: 1px solid var(--glass-border);
  border-radius: var(--radius-lg);
  padding: var(--space-md);
}

.loading {
  text-align: center;
  padding: var(--space-2xl);
  color: var(--text-secondary);
}

.view-tabs {
  display: flex;
  gap: var(--space-sm);
  margin-bottom: var(--space-md);
}

.view-tab {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px var(--space-md);
  border-radius: var(--radius-full);
  cursor: pointer;
  font-size: 13px;
  font-weight: 500;
  color: var(--text-secondary);
  border: 1px solid transparent;
  transition: all var(--duration-fast) var(--ease-out);
}

.view-tab:hover {
  background: rgba(99, 102, 241, 0.06);
  color: var(--color-primary);
}

.view-tab.active {
  background: var(--color-primary);
  color: #fff;
  border-color: var(--color-primary);
}

.empty-state {
  text-align: center;
  padding: var(--space-2xl);
  color: var(--text-muted);
}

.empty-icon {
  font-size: 48px;
  color: var(--glass-border);
  margin-bottom: var(--space-md);
  display: block;
}

.agent-cards {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: var(--space-md);
}

/* ─── 拓扑视图 ─────────────────────────────────── */
.agent-graph {
  display: flex;
  gap: var(--space-md);
  height: 400px;
  position: relative;
}

.graph-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-lg);
  padding: var(--space-md);
}

.router-node {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.node {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-width: 100px;
  padding: var(--space-md);
  border-radius: var(--radius-lg);
  font-weight: 600;
  font-size: 14px;
  cursor: pointer;
  gap: 4px;
  transition: all var(--duration-fast) var(--ease-out);
  border: 2px solid transparent;
}

.node.router {
  background: linear-gradient(135deg, #6366f1, #a78bfa);
  color: #fff;
  font-size: 16px;
}

.node.agent {
  background: rgba(255, 255, 255, 0.95);
  border-color: var(--glass-border);
  color: var(--text-primary);
  min-width: 120px;
}

.node.agent:hover,
.agent-node.selected .node.agent {
  border-color: var(--color-primary);
  box-shadow: 0 4px 16px rgba(99, 102, 241, 0.2);
  transform: translateY(-2px);
}

.node-desc {
  font-size: 11px;
  font-weight: 400;
  opacity: 0.7;
  margin: 0;
  text-align: center;
  max-width: 100px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.router-lines {
  display: flex;
  gap: var(--space-xl);
  margin-top: var(--space-sm);
  position: relative;
  width: 100%;
  justify-content: center;
}

.line {
  width: 2px;
  height: 30px;
  background: linear-gradient(to bottom, rgba(99, 102, 241, 0.5), rgba(99, 102, 241, 0.1));
  margin: 0 auto;
}

.agents-row {
  display: flex;
  gap: var(--space-xl);
  flex-wrap: wrap;
  justify-content: center;
}

.agent-node {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
}

/* ─── 详情面板 ─────────────────────────────────── */
.agent-detail-panel {
  width: 260px;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(12px);
  border: 1px solid var(--glass-border);
  border-radius: var(--radius-lg);
  overflow: hidden;
  flex-shrink: 0;
}

.detail-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--space-sm) var(--space-md);
  background: linear-gradient(135deg, #6366f1, #a78bfa);
  color: #fff;
  font-weight: 600;
  font-size: 14px;
}

.detail-header .anticon {
  cursor: pointer;
  opacity: 0.8;
}

.detail-header .anticon:hover {
  opacity: 1;
}

.detail-body {
  padding: var(--space-md);
  display: flex;
  flex-direction: column;
  gap: var(--space-md);
}

.detail-item label {
  display: block;
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--text-muted);
  margin-bottom: 4px;
}

.detail-item p {
  margin: 0;
  font-size: 13px;
  color: var(--text-primary);
  line-height: 1.5;
}

.skills-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.prompt-box {
  font-size: 12px;
  background: rgba(0, 0, 0, 0.03);
  border-radius: var(--radius-sm);
  padding: var(--space-sm);
  color: var(--text-secondary);
  line-height: 1.5;
  max-height: 100px;
  overflow-y: auto;
}
</style>
