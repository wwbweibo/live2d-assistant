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
        <!-- 侧边栏顶部极光装饰 -->
        <div class="sidebar-aurora-glow"></div>
        <div class="assistant-title">
          <div class="assistant-title-text">
            <span class="assistant-logo-icon">✦</span>
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
        </div>
      </div>
      <div class="ai-assistant-container-right">
        <ChatPage :systemSettings="systemSettings" :onNewMessage="handleNewMessage" :conversation="currentConversation" />
      </div>
    </div>
    <a-modal :open="showSettings" @cancel="showSettings = false" title="设置" :width="960" :footer="null">
      <SettingModal
        :settings="systemSettings"
        :updateSettings="handleSystemSettingsUpdate"
        :onAgentsUpdate="onAgentsUpdate"
      />
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, reactive } from 'vue'
import { FormOutlined, SettingOutlined } from '@ant-design/icons-vue'
import * as PIXI from 'pixi.js'
import { Live2DModel as Live2DModelCubism4, MotionPreloadStrategy } from 'pixi-live2d-display/cubism4'
import { Live2DModel as Live2DModelCubism2 } from 'pixi-live2d-display/cubism2'
import { Conversations } from 'ant-design-x-vue'
import type { ConversationsProps } from 'ant-design-x-vue'
import { h } from 'vue'
import { Modal as AModal, Button as AButton, message, Space } from 'ant-design-vue'
import SettingModal from '../components/setting_modal.vue'
import ChatPage from '../components/chat.vue'
import { SystemSettings, Conversation } from '../types/message'
import { updateConfig } from '../utils/requests'
import { v4 as uuidv4 } from 'uuid'
import { CommentOutlined, DeleteOutlined, RobotOutlined } from '@ant-design/icons-vue'
import { API_URL } from '../utils/api'

// 注册 Ticker
Live2DModelCubism4.registerTicker(PIXI.Ticker)
Live2DModelCubism2.registerTicker(PIXI.Ticker)

const live2dCanvas = ref<HTMLCanvasElement | null>(null)
let app: PIXI.Application | null = null
let model: any = null
const showSettings = ref(false)


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
  backgroundPath: 'assets/background.jpg',
  assistantSettings: {
    assistantName: 'Senko',
    sysPrompt: undefined,
    model: 'qwen2.5',
    apiKey: undefined,
    baseUrl: undefined,
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

const onAgentsUpdate = (agents: any[]) => {
  systemSettings.assistantSettings.agents = agents
  saveSettings()
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
/* ─── 全局布局 ─────────────────────────────────────── */
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
  z-index: 1000;
  display: flex;
  flex-direction: row;
}

/* ─── 侧边栏（毛玻璃深色） ───────────────────────────── */
.ai-assistant-container-left {
  width: 280px;
  height: 100%;
  background: linear-gradient(180deg, rgb(22, 22, 38) 0%, rgb(14, 14, 28) 100%);
  backdrop-filter: blur(var(--blur-amount-heavy)) saturate(160%);
  -webkit-backdrop-filter: blur(var(--blur-amount-heavy)) saturate(160%);
  border-right: 1px solid var(--glass-border-dark);
  display: flex;
  flex-direction: column;
  transition: width var(--duration-normal) var(--ease-out),
              transform var(--duration-normal) var(--ease-out);
  position: relative;
  z-index: 1000;
  overflow: hidden;
}

/* 侧边栏顶部极光光晕 */
.sidebar-aurora-glow {
  position: absolute;
  top: -60px;
  left: -30px;
  right: -30px;
  height: 180px;
  background: radial-gradient(ellipse at 50% 0%, rgba(var(--color-primary-rgb), 0.20) 0%, rgba(var(--color-accent-rgb), 0.08) 50%, transparent 80%);
  pointer-events: none;
  z-index: 0;
  animation: glow-pulse 4s ease-in-out infinite;
}

.ai-assistant-container-left.collapsed {
  width: 64px;
}
.ai-assistant-container-left.collapsed .assistant-title-text,
.ai-assistant-container-left.collapsed .conversation-new-button-text,
.ai-assistant-container-left.collapsed .conversation-group-title {
  display: none;
}
.ai-assistant-container-left.collapsed .conversation-new-button {
  justify-content: center;
  padding: 0;
}
.ai-assistant-container-left.collapsed .assistant-setting {
  justify-content: center;
  padding: 0;
}
.ai-assistant-container-left.collapsed .assistant-setting-item {
  justify-content: center;
}

.ai-assistant-container-left.mobile-hidden {
  transform: translateX(-100%);
}
.ai-assistant-container-left.mobile-visible {
  transform: translateX(0);
}

/* ─── 标题区 ───────────────────────────────────────── */
.assistant-title {
  height: 60px;
  padding: 0 var(--space-md);
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-shrink: 0;
  border-bottom: 1px solid var(--glass-border-dark);
  position: relative;
  z-index: 1;
}

.assistant-title-text {
  font-size: 17px;
  font-weight: 700;
  background: linear-gradient(135deg, #c7d2fe, #a78bfa, #f0abfc);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  letter-spacing: 0.03em;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  display: flex;
  align-items: center;
  gap: var(--space-sm);
}

.assistant-logo-icon {
  font-size: 20px;
  background: var(--gradient-aurora);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  animation: float 3s ease-in-out infinite;
}

.sidebar-collapse-btn {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--radius-sm);
  cursor: pointer;
  color: var(--text-on-dark-muted);
  transition: all var(--duration-fast) var(--ease-out);
  flex-shrink: 0;
  font-size: 14px;
}
.sidebar-collapse-btn:hover {
  background: rgba(255, 255, 255, 0.10);
  color: var(--text-on-dark);
}

/* ─── 对话列表 ─────────────────────────────────────── */
.conversation-list {
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
  padding: var(--space-sm) 0;
  scrollbar-width: thin;
}

.conversation-new-button {
  height: 44px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: var(--space-sm) var(--space-sm);
  padding: 0 var(--space-md);
  border-radius: var(--radius-md);
  background: linear-gradient(135deg, rgba(99, 102, 241, 0.15), rgba(167, 139, 250, 0.10));
  border: 1px solid rgba(99, 102, 241, 0.20);
  cursor: pointer;
  color: var(--text-on-dark);
  font-size: 14px;
  font-weight: 500;
  transition: all var(--duration-fast) var(--ease-out);
  gap: var(--space-sm);
  white-space: nowrap;
  position: relative;
  overflow: hidden;
}
.conversation-new-button::before {
  content: '';
  position: absolute;
  inset: 0;
  background: var(--gradient-aurora);
  opacity: 0;
  transition: opacity var(--duration-normal) var(--ease-out);
}
.conversation-new-button:hover {
  border-color: rgba(99, 102, 241, 0.40);
  color: #fff;
  box-shadow: 0 0 20px rgba(var(--color-primary-rgb), 0.20),
              0 4px 12px rgba(0, 0, 0, 0.15);
  transform: translateY(-1px);
}
.conversation-new-button:hover::before {
  opacity: 0.12;
}
.conversation-new-button:active {
  transform: scale(0.98) translateY(0);
}
.conversation-new-button-icon {
  font-size: 16px;
  color: var(--color-accent);
  display: flex;
  align-items: center;
  position: relative;
  z-index: 1;
}
.conversation-new-button-text {
  font-size: 14px;
  position: relative;
  z-index: 1;
}

.conversation-group-title {
  padding: var(--space-sm) var(--space-md);
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--text-on-dark-muted);
}

.assistant-setting-divider {
  height: 1px;
  background: linear-gradient(90deg, transparent, var(--glass-border-dark), rgba(var(--color-primary-rgb), 0.15), var(--glass-border-dark), transparent);
  flex-shrink: 0;
  margin: 0 var(--space-sm);
}

.assistant-setting {
  display: flex;
  align-items: center;
  justify-content: flex-start;
  gap: var(--space-sm);
  padding: var(--space-sm);
  flex-shrink: 0;
}
.assistant-setting-item {
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--radius-md);
  cursor: pointer;
  color: var(--text-on-dark-muted);
  transition: all var(--duration-normal) var(--ease-out);
  font-size: 18px;
  position: relative;
}
.assistant-setting-item::before {
  content: '';
  position: absolute;
  inset: 0;
  border-radius: inherit;
  background: var(--gradient-primary);
  opacity: 0;
  transition: opacity var(--duration-normal) var(--ease-out);
}
.assistant-setting-item:hover {
  color: #fff;
  transform: translateY(-2px);
}
.assistant-setting-item:hover::before {
  opacity: 0.15;
}
.assistant-setting-item:active {
  transform: translateY(0) scale(0.95);
}
.assistant-setting-item-icon {
  display: flex;
  align-items: center;
  justify-content: center;
}

.ai-assistant-container-right {
  flex: 1;
  height: 100%;
  background: rgba(255, 255, 255, 0.88);
  backdrop-filter: blur(20px) saturate(160%);
  -webkit-backdrop-filter: blur(20px) saturate(160%);
  display: flex;
  flex-direction: column;
}

.sidebar-overlay {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  z-index: 999;
  background: rgba(0, 0, 0, 0.3);
  backdrop-filter: blur(2px);
  -webkit-backdrop-filter: blur(2px);
}

.mobile-menu-toggle {
  position: fixed;
  top: 20px;
  left: 20px;
  z-index: 1100;
  width: 44px;
  height: 44px;
  border-radius: var(--radius-md);
  background: var(--glass-bg-dark);
  backdrop-filter: blur(var(--blur-amount));
  -webkit-backdrop-filter: blur(var(--blur-amount));
  border: 1px solid var(--glass-border-dark);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  box-shadow: var(--glass-shadow);
  transition: all var(--duration-fast) var(--ease-out);
}
.mobile-menu-toggle:hover {
  background: var(--glass-bg-dark-hover);
  transform: scale(1.05);
}

.hamburger {
  width: 20px;
  height: 14px;
  position: relative;
  cursor: pointer;
}
.hamburger span {
  display: block;
  position: absolute;
  height: 2px;
  width: 100%;
  background: var(--text-on-dark);
  border-radius: 2px;
  transition: all var(--duration-fast) var(--ease-out);
}
.hamburger span:nth-child(1) { top: 0px; }
.hamburger span:nth-child(2) { top: 6px; }
.hamburger span:nth-child(3) { top: 12px; }
.hamburger.active span:nth-child(1) {
  top: 6px;
  transform: rotate(135deg);
}
.hamburger.active span:nth-child(2) {
  opacity: 0;
  transform: translateX(-8px);
}
.hamburger.active span:nth-child(3) {
  top: 6px;
  transform: rotate(-135deg);
}

@media (max-width: 768px) {
  .ai-assistant-container-left {
    position: absolute;
    top: 0;
    left: 0;
    width: 280px;
    height: 100%;
    z-index: 1000;
    box-shadow: var(--glass-shadow-lg);
  }
  .ai-assistant-container-right {
    width: 100%;
  }
}

@media (max-width: 480px) {
  .ai-assistant-container-left {
    width: 260px;
  }
}
</style>
