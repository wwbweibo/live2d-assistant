<template>
  <div class="home">
    <canvas ref="live2dCanvas"></canvas>
    
    <!-- 移动端菜单切换按钮 -->
    <div class="mobile-menu-toggle" @click="toggleSidebar" v-if="isMobile">
      <div class="hamburger" :class="{ active: sidebarVisible }">
        <span></span>
        <span></span>
        <span></span>
      </div>
    </div>
    
    <div class="ai-assistant-overlay">
      <!-- 侧边栏遮罩层（移动端） -->
      <div v-if="isMobile && sidebarVisible" class="sidebar-overlay" @click="closeSidebar"></div>
      
      <div class="ai-assistant-container-left" :class="{ 
        'mobile-hidden': isMobile && !sidebarVisible,
        'mobile-visible': isMobile && sidebarVisible 
      }">
        <div class="assistant-title">
          <div class="assistant-title-text">
            AI助手
          </div>
          <!-- 桌面端折叠按钮 -->
          <div v-if="!isMobile" class="sidebar-collapse-btn" @click="toggleSidebar">
            <i class="fas" :class="sidebarCollapsed ? 'fa-expand' : 'fa-compress'"></i>
          </div>
        </div>
        <div class="conversation-list">
          <div class="conversation-new-button" @click="handleNewConversation">
            <div class="conversation-new-button-icon">
              <FormOutlined />
            </div>
            <div class="conversation-new-button-text" v-if="!sidebarCollapsed">
              新对话
            </div>
          </div>
          <Conversations 
          :items="conversationItems" 
          :active-key="selectedConversationKey"
          :on-active-change="onSelectedConversationChange"
          :menu="menuConfig"
          :groupable="groupable" />
        </div>
        <!-- 分割线 -->
        <div class="assistant-setting-divider"></div>
        <div class="assistant-setting">
          <div class="assistant-setting-item" @click="showSettings = true">
            <div class="assistant-setting-item-icon">
              <SettingOutlined />
            </div>
          </div>
          <div class="assistant-setting-item" @click="showKnowledgeBase = true">
            <div class="assistant-setting-item-icon">
              <BookOutlined />
            </div>
          </div>
        </div>
      </div>
      <div class="ai-assistant-container-right">
        <ChatPage :systemSettings="systemSettings" :onNewMessage="handleNewMessage" :conversation="currentConversation" />
      </div>
    </div>
    <a-modal :open="showSettings" @cancel="showSettings = false" title="设置" @ok="saveSettings" :width="800">
      <SettingModal :settings="systemSettings" :updateSettings="handleSystemSettingsUpdate" />
    </a-modal>
    <a-modal :open="showKnowledgeBase" @cancel="showKnowledgeBase = false" title="知识库" :width="800">
      <KnowledgeBaseModal />
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, reactive } from 'vue'
import { FormOutlined, BookOutlined, SettingOutlined } from '@ant-design/icons-vue'
import * as PIXI from 'pixi.js'
import { Live2DModel as Live2DModelCubism4, MotionPreloadStrategy } from 'pixi-live2d-display/cubism4'
import { Live2DModel as Live2DModelCubism2 } from 'pixi-live2d-display/cubism2'
import { Conversations } from 'ant-design-x-vue'
import type { ConversationsProps } from 'ant-design-x-vue'
import { h } from 'vue'
import { Modal as AModal, Button as AButton, message, Space } from 'ant-design-vue'
import SettingModal from '../components/setting_modal.vue'
import KnowledgeBaseModal from '../components/knowledge_base_modal.vue'
import ChatPage from '../components/chat.vue'
import { SystemSettings, Conversation } from '../types/message'
import { updateConfig } from '../utils/requests'
import { v4 as uuidv4 } from 'uuid'
import { CommentOutlined, DeleteOutlined } from '@ant-design/icons-vue'

// 注册 Ticker
Live2DModelCubism4.registerTicker(PIXI.Ticker)
Live2DModelCubism2.registerTicker(PIXI.Ticker)

const live2dCanvas = ref<HTMLCanvasElement | null>(null)
let app: PIXI.Application | null = null
let model: any = null
const showSettings = ref(false)
const showKnowledgeBase = ref(false)


// 响应式侧边栏状态
const sidebarVisible = ref(true)
const sidebarCollapsed = ref(false)
const isMobile = ref(false)

const STORAGE_KEY = 'live2d-viewer-settings'
const STORAGE_KEY_CONVERSATIONS = 'live2d-viewer-conversations'
const conversationItems = ref<Conversation[]>([])
const currentConversation = ref<Conversation>({
  key: '',
  label: '新对话',
  messages: [],
  createdAt: 0,
  updatedAt: 0,
  group: undefined
})
const selectedConversationKey = ref<string>(currentConversation.value.key)

const systemSettings = reactive<SystemSettings>({
  serverUrl: 'http://localhost:8000',
  backgroundPath: 'assets/background.jpg',
  assistantSettings: {
    assistantName: 'Senko',
    sysPrompt: undefined,
    model: 'qwen2.5',
    apiKey: undefined,
    baseUrl: undefined,
    mcpServers: '',
    agents: '',
  },
  live2DSettings: {
    modelPath: 'assets/models/Senko_Normals/senko.model3.json',
    offsetX: 0,
    offsetY: 0,
    scale: 0.5,
    themeColor: 'rgba(255, 255, 255, 0.8)'
  }
})

// 处理对话列表分组
const groupable: ConversationsProps['groupable'] = {
  sort(a, b) {
    console.log('sort', a, b)
    if (a === b) return 0;
    return a === 'Today' ? -1 : 1;
  },
  title: (group, { components: { GroupTitle } }) =>
    group ? h(
      GroupTitle,
      null,
      () => [h(Space, null, () => [h(CommentOutlined), h('span', null, group)])]
    ) : h(GroupTitle),
};

// 处理对话列表菜单
const menuConfig: ConversationsProps['menu'] = (conversation) => ({
  items: [
    {
      label: '删除',
      key: 'delete',
      icon: h(DeleteOutlined),
      danger: true,
    },
  ],
  onClick: (menuInfo) => {
    if (menuInfo.key === 'delete') {
      conversationItems.value = conversationItems.value.filter(item => item.key !== conversation.key)
      localStorage.setItem(STORAGE_KEY_CONVERSATIONS, JSON.stringify({
        conversationItems: conversationItems.value
      }))
    }
  },
});

// 保存设置到 localStorage
const saveSettings = () => {
  localStorage.setItem(STORAGE_KEY, JSON.stringify({
    systemSettings
  }))
  message.success('设置已保存')
  showSettings.value = false
  updateConfig(systemSettings)
}

// 数据加载 
// 加载设置
const loadSettings = () => {
  const savedSettings = localStorage.getItem(STORAGE_KEY)
  if (savedSettings) {
    const parsed = JSON.parse(savedSettings)
    Object.assign(systemSettings, parsed.systemSettings)
  }
}

// 加载对话
const loadConversations = () => {
  const savedConversations = localStorage.getItem(STORAGE_KEY_CONVERSATIONS)
  if (savedConversations) {
    const parsed = JSON.parse(savedConversations)
    const conversations = parsed.conversationItems.map(item => {
      // 分组为 今天， 7天内， 30天内， 30天前
      const now = new Date().getTime()
      const today = new Date().setHours(0, 0, 0, 0)
      const diff = now - item.updatedAt
      if (item.updatedAt > today) {
        return {
          ...item,
          group: 'Today'
        }
      }
      if (diff <= 7 * 24 * 60 * 60 * 1000) {
        return {
          ...item,
          group: '7Days'
        }
      }
      if (diff <= 30 * 24 * 60 * 60 * 1000) {
        return {
          ...item,
          group: '30Days'
        }
      }
      return {
        ...item,
        group: '30DaysAgo'
      }
    })
    conversationItems.value = conversations
  }
}


const handleNewMessage = (conversation: Conversation) => {
  conversation.updatedAt = new Date().getTime()
  if (conversationItems.value.find(item => item.key === conversation.key)) {
    currentConversation.value = conversation
  } else {
    conversationItems.value.push(conversation)
    currentConversation.value = conversation
  }
  // write to localStorage
  localStorage.setItem(STORAGE_KEY_CONVERSATIONS, JSON.stringify({
    conversationItems: conversationItems.value
  }))
}

const handleSystemSettingsUpdate = (newSettings: SystemSettings) => {
  if (systemSettings.live2DSettings.modelPath !== newSettings.live2DSettings.modelPath) {
    updateModel()
  }
  updateBackground()
  updatePosition()
  updateScale()
  updateBackgroundOpacity()
  Object.assign(systemSettings, newSettings)
}

const handleNewConversation = () => {
  currentConversation.value = {
    key: uuidv4().toString(),
    label: '新对话',
    messages: [],
    createdAt: new Date().getTime(),
    updatedAt: new Date().getTime(),
    group: "Today"
  }
  selectedConversationKey.value = currentConversation.value.key
  conversationItems.value.push(currentConversation.value)
  localStorage.setItem(STORAGE_KEY_CONVERSATIONS, JSON.stringify({
    conversationItems: conversationItems.value
  }))
}

const onSelectedConversationChange = (key: string) => {
  selectedConversationKey.value = key
  currentConversation.value = conversationItems.value.find(item => item.key === key) || {
    key: '',
    label: '新对话',
    messages: [],
    createdAt: new Date().getTime(),
    updatedAt: new Date().getTime(),
    group: 'Today'
  }
}

// 更新模型位置
const updatePosition = () => {
  if (model && app) {
    const xOffset = (app.renderer.width * Number(systemSettings.live2DSettings.offsetX)) / 100
    const yOffset = (app.renderer.height * Number(systemSettings.live2DSettings.offsetY)) / 100
    model.x = app.renderer.width / 2 + xOffset
    model.y = app.renderer.height * 2 + yOffset
  }
}

// 更新模型缩放
const updateScale = () => {
  if (model) {
    model.scale.set(Number(systemSettings.live2DSettings.scale))
  }
}

// 更新背景
const updateBackground = () => {
  const homeElement = document.querySelector('.home') as HTMLElement
  if (homeElement) {
    homeElement.style.backgroundImage = `url('${systemSettings.backgroundPath}')`
  }
}

// 更新背景透明度
const updateBackgroundOpacity = () => {
  const homeElement = document.querySelector('.ai-assistant-container-right') as HTMLElement
  if (homeElement) {
    homeElement.style.backgroundColor = systemSettings.live2DSettings.themeColor
  }
}

// 更新模型
const updateModel = async () => {
  if (!app) return
  try {
    // 如果存在旧模型，先移除
    if (model) {
      app.stage.removeChild(model)
      model.destroy()
    }

    const isModel3 = systemSettings.live2DSettings.modelPath.endsWith('.model3.json')
    const ModelClass = isModel3 ? Live2DModelCubism4 : Live2DModelCubism2
    const motions = await fetch(systemSettings.live2DSettings.modelPath).
      then(async resp => {
        const content = await resp.json();
        if (content['FileReferences']['Motions'] !== undefined) {
          return content['FileReferences']['Motions']
        }
      })
    model = await ModelClass.from(systemSettings.live2DSettings.modelPath, {
      motionPreload: MotionPreloadStrategy.IDLE,
      autoInteract: false,
      autoUpdate: true,
    })
    if (motions) {
      // 添加交互，随机执行动作
      // motions 是一个对象，需要转换为数组
      let motionList: string[] = []
      for (const motion in motions) {
        motionList.push(motion)
      }
      model.interactive = true
      model.buttonMode = true
      model.on('pointerdown', () => {
        const randomMotion = motionList[Math.floor(Math.random() * motionList.length)]
        model.motion(randomMotion)
      })
    }

    if (model) {
      app.stage.addChild(model)
      model.anchor.set(0.5, 1.0)
      updatePosition()
      updateScale()
    }
  } catch (error) {
    console.error('模型加载失败:', error)
  }
}

// 响应式侧边栏函数
const toggleSidebar = () => {
  if (isMobile.value) {
    sidebarVisible.value = !sidebarVisible.value
  } else {
    sidebarCollapsed.value = !sidebarCollapsed.value
  }
}

const closeSidebar = () => {
  if (isMobile.value) {
    sidebarVisible.value = false
  }
}

// 检查屏幕尺寸
const checkScreenSize = () => {
  isMobile.value = window.innerWidth <= 768
  if (!isMobile.value) {
    sidebarVisible.value = true
  }
}

onMounted(async () => {
  loadSettings()
  updateBackground()
  updateConfig(systemSettings)
  loadConversations()

  // 初始化响应式检查
  checkScreenSize()
  window.addEventListener('resize', checkScreenSize)

  if (!live2dCanvas.value) {
    console.error('Canvas element not found!')
    return
  }

  app = new PIXI.Application({
    view: live2dCanvas.value,
    transparent: true,
    autoStart: true,
    width: window.innerWidth,
    height: window.innerHeight,
    backgroundAlpha: 0,
  })

  await updateModel()
})

onUnmounted(() => {
  window.removeEventListener('resize', checkScreenSize)
  if (app) {
    app.destroy(true)
  }
})
</script>

<style scoped>
.home {
  width: 100vw;
  height: 100vh;
  position: fixed;
  top: 0;
  left: 0;
  background-size: cover;
  background-position: center;
}

.ai-assistant-overlay {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.2);
  z-index: 1000;
  display: flex;
  flex-direction: row;
}

/* .ai-assistant-container-left {
  width: 280px;
  height: 100%;
  background: rgba(255, 255, 255, 1);
  display: flex;
  flex-direction: column;
  box-shadow: 0 0 15px rgba(0, 0, 0, 0.2);
  color: #fff !important;
  transition: all 0.3s ease;
  position: relative;
  z-index: 1000;
} */

.assistant-title {
  width: 100%;
  height: 60px;
  padding: 10px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.assistant-title-text {
  font-size: 20px;
  font-weight: bold;
  font-family: 'Arial', sans-serif;
  color: #fff;
}

.conversation-list {
  width: 100%;
  height: 100%;
  overflow-y: auto;
  padding: 8px 0;
}

.conversation-list::-webkit-scrollbar {
  width: 4px;
}

.conversation-list::-webkit-scrollbar-thumb {
  background-color: rgba(255, 255, 255, 0.2);
  border-radius: 4px;
}

.assistant-setting-divider {
  width: 100%;
  height: 1px;
  background: rgba(255, 255, 255, 0.1);
}

.assistant-setting-item {
  width: 100%;
  height: 50px;
  padding: 0 20px;
  display: flex;
  align-items: center;
  transition: background-color 0.2s ease;
}

.assistant-setting-item:hover {
  background-color: rgba(255, 255, 255, 0.1);
}

.assistant-setting-item-icon {
  width: 20px;
  height: 20px;
  margin-right: 10px;
  font-size: 16px;
  color: rgba(255, 255, 255, 0.8);
}

.assistant-setting-item-text {
  font-size: 14px;
  font-weight: 500;
  font-family: 'Arial', sans-serif;
  color: rgba(255, 255, 255, 0.8);
}

.assistant-setting {
  display: flex;
  flex-direction: row;
  width: 100%;
  cursor: pointer;
}

.ai-assistant-container-right {
  flex: 1;
  height: 100%;
  background: rgba(255, 255, 255, 0);
  border-radius: 0 0 0 20px;
  box-shadow: -5px 0 15px rgba(137, 122, 122, 0.1);
  backdrop-filter: blur(3px);
}

.conversation-new-button {
  height: 44px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 8px 12px;
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.1);
  transition: background-color 0.2s ease;
  border: 1px solid rgba(255, 255, 255, 0.2);
}

.conversation-new-button:hover {
  background: rgba(255, 255, 255, 0.2);
}

.conversation-new-button-icon {
  width: 16px;
  height: 16px;
  margin-right: 8px;
  font-size: 16px;
  color: rgba(255, 255, 255, 0.9);
}

.conversation-new-button-text {
  font-size: 14px;
  font-weight: 500;
  color: rgba(255, 255, 255, 0.9);
}

/* 移动端菜单切换按钮 */
.mobile-menu-toggle {
  position: fixed;
  top: 20px;
  left: 20px;
  z-index: 1100;
  width: 44px;
  height: 44px;
  background: rgba(0, 0, 0, 0.8);
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.3s ease;
}

.mobile-menu-toggle:hover {
  background: rgba(0, 0, 0, 0.9);
}

.hamburger {
  width: 24px;
  height: 18px;
  position: relative;
  transform: rotate(0deg);
  transition: 0.3s ease-in-out;
  cursor: pointer;
}

.hamburger span {
  display: block;
  position: absolute;
  height: 2px;
  width: 100%;
  background: #fff;
  border-radius: 2px;
  opacity: 1;
  left: 0;
  transform: rotate(0deg);
  transition: 0.3s ease-in-out;
}

.hamburger span:nth-child(1) {
  top: 0px;
}

.hamburger span:nth-child(2) {
  top: 8px;
}

.hamburger span:nth-child(3) {
  top: 16px;
}

.hamburger.active span:nth-child(1) {
  top: 8px;
  transform: rotate(135deg);
}

.hamburger.active span:nth-child(2) {
  opacity: 0;
  left: -60px;
}

.hamburger.active span:nth-child(3) {
  top: 8px;
  transform: rotate(-135deg);
}

/* 侧边栏遮罩层 */
.sidebar-overlay {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.5);
  z-index: 999;
}

/* 侧边栏响应式样式 */
.ai-assistant-container-left {
  width: 280px;
  height: 100%;
  background: rgba(200, 200, 200, 0.85);
  display: flex;
  flex-direction: column;
  /* border-right: 1px solid rgba(0, 0, 0, 1); */
  /* box-shadow: 0 0 15px rgba(0, 0, 0, 0.2); */
  transition: all 0.3s ease;
  position: relative;
  z-index: 1000;
}

/* 桌面端折叠状态 */
.ai-assistant-container-left.collapsed {
  width: 60px;
}

.ai-assistant-container-left.collapsed .conversation-new-button-text,
.ai-assistant-container-left.collapsed .assistant-setting-item-text {
  display: none;
}

/* 移动端隐藏/显示 */
.ai-assistant-container-left.mobile-hidden {
  transform: translateX(-100%);
}

.ai-assistant-container-left.mobile-visible {
  transform: translateX(0);
}

.assistant-title {
  width: 100%;
  height: 60px;
  padding: 10px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.sidebar-collapse-btn {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s ease;
  color: rgba(255, 255, 255, 0.8);
}

.sidebar-collapse-btn:hover {
  background: rgba(255, 255, 255, 0.2);
  color: #fff;
}

/* 媒体查询 */
@media (max-width: 768px) {
  .ai-assistant-container-left {
    position: absolute;
    top: 0;
    left: 0;
    width: 280px;
    height: 100%;
    z-index: 1000;
  }
  
  .ai-assistant-container-right {
    width: 100%;
    margin-left: 0;
  }
}

@media (max-width: 480px) {
  .ai-assistant-container-left {
    width: 260px;
  }
  
  .welcome-title {
    font-size: 24px;
  }
  
  .welcome-description {
    font-size: 14px;
  }
  
  .suggestion-item {
    padding: 10px 14px;
    font-size: 13px;
  }
}
/* .ant-conversations-item {
  color: #fff !important;
} */
</style>