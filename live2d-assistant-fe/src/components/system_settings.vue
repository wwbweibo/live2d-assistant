<template>
    <div class="settings-section">
        <Collapse v-model:activeKey="collapseActiveKey">
            <CollapsePanel header="基础设置" key="basic">
                <div class="setting-item">
                    <label>服务器地址</label>
                    <input v-model="settings.serverUrl" type="text" @change="updateSettings">
                </div>
            </CollapsePanel>
            <CollapsePanel header="Live2D 设置" key="live2d">
                <div class="setting-item">
                    <label>背景图片</label>
                    <div class="setting-control">
                        <input v-model="settings.backgroundPath" type="text" @change="updateSettings">
                        <button class="reset-button" @click="">重置</button>
                    </div>
                </div>
                <div class="setting-item">
                    <label>Live2D 模型</label>
                    <div class="setting-control">
                        <input v-model="settings.live2DSettings.modelPath" type="text" @change="updateSettings">
                        <button class="reset-button" @click="">重置</button>
                    </div>
                </div>
                <div class="setting-item">
                    <label>模型横向偏移</label>
                    <Slider v-model:value="settings.live2DSettings.offsetX" @change="updateSettings" :min="-100"
                        :max="100" :step="1" />
                </div>
                <div class="setting-item">
                    <label>模型纵向偏移</label>
                    <Slider v-model:value="settings.live2DSettings.offsetY" @change="updateSettings" :min="-100"
                        :max="100" :step="1" />
                </div>
                <div class="setting-item">
                    <label>模型缩放</label>
                    <Slider v-model:value="settings.live2DSettings.scale" @change="updateSettings" :min="0.1" :max="1"
                        :step="0.1" />
                </div>
                <div class="setting-item">
                    <label>主题颜色</label>
                    <div class="setting-control">
                        <ColorPicker v-model:pureColor="settings.live2DSettings.themeColor" @pureColorChange="updateSettings"/>
                    </div>
                </div>
            </CollapsePanel>
            <CollapsePanel header="LLM 设置" key="llm">
                <div class="setting-item">
                    <label>助手名称</label>
                    <input v-model="settings.assistantSettings.assistantName" type="text" @change="updateSettings">
                </div>
                <div class="setting-item">
                    <label>LLM Base URL</label>
                    <input v-model="settings.assistantSettings.baseUrl" type="text" @change="updateSettings">
                </div>
                <div class="setting-item">
                    <label>LLM API Key</label>
                    <input v-model="settings.assistantSettings.apiKey" type="text" @change="updateSettings">
                </div>
                <div class="setting-item">
                    <label>LLM 模型</label>
                    <input v-model="settings.assistantSettings.model" type="text" @change="updateSettings">
                </div>
                <div class="setting-item">
                    <div class="setting-header">
                        <el-tooltip content="系统提示词，用于设置助手的默认行为和风格。" placement="top">
                            <template #content>
                                <div>系统提示词，用于设置助手的默认行为和风格。</div>
                            </template>
                            <el-icon>
                                <QuestionCircleFilled />
                            </el-icon>
                        </el-tooltip>
                        <label>系统提示词</label>
                    </div>
                    <el-input type="textarea" class="system-prompt-textarea" :rows="4"
                        v-model="settings.assistantSettings.sysPrompt" placeholder="请输入系统提示词" @change="updateSettings">
                    </el-input>
                </div>
                <div class="setting-item">
                    <div class="setting-header">
                        <el-tooltip content="MCP Servers，用于设置MCP服务器的地址。" placement="top" class="mcp-setting-tooltip">
                            <template #content>
                                <div>MCP Servers，用于设置MCP服务器的地址。</div>
                            </template>
                            <el-icon>
                                <QuestionCircleFilled />
                            </el-icon>
                        </el-tooltip>
                        <label>MCP Servers</label>
                        <div class="mcp-setting-edit">
                            <EditOutlined @click="() => { editMcpServersModal = true }" />
                        </div>
                    </div>
                    <div class="mcp-server-list">
                        <MCPServerListItem v-for="item in mcpServers" :key="item.name" :item="item" />
                    </div>
                </div>
                <div class="setting-item">
                    <div class="setting-header">
                        <el-tooltip content="Agent 设置，用于设置Agent的配置。" placement="top" class="mcp-setting-tooltip">
                            <template #content>
                                <div>Agent 设置，用于设置Agent的配置。</div>
                            </template>
                            <el-icon>
                                <QuestionCircleFilled />
                            </el-icon>
                        </el-tooltip>
                        <label>Agent 设置</label>
                        <div class="mcp-setting-edit">
                            <EditOutlined @click="() => { editAgentsModal = true }" />
                        </div>
                    </div>
                    <div class="agent-setting-list">
                        <AgentListItem v-for="item in agents" :key="item.name" :item="item" />
                    </div>
                </div>
            </CollapsePanel>
        </Collapse>
    </div>
    <Modal v-model:open="editMcpServersModal" title="编辑MCP服务器" @ok="editMcpServers" width="60%">
        <JsonEditorVue v-model="mcpServersValue" :mode="Mode.text" :mainMenuBar=false :navigationBar=false />
    </Modal>
    <Modal v-model:open="editAgentsModal" title="编辑Agent" @ok="editAgents" width="60%">
        <JsonEditorVue v-model="agentsValue" :mode="Mode.text" :mainMenuBar=false :navigationBar=false />
    </Modal>
</template>

<script setup lang="ts">
import 'element-plus/dist/index.css'
import { PropType, ref, h, watch, onMounted } from 'vue';
import { SystemSettings, MCPServer, MCPServerStatus, MCPServerTool, AgentConfig } from '../types/message';
import MCPServerListItem from './mcp_server_list_item.vue'
import AgentListItem from './agent_list_item.vue'
import { EditOutlined, QuestionCircleFilled } from '@ant-design/icons-vue';
import { Modal, message, Collapse, CollapsePanel, Slider } from 'ant-design-vue';
import { ColorPicker } from "vue3-colorpicker";
import "vue3-colorpicker/style.css";
import JsonEditorVue from 'json-editor-vue'
import { Mode } from 'vanilla-jsoneditor';
import { getMcpServerStatus } from '../utils/requests';

const props = defineProps({
    systemSettings: {
        type: Object as PropType<SystemSettings>,
        required: true
    },
    onChange: {
        type: Function,
        required: true
    }
})

const settings = ref<SystemSettings>(props.systemSettings)
const collapseActiveKey = ref<string[]>(['basic'])
const updateSettings = () => {
    console.log('updateSettings', settings.value)
    props.onChange(settings.value)
}

const setting2mcpServers = async (settings: SystemSettings) => {
    if (!settings.assistantSettings.mcpServers) {
        console.log('mcpServers is null')
        return []
    }
    try {
        const servers = JSON.parse(settings.assistantSettings.mcpServers)
        const mcpServers: MCPServer[] = []
        for (let i = 0; i < servers.length; i++) {
            let status: MCPServerStatus | null = null
            try {
                status = await getMcpServerStatus(servers[i].name, settings)
            } catch (error) {
                console.error(error)
            }
            const server = {
                name: servers[i].name,
                transport: servers[i].transport,
                url: servers[i].url,
                command: servers[i].command,
                args: servers[i].args,
                tools: [] as MCPServerTool[],
                status: 'offline'
            }
            if (status && status.status === 'success') {
                server.status = 'online'
                server.tools = status.details.tools
            } else {
                server.status = 'offline'
            }
            console.log('status', status)
            console.log('server', server)
            mcpServers.push(server)
        }
        console.log("mcpServers", mcpServers)
        return mcpServers
    } catch (error) {
        console.error(error)
        return []
    }
}

const setting2agents = async (settings: SystemSettings) => {
    if (!settings.assistantSettings.agents) {
        console.log('agents is null')
        return []
    }
    try {
        const agents = JSON.parse(settings.assistantSettings.agents)
        return agents
    } catch (error) {
        console.error(error)
        return []
    }
}

const mcpServers = ref<MCPServer[]>([])
watch(() => settings.value.assistantSettings.mcpServers, async () => {
    mcpServers.value = await setting2mcpServers(settings.value)
})

const agents = ref<AgentConfig[]>([])
watch(() => settings.value.assistantSettings.agents, async () => {
    agents.value = JSON.parse(settings.value.assistantSettings.agents || '[]')
})

const editMcpServersModal = ref<boolean>(false)
const mcpServersValue = ref<any>(JSON.parse(props.systemSettings.assistantSettings.mcpServers || '[]'))
const editMcpServers = () => {
    // 检查 mcpServersValue 是否符合 MCPServer 的格式
    let servers = mcpServersValue.value
    if (typeof servers === 'string') {
        try {
            servers = JSON.parse(servers)
        } catch (error) {
            message.error('MCP服务器格式错误')
            return
        }
    }
    settings.value.assistantSettings.mcpServers = JSON.stringify(servers)
    editMcpServersModal.value = false
}

const editAgentsModal = ref<boolean>(false)
const agentsValue = ref<any>(JSON.parse(props.systemSettings.assistantSettings.agents || '[]'))
const editAgents = () => {
    settings.value.assistantSettings.agents = agentsValue.value
    editAgentsModal.value = false
}

onMounted(async () => {
    mcpServers.value = await setting2mcpServers(settings.value)
    agents.value = JSON.parse(settings.value.assistantSettings.agents || '[]')
})
</script>

<style scoped>
.settings-section {
    border-radius: 12px;
    padding: 4px;
}

.setting-item {
    margin-bottom: 20px;
}

label {
    display: block;
    margin-bottom: 10px;
    color: #444;
    font-weight: 500;
    font-size: 14px;
}

input[type="text"],
select {
    width: 100%;
    padding: 10px 12px;
    border: 1px solid #e0e0e0;
    border-radius: 8px;
    font-size: 14px;
    transition: all 0.3s;
    background-color: white;
}

input[type="text"]:hover,
select:hover {
    border-color: #1890ff;
    box-shadow: 0 0 0 2px rgba(24, 144, 255, 0.1);
}

input[type="text"]:focus,
select:focus {
    border-color: #1890ff;
    box-shadow: 0 0 0 2px rgba(24, 144, 255, 0.2);
    outline: none;
}

select {
    cursor: pointer;
    appearance: none;
    background-image: url("data:image/svg+xml;charset=utf-8,%3Csvg xmlns='http://www.w3.org/2000/svg' width='16' height='16' viewBox='0 0 24 24' fill='none' stroke='%23666' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M6 9l6 6 6-6'/%3E%3C/svg%3E");
    background-repeat: no-repeat;
    background-position: right 10px center;
    padding-right: 30px;
}

.system-prompt-textarea {
    width: 100%;
    min-height: 120px;
    border-radius: 8px;
    border: 1px solid #e0e0e0;
    transition: all 0.3s;
}

.system-prompt-textarea:hover {
    border-color: #1890ff;
    box-shadow: 0 0 0 2px rgba(24, 144, 255, 0.1);
}

.setting-header {
    display: flex;
    align-items: center;
    margin-bottom: 10px;
}

.setting-control {
    display: flex;
    gap: 12px;
    align-items: center;
}

.reset-button {
    padding: 6px 12px;
    background: #ff4d4f;
    color: white;
    border: none;
    border-radius: 6px;
    cursor: pointer;
    font-size: 13px;
    white-space: nowrap;
    transition: all 0.3s;
}

.reset-button:hover {
    background: #ff7875;
    box-shadow: 0 2px 6px rgba(255, 77, 79, 0.2);
}

.divider {
    margin: 16px 0;
    border-bottom: 1px solid #eee;
}

.divider label {
    font-size: 16px;
    font-weight: 600;
    margin-top: 12px;
    color: #333;
}

.mcp-server-list, .agent-setting-list {
    background: #f9fafc;
    border-radius: 8px;
    padding: 12px;
    margin-top: 8px;
    border: 1px solid #eaedf1;
}

.mcp-setting-edit, .mcp-setting-tooltip {
    margin-left: 8px;
    color: #1890ff;
    cursor: pointer;
    transition: opacity 0.2s;
}

.mcp-setting-edit:hover {
    opacity: 0.8;
}
</style>
