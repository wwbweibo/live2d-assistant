<template>
    <div class="agent-list-item">
        <div class="agent-list-item-header">
            <div class="agent-list-item-header-title">
                <div>
                    {{ item.name }}
                </div>
            </div>
        </div>
        
        <div class="agent-list-item-body">
            <div class="agent-list-item-body-description">
                <label>Description:</label>
                {{ item.description }}
            </div>
            <div class="agent-list-item-body-prompt" v-if="item.prompt">
                <label>Prompt:</label>
                {{ item.prompt }}
            </div>
            <div class="agent-list-item-body-hands-off" v-if="item.hands_off">
                <label>Hands Off:</label>
                {{ item.hands_off.join(', ') }}
            </div>
        </div>
    </div>
</template>

<script setup lang="ts">
import type { AgentConfig } from '../types/message';
import { ref, computed } from 'vue';
import { Tag, Tooltip } from 'ant-design-vue';
const props = defineProps<{
    item: AgentConfig;
}>()

</script>

<style scoped>
.agent-list-item {
    display: flex;
    flex-direction: column;
    gap: 10px;
    border: 1px solid #ccc;
    border-radius: 5px;
    padding: 10px;
    margin-bottom: 10px;
}

.agent-list-item-header {
    display: flex;
    flex-direction: row;
    gap: 10px;
}

.agent-list-item-header-title {
    display: flex;
    flex-direction: row;
    gap: 10px;
    font-size: 16px;
    font-weight: bold;
}

.agent-list-item-header-transport {
    font-size: 12px;
    color: #ccc;
    align-self: flex-end;
}

.agent-list-item-header-status {
    font-size: 12px;
    align-self: flex-start;
    width: 10px;
    height: 10px;
    border-radius: 50%;
}

.agent-list-item-body {
    display: flex;
    flex-direction: column;
    gap: 10px;
}

.agent-list-item-body-description {
    font-size: 12px;
    color: #777;
}

.agent-list-item-body-prompt {
    font-size: 12px;
    color: #ccc;
}

.agent-list-item-body-hands-off {
    font-size: 12px;
    color: #ccc;
}

.agent-list-item-tools {
    display: flex;
    flex-direction: row;
    gap: 10px;
    flex-wrap: wrap;
}

.agent-list-item-tools-item {
    font-size: 12px;
    color: #ccc;
}
</style>
