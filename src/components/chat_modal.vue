<template>
  <div class="chat-container">
    <div class="chat-messages">
      <ChatMessage v-for="message in messages" 
        :key="message.id" 
        :username="message.username" 
        :message="message.message"
        :thinking="message.thinking"
        :timestamp="message.timestamp" />
      <div v-if="isLoading" class="loading-message">
        <div class="loading-dots">
          <span></span>
          <span></span>
          <span></span>
        </div>
      </div>
    </div>
    <div class="chat-input">
      <div class="chat-input-controls">
      </div>
      <div class="chat-input-text-container" :class="{ 'loading': isLoading }">
        <textarea v-model="inputMessage" class="chat-input-text" @keyup.enter.ctrl="sendMessage"
          placeholder="输入消息，按 Ctrl + Enter 发送" :disabled="isLoading"></textarea>
        <div class="chat-input-controls">
          <el-switch v-model="webSearchEnabled" class="web-search-switch" :active-action-icon="Search"
            :inactive-action-icon="Hide" />
        </div>
      </div>
      <button class="chat-input-button" @click="sendMessage" :disabled="isLoading">
        {{ isLoading ? '发送中...' : '发送' }}
      </button>
    </div>
  </div>
</template>

<script>
import ChatMessage from './chat_message.vue';
import { ElSwitch, ElInput, ElIcon, messageDefaults } from 'element-plus'
import { Hide, View, Search } from '@element-plus/icons-vue'
import 'element-plus/dist/index.css'
import { fetchEventData } from 'fetch-sse';
import { th } from 'element-plus/es/locales.mjs';

export default {
  name: 'ChatModal',
  components: {
    ChatMessage,
    ElSwitch,
    ElInput,
    ElIcon
  },
  props: {
    assistantSettings: {
      type: Object,
      required: true
    }
  },
  data() {
    return {
      messages: [],
      assistant_name: this.assistantSettings.name,
      model: this.assistantSettings.model,
      ollama_host: this.assistantSettings.ollamaHost,
      inputMessage: '',
      isLoading: false,
      webSearchEnabled: false,
      View,
      Hide,
      Search,
      system_message: {
        "role": "system",
        "content": "在接下来的对话中，你将扮演一位名为{{assistant_name}}的助手，你的角色设定为18-24岁之间的女性，喜欢动漫和二次元，是一个音乐能手，喜欢看乐队番，梦想自己也能组乐队，你可以回答用户的问题，或者提供一些有趣的对话。你的回答需要尽可能的幽默，但是不要过于冒犯，你的回答应该只包含你作为{{assistant_name}}的第一人称的回答，不要包含任何其他内容,特别是你对于对话的思考内容。现在，作为{{assistant_name}}，来打个招呼吧！"
      }
    }
  },
  methods: {
    sendMessage() {
      const input = document.querySelector('.chat-input-text');
      const message = input.value;
      if (message) {
        // 添加新消息
        this.messages.push({
          id: this.messages.length + 1,
          username: "You",
          message,
          timestamp: new Date().toLocaleString()
        })
        let chat_history = this.messages.map(msg => ({
          role: msg.username === 'You' ? 'user' : 'assistant',
          content: msg.message
        }))
        // 清空输入框
        this.inputMessage = ''
        chat_history.unshift(this.system_message)
        // 请求ollama的chat接口进行回复
        this.sendMessageToOllama(chat_history)
      }
    },
    async sendMessageToOllama(messages) {
      this.isLoading = true
      // 先往messages中添加一个loading的消息
      this.messages.push({
        id: this.messages.length + 1,
        username: this.assistant_name,
        thinking: '',
        message: '',
        timestamp: new Date().toLocaleString()
      })
      let message = ''
      let isThinking = false
      let thinking = ''
      await fetchEventData(this.ollama_host + '/api/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        data: {
          model: this.model,
          messages: messages,
          tts_enabled: this.assistantSettings.ttsEnabled,
          web_search: this.webSearchEnabled
        },
        onMessage: (event) => {
          this.isLoading = false
          console.log(event)
          const data = JSON.parse(event.data)
          if (data.type === 'text') {
            if (data.content === '<think>' || isThinking) {
              // 正在输出thinking的内容
              if (data.content === '</think>') {
                isThinking = false
                return
              }
              isThinking = true
              thinking = (thinking + data.content).replace('<think>', '').replace('</think>', '')
              this.messages[this.messages.length - 1].thinking = thinking
              return
            } else {
              message += data.content
              this.messages[this.messages.length - 1].message = message
            }
          } else if (data.type === 'audio' && this.assistantSettings.ttsEnabled) {
            this.playAudio([data.content])
          }
        }
      }).then(() => {
        this.isLoading = false
      }).catch((error) => {
        console.error('Error:', error)
        this.isLoading = false
      })
    },
    async playAudio(wav_data) {
      for (let i = 0; i < wav_data.length; i++) {
        // base64解码
        const binaryString = window.atob(wav_data[i]);
        const len = binaryString.length;
        const bytes = new Uint8Array(len);
        for (let i = 0; i < len; i++) {
          bytes[i] = binaryString.charCodeAt(i);
        }
        const audioContext = new AudioContext();
        const audioBuffer = await audioContext.decodeAudioData(bytes.buffer);
        const source = audioContext.createBufferSource();
        source.buffer = audioBuffer;
        source.connect(audioContext.destination);
        source.start();
        // 等待音频播放完毕
        await new Promise(resolve => {
          source.onended = resolve;
        });
      }
    }
  },
  mounted() {
    this.assistant_name = this.assistantSettings.name
    this.model = this.assistantSettings.model
    this.ollama_host = this.assistantSettings.ollamaHost
    if (this.assistantSettings.systemPrompt) {
      this.system_message.content = this.assistantSettings.systemPrompt.replace(/\{\{assistant_name\}\}/g, this.assistant_name)
    } else {
      this.system_message.content = this.system_message.content.replace(/\{\{assistant_name\}\}/g, this.assistant_name)
    }
    this.sendMessageToOllama([this.system_message])
  }
}
</script>

<style scoped>
.chat-container {
  margin-top: 20px;
  display: flex;
  flex-direction: column;
  height: 95%;
  box-sizing: border-box;
}

.chat-messages {
  overflow-y: auto;
  margin-bottom: 20px;
  height: calc(100% - 140px);
}

.message {
  margin-bottom: 15px;
  padding: 10px;
  border-radius: 8px;
  max-width: 80%;
  word-wrap: break-word;
}

.user-message {
  background-color: #e3f2fd;
  margin-left: auto;
  margin-right: 0;
}

.assistant-message {
  background-color: #f5f5f5;
  margin-right: auto;
  margin-left: 0;
}

.chat-input {
  display: flex;
  height: 140px;
  margin: 0 0 10px 0;
}

.chat-input-text-container {
  display: flex;
  flex-direction: column;
  width: 85%;
  border: 1px solid #e0e0e0;
  border-radius: 5px 0 0 5px;
  background-color: #FFFFFF;
  padding: 10px 0 0 10px;
}

.chat-input-text-container.loading {
  background-color: #f5f5f5;
}

.chat-input-text-container textarea {
  border: none;
  /* 仅用textarea 选中后的样式 */
  outline: none;
  resize: none;
}

.chat-input-controls {
  padding: 8px 0;
  display: flex;
  align-items: center;
}

.web-search-switch {
  margin: 0;
  padding: 0;
}

.chat-input-text {
  flex: 1;
  min-height: 80px;
}

.chat-input-button {
  padding: 0 20px;
  /* 高度继承 */
  height: inherit;
  background: #4CAF50;
  color: white;
  border: none;
  border-radius: 0 5px 5px 0;
  cursor: pointer;
  font-size: 14px;
  white-space: nowrap;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 15%;
}

.chat-input-button:hover {
  background: #45a049;
}

/* 自定义滚动条样式 */
.chat-messages::-webkit-scrollbar {
  width: 6px;
}

.chat-messages::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 3px;
}

.chat-messages::-webkit-scrollbar-thumb {
  background: #888;
  border-radius: 3px;
}

.chat-messages::-webkit-scrollbar-thumb:hover {
  background: #555;
}

.loading-message {
  padding: 10px;
  margin: 10px 0;
  display: flex;
  align-items: center;
  justify-content: flex-start;
}

.loading-dots {
  display: flex;
  gap: 4px;
}

.loading-dots span {
  width: 8px;
  height: 8px;
  background-color: #888;
  border-radius: 50%;
  display: inline-block;
  animation: bounce 1.4s infinite ease-in-out both;
}

.loading-dots span:nth-child(1) {
  animation-delay: -0.32s;
}

.loading-dots span:nth-child(2) {
  animation-delay: -0.16s;
}

@keyframes bounce {

  0%,
  80%,
  100% {
    transform: scale(0);
  }

  40% {
    transform: scale(1.0);
  }
}

.chat-input-button:disabled {
  background: #cccccc;
  cursor: not-allowed;
}

.chat-input-text:disabled {
  background: #f5f5f5;
  cursor: not-allowed;
}

/* 添加一些自定义样式来调整开关的位置和外观 */
:deep(.el-switch) {
  --el-switch-on-color: #4CAF50;
}

:deep(.el-switch__label) {
  color: #666;
  font-size: 13px;
}
</style>