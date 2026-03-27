<template>
  <div class="chat-container">
    <div class="chat-header">
      <div class="chat-header-title">
        <span v-if="!isEditing">{{ localConversation.label }}</span>
        <Input class="chat-header-title-input" 
            v-model:value="localConversation.label" 
            v-if="isEditing" 
            @focusout="handleSaveConversationLabel"
            @keydown.enter="handleSaveConversationLabel" />
      </div>
      <div class="chat-header-actions">
        <EditOutlined @click="handleEditConversationLabel" ref="chatHeaderTitleInputRef" />
      </div>
    </div>
    
    <!-- 空状态或欢迎界面 -->
    <div v-if="localConversation.messages.length === 0" class="welcome-container">
      <div class="welcome-content">
        <div class="welcome-icon">
          <span class="welcome-icon-inner">✦</span>
        </div>
        <h2 class="welcome-title">{{ systemSettings?.assistantSettings.assistantName || 'AI助手' }}</h2>
        <p class="welcome-description">我是您的智能助手，可以帮助您解答问题、处理任务。开始对话吧！</p>
        <div class="welcome-suggestions">
          <div class="suggestion-item" @click="sendSuggestion('介绍一下你自己')">
            <UserOutlined />
            <span>介绍一下你自己</span>
          </div>
          <div class="suggestion-item" @click="sendSuggestion('你能帮我做什么？')">
            <QuestionCircleOutlined />
            <span>你能帮我做什么？</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 消息列表 -->
    <div class="messages" ref="messagesRef">
      <Flex gap="middle" vertical>
        <BubbleList :roles="roles" :items="message2BubbleListItem()" />
        
        <!-- 加载状态指示器 -->
        <div v-if="isMessageLoading" class="loading-indicator">
          <div class="loading-content">
            <div class="loading-dots">
              <span></span>
              <span></span>
              <span></span>
            </div>
            <span class="loading-text">{{ props.systemSettings?.assistantSettings.assistantName || 'AI助手' }} 正在思考...</span>
          </div>
        </div>
      </Flex>
    </div>

    <!-- 输入区域 -->
    <div class="chat-input-container">
      <Sender class="chat-sender" 
            @submit="sendMessage" 
            v-model:value="value"
            :footer="renderFooter"
            :placeholder="getInputPlaceholder()"
            />
    </div>
  </div>
</template>

<script setup lang="ts">
import { Flex, Input, Typography, Button, Switch } from 'ant-design-vue';
import { Sender, Bubble, BubbleList, Prompts } from 'ant-design-x-vue';
import type { BubbleProps, BubbleListProps } from 'ant-design-x-vue';
// import { onWatcherCleanup, ref, watch } from 'vue';
import { UserOutlined, EditOutlined, AndroidOutlined, QuestionCircleOutlined } from '@ant-design/icons-vue';
import type { CSSProperties } from 'vue';
import { computed } from 'vue';
import { h, ref, watch, nextTick, toRef } from 'vue';
import { PropType } from 'vue';
import { fetchEventData } from 'fetch-sse';
import markdownit from 'markdown-it';
import { v4 as uuidv4 } from 'uuid';
import { Message, SystemSettings, ChatHistory, Conversation } from '../types/message';
import { API_URL } from '../utils/api';

const md = markdownit({ html: true, breaks: true });
const isEditing = ref(false)
const chatHeaderTitleInputRef = ref<HTMLInputElement>()
const messagesRef = ref<HTMLDivElement>();

// 是否有配置 Agent：自动检测
const hasAgents = computed(() => {
  const raw = props.systemSettings?.assistantSettings.agents
  if (!raw) return false
  if (typeof raw === 'string') {
    try { return JSON.parse(raw).length > 0 } catch { return false }
  }
  return (raw as any[]).length > 0
})

const roles: BubbleListProps['roles'] = {
  assistant: {
    placement: 'start',
    avatar: { icon: h(AndroidOutlined), style: { background: 'linear-gradient(135deg, #6366f1, #a78bfa)', color: '#fff' } },
    messageRender: (content) =>
    h(Typography, null, {
      default: () => h('div', { innerHTML: md.render(content) }),
    }) 
  },
  waiting_for_input: {
    placement: 'start',
    avatar: { icon: h(QuestionCircleOutlined), style: { background: 'linear-gradient(135deg, #f472b6, #fbbf24)', color: '#fff' } },
    messageRender: (content) =>
    h(Typography, null, {
      default: () => h('div', { innerHTML: md.render(content) }),
    }) 
  },
  tool: {
    placement: 'start',
    avatar: { icon: h(AndroidOutlined), style: { background: 'linear-gradient(135deg, #06b6d4, #6366f1)', color: '#fff' } },
    messageRender: (content) =>{
      const tool_call = JSON.parse(content)[0]
      console.log("tool_call", tool_call)
      if (tool_call.name.startsWith('transfer_to_')) {
        return h(Typography, null, {
          default: () => h('div', { innerHTML: md.render("移交控制权给 `" + tool_call.name.replace('transfer_to_', '') + "`") }),
        })
      }
      // 内联显示工具调用
      return h(Typography, null, {
        default: () => h('div', {
          style: { padding: '8px 12px', background: '#f5f5f5', borderRadius: '8px', fontSize: '13px' },
          innerHTML: md.render("**工具调用**: `" + tool_call.name + "`\n\n**参数**:\n```json\n" + JSON.stringify(tool_call.arguments, null, 2) + "\n```")
        }),
      })
    }
  },
  user: {
    placement: 'end',
    avatar: { icon: h(UserOutlined), style: { background: 'linear-gradient(135deg, #34d399, #06b6d4)', color: '#fff' } },
  },
};

const message2BubbleListItem = () => {
  return localConversation.value.messages.map(msg => ({
    key: msg.id,
    role: msg.role,
    content: msg.content,
    timestamp: msg.timestamp,
    loading: msg.loading
  }))
} 

const renderFooter = () => null

// 获取输入框占位符文本
const getInputPlaceholder = () => {
  if (waiting_for_input.value) {
    return '请回答上面的问题...'
  }
  if (hasAgents.value) {
    return '请输入您的任务，我会调用相应的工具来帮助您...'
  }
  return `与 ${props.systemSettings?.assistantSettings.assistantName || 'AI助手'} 对话...`
}

// 发送建议消息
const sendSuggestion = (suggestion: string) => {
  value.value = suggestion
  sendMessage()
}

defineOptions();

// 定义组件参数
const props = defineProps({
  conversation: {
    type: Object as PropType<Conversation>,
    required: true,
  },
  onNewMessage: {
    type: Function as PropType<(conversation: Conversation) => void>,
    required: true,
  },
  systemSettings: {
    type: Object as PropType<SystemSettings>,
    required: false,
  }
});

const value = ref('');
const localConversation = ref<Conversation>(props.conversation)
const conversationRef = toRef(props, 'conversation')
const waiting_for_input = ref(false)
const isMessageLoading = ref(false)

const handleMessageChange = (newVal: Message[]) => {
  if (localConversation.value.key === "") {
    localConversation.value.messages = newVal
    localConversation.value.key = uuidv4().toString()
    localConversation.value.label = newVal[0].content
    localConversation.value.updatedAt = new Date().getTime()
    localConversation.value.createdAt = new Date().getTime()
  } else if (localConversation.value.label === '' || localConversation.value.label === '新对话') {
    localConversation.value.label = newVal[0].content
    localConversation.value.updatedAt = new Date().getTime()
    localConversation.value.createdAt = new Date().getTime()
  }
  props.onNewMessage(localConversation.value)
}

watch(conversationRef, async () => {
  localConversation.value = props.conversation
  console.log("conversationRef watch")
  await nextTick()
  if (messagesRef.value) {
    console.log("messagesRef.value scrollTo")
    console.log("messagesRef.value.scrollHeight", messagesRef.value.scrollHeight)
    messagesRef.value.scrollTo({
      top: messagesRef.value.scrollHeight,
      behavior: 'smooth'
    })
  }
})

watch(localConversation.value.messages, async () => {
  await nextTick()
  if (messagesRef.value) {
    console.log("localConversation.value.messages watch")
    messagesRef.value.scrollTo({
      top: messagesRef.value.scrollHeight,
      behavior: 'smooth'
    })
  }
})

const sendMessage = async () => {
  const message = value.value;
  value.value = ''
  if (message) {
    // 添加新消息
    localConversation.value.messages.push({
      id: localConversation.value.messages.length + 1,
      role: "user",
      content: message,
      timestamp: new Date().toLocaleString(),
      loading: false
    })
    handleMessageChange(localConversation.value.messages)
    sendMessageToServer(message)
  }
}

const sendMessageToServer = async (input_message: string) => {
  isMessageLoading.value = true
  const waiting_massage = {
    id: localConversation.value.messages.length + 1,
    role: 'assistant',
    content: '',
    timestamp: new Date().toLocaleString(),
    loading: true
  }
  let text_cache_message: Message|null = null
  // 先往messages中添加一个loading的消息
  localConversation.value.messages.push(waiting_massage)
  let waiting_removed = false
  let message = ''
  let isThinking = false
  let thinking = ''
  const req_path = '/api/agentic/chat'
  if (localConversation.value.key === '') {
    localConversation.value.key = uuidv4().toString()
  }
  await fetchEventData(API_URL + req_path, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    data: {
      message: input_message,
      chat_id: localConversation.value.key,
    },
    onMessage: (event) => {
      // this.isLoading = false
      const data = JSON.parse(event!.data)
      // 文本消息处理
      if (data.type === 'text' && data.content !== '') {
        if (!waiting_removed) {
          // waiting_massage is always last one, remove last message, then add a new assistant message
          localConversation.value.messages.pop()
          waiting_removed = true
          isMessageLoading.value = false
          localConversation.value.messages.push({
            id: localConversation.value.messages.length + 1,
            role: 'assistant',
            content: '',
            timestamp: new Date().toLocaleString(),
            loading: false
          })
        }
        let last_message = localConversation.value.messages[localConversation.value.messages.length - 1]
        if (last_message.role !== 'assistant') {
          // 如果last_message 不是assistant，添加一条新的assistant消息
          last_message = {
            id: localConversation.value.messages.length + 1,
            role: 'assistant',
            content: '',
            timestamp: new Date().toLocaleString(),
            loading: false
          }
          localConversation.value.messages.push(last_message)
        }
        if (data.content === '<think>' || isThinking) {          // 正在输出thinking的内容
          if (data.content === '</think>') {
            isThinking = false
            return
          }
          isThinking = true
          thinking = (thinking + data.content).replace('<think>', '').replace('</think>', '')
          last_message.content = thinking
          return
        } else {
          last_message.content += data.content
        }
        localConversation.value.messages = [...localConversation.value.messages]
      } else if (data.type === 'tool_calls' && data.content !== '') {
        if (!waiting_removed) {
          localConversation.value.messages.pop()
          waiting_removed = true
          isMessageLoading.value = false
        }
        // 特殊处理 request_user_input 工具调用
        if (data.content.some(c => c.name === 'request_user_input')) {
          // 添加一条assistant消息，内容为等待用户输入
          let tc = data.content.find(c => c.name === 'request_user_input')
          if (tc) {
          localConversation.value.messages.push({
            id: localConversation.value.messages.length + 1,
            role: 'waiting_for_input',
            content: tc.arguments.prompt,
            timestamp: new Date().toLocaleString(),
            loading: false
          })
          waiting_for_input.value = true
          // 移除该工具调用
          data.content = data.content.filter(c => c.name !== 'request_user_input')
          }
        }
        if (data.content.length > 0) {
        const content = JSON.stringify(data.content)
        const message = {
          id: localConversation.value.messages.length + 1,
          role: 'tool',
          content: content,
          timestamp: new Date().toLocaleString(),
          loading: false
        }
        localConversation.value.messages.push(message)
      }
      }
    }
  }).then(() => {
    isMessageLoading.value = false
    localConversation.value.updatedAt = new Date().getTime()
    if (localConversation.value.label === '新对话') {
      localConversation.value.label = localConversation.value.messages[0].content as string
    }
    props.onNewMessage(localConversation.value)
  }).catch(() => {
    isMessageLoading.value = false
  })
}

const handleEditConversationLabel = () => {
  isEditing.value = true
  nextTick(() => {
    chatHeaderTitleInputRef.value?.focus()
  })
}

const handleSaveConversationLabel = () => {
  isEditing.value = false
  // localConversation.value.label = chatHeaderTitleInputRef.value?.value as string
  props.onNewMessage(localConversation.value)
}

// async playAudio(wav_data) {
//   for (let i = 0; i < wav_data.length; i++) {
//     // base64解码
//     const binaryString = window.atob(wav_data[i]);
//     const len = binaryString.length;
//     const bytes = new Uint8Array(len);
//     for (let i = 0; i < len; i++) {
//       bytes[i] = binaryString.charCodeAt(i);
//     }
//     const audioContext = new AudioContext();
//     const audioBuffer = await audioContext.decodeAudioData(bytes.buffer);
//     const source = audioContext.createBufferSource();
//     source.buffer = audioBuffer;
//     source.connect(audioContext.destination);
//     source.start();
//     // 等待音频播放完毕
//     await new Promise(resolve => {
//       source.onended = resolve;
//     });
//   }
// }

</script>

<style scoped>
.chat-container {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  background: transparent;
}

/* ─── 消息列表 ──────────────────────────────────── */
.messages {
  width: 100%;
  height: 100%;
  padding: var(--space-lg) 10%;
  align-self: center;
  overflow-y: auto;
  overflow-x: hidden;
  scrollbar-width: thin;
  background: rgba(255, 255, 255, 0.3);
}
.messages::-webkit-scrollbar { width: 4px; }
.messages::-webkit-scrollbar-thumb {
  background: rgba(0, 0, 0, 0.12);
  border-radius: 10px;
}

.message {
  margin-bottom: var(--space-md);
  animation: fadeInUp var(--duration-normal) var(--ease-out) both;
}

/* ─── 聊天头部 ───────────────────────────────────── */
.chat-header {
  height: 56px;
  margin: var(--space-sm) var(--space-md);
  padding: 0 var(--space-md);
  border-radius: var(--radius-xl);
  background: rgba(255, 255, 255, 0.92);
  backdrop-filter: blur(var(--blur-amount)) saturate(180%);
  -webkit-backdrop-filter: blur(var(--blur-amount)) saturate(180%);
  border: 1px solid var(--glass-border);
  box-shadow: var(--glass-shadow-sm);
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all var(--duration-normal) var(--ease-out);
  position: relative;
  overflow: hidden;
}
.chat-header::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 10%;
  right: 10%;
  height: 1px;
  background: linear-gradient(90deg, transparent, rgba(var(--color-primary-rgb), 0.3), transparent);
}
.chat-header:hover {
  box-shadow: var(--glass-shadow-md), 0 0 0 1px rgba(var(--color-primary-rgb), 0.10);
}

.chat-header-title {
  font-size: 15px;
  font-weight: 500;
  color: var(--text-primary);
  text-align: center;
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.chat-header-actions {
  margin-left: var(--space-sm);
  cursor: pointer;
  color: var(--text-secondary);
  transition: color var(--duration-fast) var(--ease-out);
  display: flex;
  align-items: center;
}
.chat-header-actions:hover {
  color: var(--color-primary);
}

.chat-header-title-input {
  width: 100%;
  height: 100%;
  border-radius: var(--radius-sm);
  border: 1px solid rgba(0, 0, 0, 0.10);
  padding: var(--space-xs) var(--space-sm);
  font-family: var(--font-sans);
  font-size: 15px;
  outline: none;
  background: rgba(255, 255, 255, 0.9);
  transition: all var(--duration-fast) var(--ease-out);
}
.chat-header-title-input:focus {
  border-color: var(--color-primary);
  box-shadow: 0 0 0 3px rgba(var(--color-primary-rgb), 0.12);
}

/* ─── 欢迎页 ─────────────────────────────────────── */
.welcome-container {
  flex: 1;
  display: flex;
  justify-content: center;
  align-items: center;
  padding: var(--space-2xl) var(--space-lg);
  min-height: 400px;
}

.welcome-content {
  text-align: center;
  max-width: 540px;
  animation: fadeInUp var(--duration-slow) var(--ease-out) both;
}

.welcome-icon {
  width: 88px;
  height: 88px;
  border-radius: var(--radius-2xl);
  background: var(--gradient-aurora);
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto var(--space-lg);
  position: relative;
  animation: float 3s ease-in-out infinite;
  box-shadow: 0 8px 32px rgba(var(--color-primary-rgb), 0.30),
              0 0 60px rgba(var(--color-primary-rgb), 0.15);
}
.welcome-icon::after {
  content: '';
  position: absolute;
  inset: -4px;
  border-radius: inherit;
  background: var(--gradient-aurora);
  opacity: 0.3;
  filter: blur(16px);
  z-index: -1;
  animation: glow-pulse 3s ease-in-out infinite;
}

.welcome-icon-inner {
  font-size: 40px;
  color: #fff;
}

.welcome-title {
  font-size: 30px;
  font-weight: 800;
  margin-bottom: var(--space-sm);
  background: var(--gradient-aurora);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  letter-spacing: -0.02em;
  background-size: 200% 200%;
  animation: gradient-shift 4s ease infinite;
}

.welcome-description {
  font-size: 15px;
  color: var(--text-secondary);
  margin-bottom: var(--space-xl);
  line-height: 1.8;
}

.welcome-suggestions {
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
  max-width: 360px;
  margin: 0 auto;
}

.suggestion-item {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  padding: var(--space-md) var(--space-lg);
  border-radius: var(--radius-lg);
  background: var(--glass-bg);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  border: 1px solid var(--glass-border);
  box-shadow: var(--glass-shadow-sm);
  cursor: pointer;
  color: var(--text-primary);
  font-size: 14px;
  font-weight: 500;
  transition: all var(--duration-normal) var(--ease-out);
  text-align: left;
  position: relative;
  overflow: hidden;
}
.suggestion-item::before {
  content: '';
  position: absolute;
  inset: 0;
  background: var(--gradient-primary);
  opacity: 0;
  transition: opacity var(--duration-normal) var(--ease-out);
}
.suggestion-item:hover {
  border-color: var(--color-primary-border);
  transform: translateY(-3px);
  box-shadow: 0 8px 24px rgba(var(--color-primary-rgb), 0.20);
}
.suggestion-item:hover::before {
  opacity: 0.06;
}
.suggestion-item:active {
  transform: translateY(0);
}
.suggestion-item i,
.suggestion-item :deep(.anticon) {
  font-size: 16px;
  color: var(--color-primary);
  flex-shrink: 0;
  position: relative;
  z-index: 1;
}
.suggestion-item span {
  position: relative;
  z-index: 1;
}

/* ─── 输入区 ─────────────────────────────────────── */
.chat-input-container {
  width: 100%;
  padding: var(--space-sm) var(--space-md) var(--space-md);
  background: linear-gradient(to top, rgba(255,255,255,1) 40%, rgba(255,255,255,0.85) 80%, transparent);
}

.chat-sender {
  align-self: center;
  border-radius: var(--radius-2xl) !important;
  background: rgba(255, 255, 255, 0.95) !important;
  backdrop-filter: blur(var(--blur-amount)) saturate(180%);
  -webkit-backdrop-filter: blur(var(--blur-amount)) saturate(180%);
  border: 1px solid rgba(var(--color-primary-rgb), 0.12) !important;
  box-shadow: var(--glass-shadow-md), 0 0 0 1px rgba(var(--color-primary-rgb), 0.05) !important;
  transition: all var(--duration-normal) var(--ease-out) !important;
  overflow: hidden;
}
.chat-sender:hover,
.chat-sender:focus-within {
  border-color: rgba(var(--color-primary-rgb), 0.25) !important;
  box-shadow: var(--glass-shadow), 0 0 30px rgba(var(--color-primary-rgb), 0.08) !important;
}

/* ─── 加载动画 ─────────────────────────────────── */
.loading-indicator {
  display: flex;
  justify-content: center;
  align-items: center;
  padding: var(--space-md);
  animation: fadeIn var(--duration-normal) var(--ease-out);
}

.loading-content {
  text-align: center;
  max-width: 400px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-sm);
}

.loading-dots {
  display: flex;
  gap: 8px;
  justify-content: center;
}

.loading-dots span {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--gradient-primary);
  animation: dot-bounce 1.4s infinite both;
}

.loading-dots span:nth-child(1) { animation-delay: -0.32s; }
.loading-dots span:nth-child(2) { animation-delay: -0.16s; }
.loading-dots span:nth-child(3) { animation-delay: 0s; }

.loading-text {
  font-size: 14px;
  font-weight: 500;
  color: var(--text-secondary);
  margin-top: var(--space-sm);
}

@keyframes fadeInUp {
  from { opacity: 0; transform: translateY(14px); }
  to { opacity: 1; transform: translateY(0); }
}
</style>
