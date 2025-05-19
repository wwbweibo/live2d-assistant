<template>
  <div class="chat-container">
    <div class="messages" ref="messagesRef">
      <Flex gap="middle" vertical>
        <Bubble :placement="message.role === 'assistant' ? 'start' : 'end'"
          :avatar="{ icon: h(UserOutlined), style: fooAvatar }" 
          :header="message.role === 'assistant' ? systemSettings?.assistantSettings.assistantName : '用户'" 
          class="message"
          :content="message.content"
          :key="message.id"
          :messageRender="renderMarkdown"
          v-model:value="value"
          :loading="message.loading"
          v-for="message in localConversation.messages"  />
      </Flex>
    </div>
    <!-- <div class="chat-sender"> -->
    <Sender class="chat-sender" @submit="sendMessage" v-model:value="value" />
    <!-- </div> -->
  </div>
</template>

<script setup lang="ts">
import { Flex, Typography } from 'ant-design-vue';
import { Sender, Bubble } from 'ant-design-x-vue';
import type { BubbleProps } from 'ant-design-x-vue';
// import { onWatcherCleanup, ref, watch } from 'vue';
import { UserOutlined } from '@ant-design/icons-vue';
import type { CSSProperties } from 'vue';
import { h, ref, watch, nextTick, toRef } from 'vue';
import { PropType } from 'vue';
import { fetchEventData } from 'fetch-sse';
import markdownit from 'markdown-it';
import { v4 as uuidv4 } from 'uuid';
import { Message, SystemSettings, ChatHistory, Conversation } from '../types/message';


const md = markdownit({ html: true, breaks: true });

const renderMarkdown: BubbleProps['messageRender'] = (content) =>
h(Typography, null, {
  default: () => h('div', { innerHTML: md.render(content) }),
});

const messagesRef = ref<HTMLDivElement>();

const fooAvatar: CSSProperties = {
  color: '#f56a00',
  backgroundColor: '#fde3cf',
};

const barAvatar: CSSProperties = {
  color: '#fff',
  backgroundColor: '#87d068',
};

const hideAvatar: CSSProperties = {
  visibility: 'hidden',
};

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
  }
  console.log('localConversation', localConversation.value)
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
  // 先往messages中添加一个loading的消息
  localConversation.value.messages.push({
    id: localConversation.value.messages.length + 1,
    role: 'assistant',
    content: '',
    timestamp: new Date().toLocaleString(),
    loading: true
  })
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
      if (data.type === 'text') {
        if (data.content === '<think>' || isThinking) {          // 正在输出thinking的内容
          if (data.content === '</think>') {
            isThinking = false
            return
          }
          isThinking = true
          thinking = (thinking + data.content).replace('<think>', '').replace('</think>', '')
          localConversation.value.messages[localConversation.value.messages.length - 1].content = thinking
          return
        } else {
          message += data.content
          localConversation.value.messages[localConversation.value.messages.length - 1].content = message
        }
        if (localConversation.value.messages[localConversation.value.messages.length - 1].content.length > 0) {
          localConversation.value.messages[localConversation.value.messages.length - 1].loading = false
        }
      }
    }
  }).then(() => {
    props.onNewMessage(localConversation.value)
  })
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
</style>