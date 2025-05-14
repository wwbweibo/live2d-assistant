<template>
  <div class="chat-container">
    <div class="messages">
      <Flex gap="middle" vertical>
        <Bubble :placement="message.role === 'assistant' ? 'start' : 'end'"
          :avatar="{ icon: h(UserOutlined), style: fooAvatar }" 
          :header="message.role === 'assistant' ? systemSettings?.assistantSettings.assistantName : '用户'" 
          class="message"
          :content="message.content"
          :key="message.id"
          v-model:value="value"
          :loading="message.loading"
          v-for="message in localMessages"  />
      </Flex>
    </div>
    <!-- <div class="chat-sender"> -->
    <Sender class="chat-sender" @submit="sendMessage" v-model:value="value" />
    <!-- </div> -->
  </div>
</template>

<script setup lang="ts">
import { Flex } from 'ant-design-vue';
import { Sender, Bubble } from 'ant-design-x-vue';
// import { onWatcherCleanup, ref, watch } from 'vue';
import { UserOutlined } from '@ant-design/icons-vue';
import type { CSSProperties } from 'vue';
import { h, ref, watch } from 'vue';
import { PropType } from 'vue';
import { fetchEventData } from 'fetch-sse';

import { Message, SystemSettings, ChatHistory } from '../models/message.vue';
import { settings } from 'pixi.js';

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
  messages: {
    type: Array as PropType<Message[]>,
    required: false,
  },
  systemSettings: {
    type: Object as PropType<SystemSettings>,
    required: false,
  }
});

const value = ref('');
const localMessages = ref<Message[]>([...(props.messages || [])])

watch(() => props.messages, (newVal) => {
  if (newVal) localMessages.value = [...newVal]
})

const sendMessage = async () => {
  console.log('sendMessage')
  const message = value.value;
  value.value = ''
  if (message) {
    // 添加新消息
    localMessages.value.push({
      id: localMessages.value.length + 1,
      role: "user",
      content: message,
      timestamp: new Date().toLocaleString(),
      loading: false
    })
    let chat_history = localMessages.value.map(msg => ({
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
  localMessages.value.push({
    id: localMessages.value.length + 1,
    role: 'assistant',
    content: '',
    timestamp: new Date().toLocaleString(),
    loading: true
  })
  let message = ''
  let isThinking = false
  let thinking = ''
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
      console.log(event)
      localMessages.value[localMessages.value.length - 1].loading = false
      const data = JSON.parse(event!.data)
      if (data.type === 'text') {
        if (data.content === '<think>' || isThinking) {
          // 正在输出thinking的内容
          if (data.content === '</think>') {
            isThinking = false
            return
          }
          isThinking = true
          thinking = (thinking + data.content).replace('<think>', '').replace('</think>', '')
          localMessages.value[localMessages.value.length - 1].content = thinking
          return
        } else {
          message += data.content
          localMessages.value[localMessages.value.length - 1].content = message
        }
      }
    }
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
  width: 80%;
  height: 100%;
  align-self: center;
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