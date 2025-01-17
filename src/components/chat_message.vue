<template>
    <div>
        <div class="message-header">
            <span class="username">{{ username }}</span>
            <span class="timestamp">{{ timestamp }}</span>
        </div>
        <div class="chat-message" :class="{ 'chat-message-right': username === 'You' }">
            <div class="message-body">
                {{ message }}
            </div>
        </div>
    </div>
</template>

<script>
export default {
    name: 'ChatMessage',
    props: {
        username: {
            type: String,
            required: true
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
    }
}
</script>

<style scoped>
.chat-message {
    border: 1px solid #ccc;
    padding: 10px;
    margin: 10px 0;
    border-radius: 5px;
    display: flex;
    align-items: center;
    background-color: #f9f9f9;
}

.chat-message-right {
    flex-direction: row-reverse;
    background-color: #e0f7fa;
}

.message-header {
    display: flex;
    justify-content: space-between;
    font-size: 0.9em;
    color: #555;
    width: 100%;
}

.message-body {
    margin-top: 5px;
    font-size: 1em;
    flex: 1;
}

.avatar {
    width: 40px;
    height: 40px;
    border-radius: 50%;
    margin-right: 10px;
}

.chat-message-right .avatar {
    margin-left: 10px;
    margin-right: 0;
}
</style>