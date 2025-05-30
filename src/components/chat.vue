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
    <div class="messages" ref="messagesRef">
      <Flex gap="middle" vertical>
        <BubbleList :roles="roles" :items="message2BubbleListItem()" />
      </Flex>
    </div>
    <Sender class="chat-sender" 
          @submit="sendMessage" 
          v-model:value="value"
          :footer="renderFooter"
          />
  </div>
</template>

<script setup lang="ts">
import { Flex, Input, Typography, Button, Switch } from 'ant-design-vue';
import { Sender, Bubble, BubbleList, Prompts } from 'ant-design-x-vue';
import type { BubbleProps, BubbleListProps } from 'ant-design-x-vue';
// import { onWatcherCleanup, ref, watch } from 'vue';
import { UserOutlined, EditOutlined, AndroidOutlined, QuestionCircleOutlined } from '@ant-design/icons-vue';
import type { CSSProperties } from 'vue';
import { h, ref, watch, nextTick, toRef } from 'vue';
import { PropType } from 'vue';
import { fetchEventData } from 'fetch-sse';
import markdownit from 'markdown-it';
import { v4 as uuidv4 } from 'uuid';
import { Message, SystemSettings, ChatHistory, Conversation } from '../types/message';
import ToolCall from './tool_call.vue';

const md = markdownit({ html: true, breaks: true });
const isEditing = ref(false)
const chatHeaderTitleInputRef = ref<HTMLInputElement>()
const messagesRef = ref<HTMLDivElement>();
const isAgent = ref(false)

const roles: BubbleListProps['roles'] = {
  assistant: {
    placement: 'start',
    avatar: { icon: h(UserOutlined), style: { background: '#fde3cf' } },
    messageRender: (content) =>
    h(Typography, null, {
      default: () => h('div', { innerHTML: md.render(content) }),
    }) 
  },
  waiting_for_input: {
    placement: 'start',
    avatar: { icon: h(QuestionCircleOutlined), style: { background: '#fde3cf' } },
    messageRender: (content) =>
    h(Typography, null, {
      default: () => h('div', { innerHTML: md.render(content) }),
    }) 
  },
  tool: {
    placement: 'start',
    avatar: { icon: h(UserOutlined), style: { background: '#fde3cf' } },
    messageRender: (content) =>{
      const tool_call = JSON.parse(content)[0]
      console.log("tool_call", tool_call)
      if (tool_call.name.startsWith('transfer_to_')) {
        return h(Typography, null, {
          default: () => h('div', { innerHTML: md.render("移交控制权给`" + tool_call.name.replace('transfer_to_', '') + "`") }),
        }) 
      }
      return h(ToolCall, {
      function_name: tool_call.name,
      function_args: tool_call.arguments,
      response: tool_call.response
    }) 
    }
  },
  user: {
    placement: 'end',
    avatar: { icon: h(UserOutlined), style: { background: '#fde3cf' } },
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

const renderFooter = (components) => {
  const { SendButton, LoadingButton, SpeechButton } = components;
  return h(Flex, { align: 'start', gap: 'middle' }, [
    h(Switch, {
      checked: isAgent.value,
      checkedChildren: 'Agent',
      unCheckedChildren: 'Chat',
      onChange: (checked) => {
        isAgent.value = !isAgent.value
      }
    })
  ])
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
    let chat_history = localConversation.value.messages.map(msg => ({
      role: msg.role === 'user' ? 'user' : 'assistant',
      content: msg.content
    }))
    // chat_history.unshift(props.system_message ? { role: 'system', content: props.system_message } : {})
    // 请求ollama的chat接口进行回复
    sendMessageToOllama(chat_history)
  }
}

const sendMessageToOllama = async (messages: ChatHistory[]) => {
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
  // 如果系统设置中存在系统提示词，则添加到messages中
  if (props.systemSettings?.assistantSettings.sysPrompt) {
    messages.unshift({
      role: 'system',
      content: props.systemSettings.assistantSettings.sysPrompt
    })
  }
  let req_path = isAgent.value ? '/api/agentic/chat' : '/api/chat'  
  if (localConversation.value.key === '') {
    localConversation.value.key = uuidv4().toString()
  }
  await fetchEventData(props.systemSettings!.serverUrl + req_path, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    data: {
      model: props.systemSettings!.assistantSettings.model,
      messages: messages,
      agents: JSON.parse(props.systemSettings!.assistantSettings.agents || '[]'),
      chat_id: localConversation.value.key,
      is_resume: localConversation.value.messages[localConversation.value.messages.length - 1].role === 'waiting_for_input',
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
    localConversation.value.updatedAt = new Date().getTime()
    if (localConversation.value.label === '新对话') {
      localConversation.value.label = localConversation.value.messages[0].content as string
    }
    props.onNewMessage(localConversation.value)
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
}

.messages {
  width: 100%;
  height: 100%;
  /* padding: 20px; */
  /* margin-top: 10px; */
  padding-left: 10%;
  padding-right: 10%;
  align-self: center;
  overflow-y: auto;
  overflow-x: hidden;
  /* 滚动条样式 */
  scrollbar-width: thin;
}

.message {
  margin-bottom: 10px;
}

.chat-sender {
  width: 80%;
  /* height: 100px; */
  align-self: center;
  margin-bottom: 20px;
  box-shadow: 0 0 10px 0 rgba(0, 0, 0, 0.1);
  border-radius: 10px;
  background-color: #fff;
}
.chat-header {
  /* width: 100%; */
  height: 50px;
  margin: 10px;
  border-radius: 10px;
  box-shadow: 0 0 10px 0 rgba(0, 0, 0, 0.1);
  background-color: rgba(255, 255, 255, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
}

.chat-header-title {
  font-size: 16px;
  font-weight: 500;
  color: #000;
  text-align: center;
}

.chat-header-actions {
  margin-left: 10px;
  margin-right: 10px;
}

.chat-header-title-input {
  width: 100%;
  height: 100%;
}
</style>