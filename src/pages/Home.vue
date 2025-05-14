<template>
  <div class="home">
    <canvas ref="live2dCanvas"></canvas>
    <div class="ai-assistant-overlay">
      <!-- 左右分栏，左侧27%，右侧73%，左侧展示对话列表，设置，聊天，右侧展示对话内容 -->
      <div class="ai-assistant-container-left">
        <div class="assistant-title">
          <div class="assistant-title-text">
            AI助手
          </div>
        </div>
        <div class="conversation-list">
          <Conversations :items="conversationItems" />
        </div>
        <!-- 分割线 -->
        <div class="assistant-setting-divider"></div>
        <div class="assistant-setting" @click="showSettings = true">
          <div class="assistant-setting-item">
            <div class="assistant-setting-item-icon">
              <i class="fas fa-cog"></i>
            </div>
            <div class="assistant-setting-item-text">
              设置
            </div>
          </div>
        </div>
      </div>
      <div class="ai-assistant-container-right">
        <ChatPage :systemSettings="systemSettings" />
      </div>
    </div>
    <a-modal :visible="showSettings" @cancel="showSettings = false" title="设置" @ok="saveSettings">
      <SettingModal :settings="systemSettings" :updateSettings="handleSystemSettingsUpdate" />
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ElMessage } from 'element-plus'
import { ref, onMounted, onUnmounted, reactive } from 'vue'
import * as PIXI from 'pixi.js'
import { Live2DModel as Live2DModelCubism4, MotionPreloadStrategy } from 'pixi-live2d-display/cubism4'
import { Live2DModel as Live2DModelCubism2 } from 'pixi-live2d-display/cubism2'

import { Conversations } from 'ant-design-x-vue'
import type { ConversationsProps } from 'ant-design-x-vue'

import { Modal as AModal, Button as AButton } from 'ant-design-vue'

import SettingModal from '../components/setting_modal.vue'
import ChatPage from '../components/chat.vue'
import { Live2DSettings, SystemSettings } from '../models/message.vue'

// 注册 Ticker
Live2DModelCubism4.registerTicker(PIXI.Ticker)
Live2DModelCubism2.registerTicker(PIXI.Ticker)

const live2dCanvas = ref<HTMLCanvasElement | null>(null)
let app: PIXI.Application | null = null
let model: any = null
const showSettings = ref(false)
const STORAGE_KEY = 'live2d-viewer-settings'

const conversationItems: ConversationsProps['items'] = Array.from({ length: 4 }).map((_, index) => ({
  key: `item${index + 1}`,
  label: `Conversation Item ${index + 1}`,
  group: 'Today'
}));

const systemSettings = reactive({
  serverUrl: 'http://localhost:8000',
  debugEnabled: false,
  backgroundPath: 'assets/background.jpg',
  assistantSettings: {
    assistantName: 'Senko',
    sysPrompt: undefined,
    model: 'qwen2.5',
  },
  live2DSettings: {
    modelPath: 'assets/models/Senko_Normals/senko.model3.json',
    offsetX: 0,
    offsetY: 0,
    scale: 0.5
  }
})

// 保存设置到 localStorage
const saveSettings = () => {
  localStorage.setItem(STORAGE_KEY, JSON.stringify({
    systemSettings
  }))
  ElMessage.success('设置已保存')
}

// 从 localStorage 加载设置
const loadSettings = () => {
  const savedSettings = localStorage.getItem(STORAGE_KEY)
  if (savedSettings) {
    const parsed = JSON.parse(savedSettings)
    Object.assign(systemSettings, parsed.systemSettings)
  }
}

const handleSystemSettingsUpdate = (newSettings: SystemSettings) => {
  if (systemSettings.live2DSettings.modelPath !== newSettings.live2DSettings.modelPath) {
    updateModel()
  }
  updateBackground()
  updatePosition()
  updateScale()
  Object.assign(systemSettings, newSettings)
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
    console.log(motions)
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
        console.log(randomMotion)
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

onMounted(async () => {
  loadSettings()
  updateBackground()

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
  if (app) {
    app.destroy(true)
  }
})
</script>

<style scoped>
.chat-modal {
  position: absolute;
  top: 0;
  right: 0;
  bottom: 0;
  width: 600px;
  background: rgba(255, 255, 255, 0.95);
  padding: 20px;
  box-shadow: -2px 0 10px rgba(0, 0, 0, 0.1);
}

.home {
  width: 100vw;
  height: 100vh;
  position: fixed;
  top: 0;
  left: 0;
  background-size: cover;
  background-position: center;
}

canvas {
  width: 100%;
  height: 100%;
  display: block;
}

.settings-button {
  position: absolute;
  right: 20px;
  top: 20px;
  width: 40px;
  height: 40px;
  background: rgba(255, 255, 255, 0.8);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
  z-index: 1000;
}

.chat-button {
  position: absolute;
  right: 20px;
  top: 100px;
  width: 40px;
  height: 40px;
  background: rgba(255, 255, 255, 0.8);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
}

.settings-modal {
  position: absolute;
  top: 0;
  right: 0;
  bottom: 0;
  width: 400px;
  background: rgba(255, 255, 255, 0.95);
  padding: 20px;
  box-shadow: -2px 0 10px rgba(0, 0, 0, 0.1);
}


.close-button {
  margin-top: auto;
  padding: 10px;
  background: #42b983;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.close-button:hover {
  background: #3aa876;
}

.button-group {
  display: flex;
  gap: 10px;
  position: absolute;
  top: 20px;
  right: 20px;
  width: auto;
}

.save-button {
  flex: 0 0 auto;
  padding: 8px 16px;
  background: #4CAF50;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.save-button:hover {
  background: #45a049;
}

.close-button {
  flex: 0 0 auto;
  padding: 8px 16px;
  background: #42b983;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.close-button:hover {
  background: #3aa876;
}

.ai-assistant-overlay {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.5);
  z-index: 1000;
  display: flex;
  flex-direction: row;
}

.ai-assistant-container-left {
  width: 20%;
  height: 100%;
  background: rgba(200, 200, 200, 0.8);
  display: flex;
  flex-direction: column;
}

.assistant-title {
  width: 100%;
  height: 7%;
  /* background: rgba(255, 255, 255, 0); */
  padding: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.assistant-title-text {
  font-size: 24px;
  font-weight: bold;
  font-family: 'Arial', sans-serif;
}

.conversation-list {
  width: 100%;
  height: 100%;
  /* background: rgba(255, 255, 255, 0); */
  overflow-y: auto;
}

.assistant-setting-divider {
  width: 100%;
  height: 1px;
  background: rgba(0, 0, 0, 0.1);
}

.assistant-setting-item {
  width: 100%;
  height: 70px;
  padding-left: 20px;
  padding-bottom: 10px;
  /* background: rgba(255, 255, 255, 0); */
  display: flex;
  align-items: center;
  justify-content: start;
}

.assistant-setting-item-icon {
  width: 20px;
  height: 20px;
  margin-right: 10px;
  font-size: 20px;
  font-weight: bold;
  font-family: 'Arial', sans-serif;
}

.assistant-setting-item-text {
  font-size: 16px;
  font-weight: bold;
  font-family: 'Arial', sans-serif;
}

.assistant-setting {
  width: 100%;
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  justify-content: start;
}


.ai-assistant-container-right {
  width:80%;
  height: 100%;
  background: rgba(255, 255, 255, 0.8);
}
</style>