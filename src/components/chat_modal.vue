<template>
    <div class="chat-content" ref="chatContent">
        <h3>聊天</h3>
        <div class="chat-messages">
            <el-scrollbar wrap-class="scrollbar-wrapper">
                <ChatMessage
                    v-for="message in messages"
                    :key="message.id"
                    :username="message.username"
                    :message="message.message"
                    :timestamp="message.timestamp"
                />
            </el-scrollbar>
        </div>
        <div class="chat-input">
            <textarea class="chat-input-text" rows="10" placeholder="输入消息" @keydown.enter="sendMessage" ></textarea>
            <button class="chat-input-button" @click="sendMessage">发送</button>
        </div>
    </div>
</template>

<script>
import ChatMessage from './chat_message.vue';

export default {
  name: 'ChatModal',
  components: {
    ChatMessage
  },
  data() {
    return {
      messages: [
        {
          id: 1,
          username: "Senko",
          message: "你好，我是Senko，有什么可以帮助你的吗？",
          timestamp: new Date().toLocaleString()
        }
      ],
      "assistant_name": "Senko",
      "model": "qwen2.5",
      "ollama_host": "http://localhost:11434",
      "system_message": {
        "role": "system",
        "content": "在接下来的对话中，你将扮演一位名为{{assistant_name}}的助手，你的角色设定为18-24岁之间的女性，喜欢动漫和二次元，是一个音乐能手，喜欢看乐队番，梦想自己也能组乐队，你可以回答用户的问题，或者提供一些有趣的对话。你的回答需要尽可能的幽默，但是不要过于冒犯。"
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
            input.value = ''
            let chat_history = this.messages.map(msg => ({
                    role: msg.username === 'You' ? 'user' : 'assistant',
                    content: msg.message
                }))
            // 在chat_history中添加系统消息
            let sys_msg = this.system_message
            sys_msg.content = sys_msg.content.replace("{{assistant_name}}", this.assistant_name)
            chat_history.unshift(sys_msg)
            // 请求ollama的chat接口进行回复
            fetch(this.ollama_host + '/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                model: this.model,
                messages: chat_history,
                stream: false
            })
            })
            .then(response => response.json())
            .then(data => {
                if (data.message.content) {
                this.messages.push({
                    id: this.messages.length + 1,
                    username: "Senko",
                    message: data.message.content,
                    timestamp: new Date().toLocaleString()
                })
                }
            })
            .catch(error => {
                console.error('Error:', error)
            })
        }
    }
  }
}
</script>

<style scoped>
.chat-content {
  height: 100%;
  display: flex;
  flex-direction: column;
  gap: 20px;
  margin-top: 60px;
}

.chat-input {
  display: flex;
  gap: 10px;
  align-items: flex-start;
  width: -webkit-fill-available;
  padding-right: 10px;
  font-family: '微软雅黑', sans-serif;
  flex-direction: row;
  height: 200px;
}

.chat-input-text {
  flex: 1;
  padding: 8px;
  border: 1px solid #ddd;
  border-radius: 4px;
  resize: none;
  height: 100px;
  font-size: 20px;
  font-family: '微软雅黑', Arial, sans-serif;
}

.chat-input-button {
  padding: 8px 16px;
  background: #4CAF50;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  height: 100px;
  width: 80px;
  display: flex;
  align-items: center;
  justify-content: center;
  white-space: nowrap;
}

.chat-input-button:hover {
  background: #45a049;
}

.chat-messages {
  display: flex;
  flex-direction: column;
  height: calc(100% - 200px);
}
</style>