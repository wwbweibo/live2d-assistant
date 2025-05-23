<template>
    <div class="mcp-server-list-item">
        <div class="mcp-server-list-item-header">
            <div class="mcp-server-list-item-header-title">
                <div>
                    {{ item.name }}
                </div>
                <div class="mcp-server-list-item-header-status" :style="{ backgroundColor: statusColor }">
                </div>
                <div class="mcp-server-list-item-header-transport">
                    {{ item.transport }}
                </div>
            </div>
        </div>
        <div class="mcp-server-list-item-tools">
            <div class="mcp-server-list-item-tools-item" v-for="tool in item.tools" :key="tool.name">
                <Tooltip :title="tool.description">
                    <Tag>{{ tool.name }}</Tag>
                </Tooltip>
            </div>
        </div>
        <div class="mcp-server-list-item-body">
            <div class="mcp-server-list-item-body-url" v-if="item.url">
                <label>URL:</label>
                {{ item.url }}
            </div>
            <div class="mcp-server-list-item-body-command" v-if="item.command">
                <label>Command:</label>
                {{ item.command }}
            </div>
            <div class="mcp-server-list-item-body-args" v-if="item.args">
                <label>Args:</label>
                {{ item.args }}
            </div>
        </div>
    </div>
</template>

<script setup lang="ts">
import type { MCPServer } from '../types/message';
import { ref, computed } from 'vue';
import { Tag, Tooltip } from 'ant-design-vue';
const props = defineProps<{
    item: MCPServer;
}>()

const statusColor = computed(() => {
    return props.item.status === 'online' ? 'green' : 'red'
})

</script>

<style scoped>
.mcp-server-list-item {
    display: flex;
    flex-direction: column;
    gap: 10px;
    border: 1px solid #ccc;
    border-radius: 5px;
    padding: 10px;
    margin-bottom: 10px;
}

.mcp-server-list-item-header {
    display: flex;
    flex-direction: row;
    gap: 10px;
}

.mcp-server-list-item-header-title {
    display: flex;
    flex-direction: row;
    gap: 10px;
    font-size: 16px;
    font-weight: bold;
}

.mcp-server-list-item-header-transport {
    font-size: 12px;
    color: #ccc;
    align-self: flex-end;
}

.mcp-server-list-item-header-status {
    font-size: 12px;
    align-self: flex-start;
    width: 10px;
    height: 10px;
    border-radius: 50%;
}

.mcp-server-list-item-body {
    display: flex;
    flex-direction: column;
    gap: 10px;
}

.mcp-server-list-item-body-url {
    font-size: 12px;
    color: #777;
}

.mcp-server-list-item-body-command {
    font-size: 12px;
    color: #ccc;
}

.mcp-server-list-item-body-args {
    font-size: 12px;
    color: #ccc;
}

.mcp-server-list-item-tools {
    display: flex;
    flex-direction: row;
    gap: 10px;
    flex-wrap: wrap;
}

.mcp-server-list-item-tools-item {
    font-size: 12px;
    color: #ccc;
}
</style>
