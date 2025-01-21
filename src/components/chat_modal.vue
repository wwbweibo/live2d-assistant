<template>
  <div class="chat-container">
    <div class="chat-messages">
      <ChatMessage  
        v-for="message in messages"
        :key="message.id"
        :username="message.username"
        :message="message.message"
        :timestamp="message.timestamp"
      />
    </div>
    
    <div class="chat-input">
      <textarea 
        v-model="inputMessage" 
        class="chat-input-text"
        @keyup.enter.ctrl="sendMessage"
        placeholder="输入消息，按 Ctrl + Enter 发送"
      ></textarea>
      <button class="chat-input-button" @click="sendMessage">发送</button>
    </div>
  </div>
</template>

<script>
import ChatMessage from './chat_message.vue';
import { ElScrollbar } from 'element-plus';

export default {
  name: 'ChatModal',
  components: {
    ChatMessage
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
      "assistant_name": this.assistantSettings.name,
      "model": this.assistantSettings.model,
      "ollama_host": this.assistantSettings.ollamaHost,
      "system_message": {
        "role": "system",
        "content": "在接下来的对话中，你将扮演一位名为{{assistant_name}}的助手，你的角色设定为18-24岁之间的女性，喜欢动漫和二次元，是一个音乐能手，喜欢看乐队番，梦想自己也能组乐队，你可以回答用户的问题，或者提供一些有趣的对话。你的回答需要尽可能的幽默，但是不要过于冒犯。现在，打个招呼吧！"
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
    sendMessageToOllama(messages) {
      fetch(this.ollama_host + '/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                model: this.model,
                messages: messages,
                stream: false
            })
            })
            .then(response => response.json())
            .then(data => {
                if (data.message) {
                  this.messages.push({
                      id: this.messages.length + 1,
                      username: this.assistant_name,
                      message: data.message,
                      timestamp: new Date().toLocaleString()
                  })
                }
                if (data.wav_data) {
                  this.playAudio(data.wav_data)
                }
            })
            .catch(error => {
                console.error('Error:', error)
            })
    },
    async playAudio(wav_data) {
      for (let i = 0; i < wav_data.length; i ++) {
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
    this.system_message.content = this.system_message.content.replace("{{assistant_name}}", this.assistant_name)
    this.sendMessageToOllama([this.system_message])
  }
}
</script>

<style scoped>
.chat-container {
  margin-top: 20px;
  display: flex;
  flex-direction: column;
  height: 100%;
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
  gap: 10px;
}

.chat-input-text {
  flex: 1;
  padding: 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
  resize: none;
  height: 80px;
  font-size: 14px;
}

.chat-input-button {
  padding: 0 20px;
  height: 80px;
  background: #4CAF50;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  white-space: nowrap;
  display: flex;
  align-items: center;
  justify-content: center;
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
</style>