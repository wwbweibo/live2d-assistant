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
        <!-- <Bubble :placement="message.role === 'assistant' ? 'start' : 'end'"
          :avatar="{ icon: h(UserOutlined), style: fooAvatar }" 
          :header="message.role === 'assistant' ? systemSettings?.assistantSettings.assistantName : '用户'" 
          class="message"
          :content="message.content"
          :key="message.id"
          :messageRender="renderMarkdown"
          v-model:value="value"
          :loading="message.loading"
          v-for="message in localConversation.messages"  /> -->
      </Flex>
    </div>
    <!-- <div class="chat-sender"> -->
    <Sender class="chat-sender" @submit="sendMessage" v-model:value="value" />
    <!-- </div> -->
  </div>
</template>

<script setup lang="ts">
import { Flex, Input, Typography } from 'ant-design-vue';
import { Sender, Bubble, BubbleList, Prompts } from 'ant-design-x-vue';
import type { BubbleProps, BubbleListProps } from 'ant-design-x-vue';
// import { onWatcherCleanup, ref, watch } from 'vue';
import { UserOutlined, EditOutlined } from '@ant-design/icons-vue';
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

// const renderMarkdown: BubbleProps['messageRender'] = (content) =>
// h(Typography, null, {
//   default: () => h('div', { innerHTML: md.render(content) }),
// });

const roles: BubbleListProps['roles'] = {
  assistant: {
    placement: 'start',
    avatar: { icon: h(UserOutlined), style: { background: '#fde3cf' } },
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
  await fetchEventData(props.systemSettings!.serverUrl + '/api/chat', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    data: {
      model: props.systemSettings!.assistantSettings.model,
      messages: messages,
      // tts_enabled: this.assistantSettings.ttsEnabled,
      // web_search: this.webSearchEnabled
    },
    onMessage: (event) => {
      // this.isLoading = false
      const data = JSON.parse(event!.data)
      // 文本消息处理
      if (data.type === 'text' && data.content !== '') {
        if (!waiting_removed) {
          // waiting_massage is always last one, remove last message
          localConversation.value.messages.pop()
          waiting_removed = true
        }
        if (text_cache_message === null) {
          text_cache_message = {
            id: localConversation.value.messages.length + 1,
            role: 'assistant',
            content: '',
            timestamp: new Date().toLocaleString(),
            loading: false
          }
          localConversation.value.messages.push(text_cache_message)
        }
        if (data.content === '<think>' || isThinking) {          // 正在输出thinking的内容
          if (data.content === '</think>') {
            isThinking = false
            return
          }
          isThinking = true
          thinking = (thinking + data.content).replace('<think>', '').replace('</think>', '')
          text_cache_message.content = thinking
          return
        } else {
          message += data.content
          text_cache_message.content = message
        }
        localConversation.value.messages = [...localConversation.value.messages]
      } else if (data.type === 'tool_calls' && data.content !== '') {
        if (!waiting_removed) {
          localConversation.value.messages.pop()
          waiting_removed = true
        }
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