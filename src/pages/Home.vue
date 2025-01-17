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
      <!-- <div class="settings-content">
        <h3>模型设置</h3>
        
        <div class="setting-item">
          <label>模型路径：</label>
          <input v-model="settings.modelPath" type="text" @change="updateModel">
        </div>

        <div class="setting-item">
          <div class="setting-header">
            <label>横向偏移：</label>
            <button class="reset-button" @click="resetOffset('x')">重置</button>
          </div>
          <div class="setting-control">
            <input 
              v-model="settings.offsetX" 
              type="range" 
              min="-100" 
              max="100" 
              @input="updatePosition"
            >
            <span>{{ settings.offsetX }}%</span>
          </div>
        </div>

        <div class="setting-item">
          <div class="setting-header">
            <label>纵向偏移：</label>
            <button class="reset-button" @click="resetOffset('y')">重置</button>
          </div>
          <div class="setting-control">
            <input 
              v-model="settings.offsetY" 
              type="range" 
              min="-100" 
              max="100" 
              @input="updatePosition"
            >
            <span>{{ settings.offsetY }}%</span>
          </div>
        </div>

        <div class="setting-item">
          <div class="setting-header">
            <label>缩放比例：</label>
            <button class="reset-button" @click="resetScale">重置</button>
          </div>
          <div class="setting-control">
            <input 
              v-model="settings.scale" 
              type="range" 
              min="0.1" 
              max="2" 
              step="0.1" 
              @input="updateScale"
            >
            <span>{{ settings.scale }}x</span>
          </div>
        </div>

        <div class="setting-item">
          <label>背景图片：</label>
          <div class="setting-control">
            <input 
              v-model="settings.backgroundPath" 
              type="text" 
              @change="updateBackground"
            >
            <button class="reset-button" @click="resetBackground">重置</button>
          </div>
        </div>

        <div class="button-group">
          <button class="save-button" @click="saveSettings">保存设置</button>
          <button class="close-button" @click="showSettings = false">关闭</button>
        </div>
      </div> -->
      <SettingModel :onModelSettingChange="onModelSettingChange" :onAssistantSettingChange="onAssistantSettingChange" />
      <div class="button-group">
          <button class="save-button" @click="saveSettings">保存设置</button>
          <button class="close-button" @click="showSettings = false">关闭</button>
      </div>
    </div>
    <!-- 聊天弹窗 -->
    <div class="chat-modal" v-if="showChat">
      <div class="chat-header">
        <button class="close-button" @click="showChat = false">关闭</button>
      </div>
      <ChatModal />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, reactive } from 'vue'
import * as PIXI from 'pixi.js'
import { Live2DModel as Live2DModelCubism4 } from 'pixi-live2d-display/cubism4'
import { Live2DModel as Live2DModelCubism2 } from 'pixi-live2d-display/cubism2'
import ChatModal from '../components/chat_modal.vue'
import SettingModel from '../components/setting_modal.vue'

// 注册 Ticker
Live2DModelCubism4.registerTicker(PIXI.Ticker)
Live2DModelCubism2.registerTicker(PIXI.Ticker)

const live2dCanvas = ref<HTMLCanvasElement | null>(null)
let app: PIXI.Application | null = null
let model: any = null


const showSettings = ref(false)
const showChat = ref(false)
const STORAGE_KEY = 'live2d-viewer-settings'

const settings = reactive({
  modelPath: 'assets/models/Senko_Normals/senko.model3.json',
  offsetX: 0,
  offsetY: 0,
  scale: 0.5,
  backgroundPath: 'assets/background.jpg'
})

const defaultSettings = {
  offsetX: 0,
  offsetY: 0,
  scale: 0.5,
  backgroundPath: 'assets/background.jpg'
}

const resetOffset = (axis: 'x' | 'y') => {
  if (axis === 'x') {
    settings.offsetX = defaultSettings.offsetX
  } else {
    settings.offsetY = defaultSettings.offsetY
  }
  updatePosition()
}

const resetScale = () => {
  settings.scale = defaultSettings.scale
  updateScale()
}

// 保存设置到 localStorage
const saveSettings = () => {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(settings))
}

// 从 localStorage 加载设置
const loadSettings = () => {
  const savedSettings = localStorage.getItem(STORAGE_KEY)
  if (savedSettings) {
    const parsed = JSON.parse(savedSettings)
    settings.modelPath = parsed.modelPath
    settings.offsetX = parsed.offsetX
    settings.offsetY = parsed.offsetY
    settings.scale = parsed.scale
  }
}

// 添加重置背景的方法
const resetBackground = () => {
  settings.backgroundPath = defaultSettings.backgroundPath
  updateBackground()
}

const onModelSettingChange = (newSettings: any) => {
  settings.modelPath = newSettings.modelPath
  settings.offsetX = newSettings.offsetX
  settings.offsetY = newSettings.offsetY
  settings.scale = newSettings.scale
  updateModel()
  updatePosition()
  updateScale()
}

const onAssistantSettingChange = (newSettings: any) => {
  // Implement the logic for assistant setting change
  console.log('Assistant settings changed:', newSettings)
}

onMounted(async () => {
  // 先加载保存的设置
  loadSettings()
  // 初始化背景
  updateBackground()
  console.log("Settings loaded:", settings)
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
  console.log("init app:", app);
  try {
    const modelSettings = {
      motionPreload: "none",
      autoInteract: false,
      autoUpdate: true
    }

    // 添加调试信息
    console.log('Loading model from:', settings.modelPath)
    console.log('PIXI Application created:', app)
    console.log('Live2D Core loaded:', window.Live2DCubismCore)
    console.log('Live2D Model class:', Live2DModelCubism4)

    // 使用保存的模型路径
    const isModel3 = settings.modelPath.endsWith('.model3.json')
    const ModelClass = isModel3 ? Live2DModelCubism4 : Live2DModelCubism2

    model = await ModelClass.from(settings.modelPath, modelSettings)
    
    if (app && model) {
      console.log('Model loaded successfully:', model)
      app.stage.addChild(model)
      
      // 设置锚点
      model.anchor.set(0.5, 1.0)
      
      // 应用保存的设置
      updateScale()
      updatePosition()
      
      // 使舞台可交互
      app.stage.interactive = true
    }
  } catch (error) {
    console.error('模型加载失败:', error)
  }
})

onUnmounted(() => {
  if (app) {
    app.destroy(true)
  }
})

const updatePosition = () => {
  if (model && app) {
    // 将百分比转换为实际像素
    const xOffset = (app.renderer.width * Number(settings.offsetX)) / 100
    const yOffset = (app.renderer.height * Number(settings.offsetY)) / 100
    
    model.x = app.renderer.width / 2 + xOffset
    model.y = app.renderer.height * 2 + yOffset
  }
}

const updateScale = () => {
  if (model) {
    model.scale.set(Number(settings.scale))
  }
}

const updateModel = async () => {
  if (!app) return
  
  try {
    if (model) {
      app.stage.removeChild(model)
    }
    
    // 根据文件扩展名选择合适的模型加载器
    const isModel3 = settings.modelPath.endsWith('.model3.json')
    const ModelClass = isModel3 ? Live2DModelCubism4 : Live2DModelCubism2
    
    model = await ModelClass.from(settings.modelPath, {
      motionPreload: "none",
      autoInteract: false,
      autoUpdate: true
    })
    
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

const updateBackground = () => {
  const homeElement = document.querySelector('.home') as HTMLElement
  if (homeElement) {
    homeElement.style.backgroundImage = `url('${settings.backgroundPath}')`
  }
}
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