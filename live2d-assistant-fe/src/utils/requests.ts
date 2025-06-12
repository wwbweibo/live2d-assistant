import axios from 'axios'
import type { SystemSettings } from '../types/message'

async function updateConfig(config: SystemSettings) {
    await axios.post(config.serverUrl + '/api/settings', 
        {
            llm: {
                base_url: config.assistantSettings.baseUrl,
                api_key: config.assistantSettings.apiKey,
            },
            mcp_servers: config.assistantSettings.mcpServers ? JSON.parse(config.assistantSettings.mcpServers) : []
        }
    ).catch((error) => {
        console.error(error)
    })
}

async function getMcpServerStatus(name: string, config: SystemSettings) {
    const response = await axios.get(config.serverUrl + '/api/mcp_servers/' + name + '/status')
    return response.data
}

export { updateConfig, getMcpServerStatus }