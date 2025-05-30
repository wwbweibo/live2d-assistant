<template>
    <div class="message-container">
        <div class="message-header">
            <div class="user-info">
                <img :src="avatar" :alt="username" class="avatar" />
                <span class="username">{{ username }}</span>
            </div>
            <span class="timestamp">{{ timestamp }}</span>
        </div>
        <!-- 需要在这里处理 thinking 的展示，考虑使用 一个可折叠的组件 -->
        <el-collapse v-model="thinking_title" accordion class="thinking-collapse" v-if="hasThinking">
            <el-collapse-item name="thinking" title="正在思考...">
                <div class="thinking-content">
                    <div class="thinking-dots" v-if="isThinking">
                        <span></span>
                        <span></span>
                        <span></span>
                    </div>
                    {{ thinking }}
                </div>
            </el-collapse-item>
        </el-collapse>
        <div class="chat-message" :class="{ 'chat-message-right': username === 'You' }">
            <div class="message-body">
                {{ message }}
            </div>
        </div>
    </div>
</template>

<script>
import { ElCollapse, ElCollapseItem } from 'element-plus'
import 'element-plus/dist/index.css'

export default {
    name: 'ChatMessage',
    props: {
        username: {
            type: String,
            required: true
        },
        thinking: {
            type: String,
            required: false,
            default: ''
        },
        message: {
            type: String,
            required: true
        },
        timestamp: {
            type: String,
            required: true
        },
        avatar: {
            type: String,
            required: false,
            default: 'https://via.placeholder.com/40'
        }
    },
    computed: {
        isThinking() {
            return this.thinking && this.thinking.length > 0 && this.message.length === 0
        },
        hasThinking() {
            return this.thinking && this.thinking.length > 0
        },
        thinkingTitle() {
            return this.isThinking ? '正在思考' : this.hasThinking ? '思考结果' : ''
        }
    },
    data() {
        return {
            thinking_title: 'thinking'
        }
    }
}
</script>

<style scoped>
.message-container {
    margin: 15px 0;
    animation: fadeIn 0.3s ease-in-out;
}

@keyframes fadeIn {
    from { opacity: 0; transform: translateY(10px); }
    to { opacity: 1; transform: translateY(0); }
}

.chat-message {
    border: none;
    padding: 12px 16px;
    margin: 8px 0;
    border-radius: 12px;
    display: flex;
    align-items: flex-start;
    background-color: #f0f2f5;
    box-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
    max-width: 80%;
    position: relative;
}

.chat-message-right {
    flex-direction: row-reverse;
    background-color: #e3f2fd;
    margin-left: auto;
}

.message-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: 0.9em;
    color: #666;
    margin-bottom: 4px;
}

.user-info {
    display: flex;
    align-items: center;
    gap: 8px;
}

.message-body {
    margin: 0;
    font-size: 1em;
    line-height: 1.5;
    word-break: break-word;
}

.avatar {
    width: 32px;
    height: 32px;
    border-radius: 50%;
    object-fit: cover;
    border: 2px solid #fff;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.thinking-collapse {
    background-color: #f8f9fa;
    border-radius: 12px;
    margin: 8px 0;
    overflow: hidden;
}

.thinking-content {
    padding: 12px;
    display: flex;
    align-items: center;
    gap: 8px;
}

.thinking-dots {
    display: flex;
    gap: 4px;
}

.thinking-dots span {
    width: 8px;
    height: 8px;
    background-color: #90caf9;
    border-radius: 50%;
    animation: bounce 1.4s infinite ease-in-out;
}

.thinking-dots span:nth-child(1) { animation-delay: -0.32s; }
.thinking-dots span:nth-child(2) { animation-delay: -0.16s; }

@keyframes bounce {
    0%, 80%, 100% { transform: scale(0); }
    40% { transform: scale(1); }
}

.timestamp {
    font-size: 0.8em;
    color: #999;
}
</style>