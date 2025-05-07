<template>
  <div class="home">
    <canvas ref="live2dCanvas"></canvas>
    <!-- 设置按钮 -->
    <div v-if="!showSettings && !showChat">
      <div class="settings-button" @click="showSettings = true">
        <i class="fas fa-cog"></i>
      </div>
    </div>
    <div v-if="!showSettings && !showChat">
      <div class="chat-button" @click="showChat = true">
        <i class="fas fa-comment"></i>
      </div>
    </div>
    <!-- 设置弹窗 -->
    <div class="settings-modal" v-if="showSettings">
      <div class="button-group">
        <button class="save-button" @click="saveSettings">保存设置</button>
        <button class="close-button" @click="showSettings = false">关闭</button>
      </div>
      <SettingModal :settings="settings" :updateSettings="handleSettingsUpdate" />
    </div>
    <!-- 聊天弹窗 -->
    <div class="chat-modal" v-if="showChat">
      <div class="chat-header">
        <button class="close-button" @click="showChat = false">关闭</button>
      </div>
      <ChatModal :assistantSettings="assistantSettings" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ElMessage } from 'element-plus'
import { ref, onMounted, onUnmounted, reactive } from 'vue'
import * as PIXI from 'pixi.js'
import { Live2DModel as Live2DModelCubism4, MotionPreloadStrategy } from 'pixi-live2d-display/cubism4'
import { Live2DModel as Live2DModelCubism2 } from 'pixi-live2d-display/cubism2'
import ChatModal from '../components/chat_modal.vue'
import SettingModal from '../components/setting_modal.vue'

// 注册 Ticker
Live2DModelCubism4.registerTicker(PIXI.Ticker)
Live2DModelCubism2.registerTicker(PIXI.Ticker)

const live2dCanvas = ref<HTMLCanvasElement | null>(null)
let app: PIXI.Application | null = null
let model: any = null

const showSettings = ref(false)
const showChat = ref(false)
const STORAGE_KEY = 'live2d-viewer-settings'


// 默认设置
const defaultSettings = {
  modelPath: 'assets/models/Senko_Normals/senko.model3.json',
  offsetX: 0,
  offsetY: 0,
  scale: 0.5,
  backgroundPath: 'assets/background.jpg'
}

const systemSettings = reactive({
  serverUrl: 'http://localhost:8000',
  debugEnabled: false,
  backgroundPath: 'assets/background.jpg'
})

const modelSettings = reactive({
  modelPath: 'assets/models/Senko_Normals/senko.model3.json',
  offsetX: 0,
  offsetY: 0,
  scale: 0.5,
  backgroundPath: 'assets/background.jpg'
})

// 助手设置
const assistantSettings = reactive({
  name: 'Senko',
  model: 'qwen2.5',
  ollamaHost: 'http://localhost:11434',
  ttsEnabled: false
})


const settings = reactive({
  'system': systemSettings,
  'model': modelSettings,
  'assistant': assistantSettings,
})

// 保存设置到 localStorage
const saveSettings = () => {
  localStorage.setItem(STORAGE_KEY, JSON.stringify({
    systemSettings,
    modelSettings,
    assistantSettings
  }))
  // 调用设置接口

  // 提示保存成功
  ElMessage.success('设置已保存')
}

// 从 localStorage 加载设置
const loadSettings = () => {
  const savedSettings = localStorage.getItem(STORAGE_KEY)
  if (savedSettings) {
    const parsed = JSON.parse(savedSettings)
    Object.assign(modelSettings, parsed.modelSettings)
    Object.assign(assistantSettings, parsed.assistantSettings)
    Object.assign(systemSettings, parsed.systemSettings)
  }
}

// 处理模型设置更新
const handleModelSettingsUpdate = (newSettings: any) => {
  console.log('handleModelSettingsUpdate', newSettings)
  // 检查是否改变了模型路径
  const modelPathChanged = modelSettings.modelPath !== newSettings.modelPath
  Object.assign(modelSettings, newSettings)
  // 如果模型路径改变，需要重新加载模型
  if (modelPathChanged) {
    updateModel()
  } else {
    // 否则只更新现有模型的参数
    updatePosition()
    updateScale()
  }
  // 更新背景
  updateBackground()
}

const handleSystemSettingsUpdate = (newSettings: any) => {
  Object.assign(systemSettings, newSettings)
}

const handleAssistantSettingsUpdate = (newSettings: any) => {
  Object.assign(assistantSettings, newSettings)
}

const isModelSettingUpdated = (oldSetting, newSetting) => {
  return oldSetting.modelPath !== newSetting.modelPath ||
    oldSetting.offsetX !== newSetting.offsetX ||
    oldSetting.offsetY !== newSetting.offsetY ||
    oldSetting.scale !== newSetting.scale
}

const isSystemSettingUpdated = (oldSetting, newSetting) => {
  return oldSetting.serverUrl !== newSetting.serverUrl ||
    oldSetting.debugEnabled !== newSetting.debugEnabled ||
    oldSetting.backgroundPath !== newSetting.backgroundPath
}

const isAssistantSettingUpdated = (oldSetting, newSetting) => {
  return oldSetting.name !== newSetting.name ||
    oldSetting.model !== newSetting.model ||
    oldSetting.ollamaHost !== newSetting.ollamaHost ||
    oldSetting.ttsEnabled !== newSetting.ttsEnabled
}

const handleSettingsUpdate = (newSettings: any) => {
  if (isModelSettingUpdated(modelSettings, newSettings.model)) {
    handleModelSettingsUpdate(newSettings.model)
  }
  if (isSystemSettingUpdated(systemSettings, newSettings.system)) {
    handleSystemSettingsUpdate(newSettings.system)
  }
  if (isAssistantSettingUpdated(assistantSettings, newSettings.assistant)) {
    handleAssistantSettingsUpdate(newSettings.assistant)
  }
  if (settings.system.backgroundPath !== newSettings.system.backgroundPath) {
    updateBackground()
  }
  Object.assign(settings, newSettings)
}

// 更新模型位置
const updatePosition = () => {
  if (model && app) {
    const xOffset = (app.renderer.width * Number(modelSettings.offsetX)) / 100
    const yOffset = (app.renderer.height * Number(modelSettings.offsetY)) / 100
    model.x = app.renderer.width / 2 + xOffset
    model.y = app.renderer.height * 2 + yOffset
  }
}

// 更新模型缩放
const updateScale = () => {
  if (model) {
    model.scale.set(Number(modelSettings.scale))
  }
}

// 更新背景
const updateBackground = () => {
  const homeElement = document.querySelector('.home') as HTMLElement
  if (homeElement) {
    homeElement.style.backgroundImage = `url('${settings.system.backgroundPath}')`
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

    const isModel3 = modelSettings.modelPath.endsWith('.model3.json')
    const ModelClass = isModel3 ? Live2DModelCubism4 : Live2DModelCubism2
    const motions = await fetch(modelSettings.modelPath).
      then(async resp => {
        const content = await resp.json();
        if (content['FileReferences']['Motions'] !== undefined) {
          return content['FileReferences']['Motions']
        }
      })
    model = await ModelClass.from(modelSettings.modelPath, {
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
</style>