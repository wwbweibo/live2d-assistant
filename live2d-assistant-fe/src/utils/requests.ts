import axios from 'axios'
import type { SystemSettings } from '../types/message'

async function updateConfig(config: SystemSettings) {
    // MVP: 目前不需要向服务端同步配置
    // LLM 配置由前端通过 AgentConfig 直接传递给后端
    console.log('Config updated:', config)
}

export { updateConfig }
