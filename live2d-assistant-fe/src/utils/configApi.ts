import { API_URL } from './api'
import type { AgentConfig, LLMConfig, SkillMeta, MCPServerConfig, MCPServerResp } from '../types/message'

// Re-export types for backward compatibility
export type { LLMConfig, AgentConfig, SkillMeta, MCPServerConfig, MCPServerResp }
export type { AgentMeta } from '../types/message'

// LLM 配置
export async function getLLMConfig(): Promise<LLMConfig> {
  const resp = await fetch(`${API_URL}/api/settings/llm`)
  return resp.json()
}

export async function updateLLMConfig(config: LLMConfig): Promise<{ success: boolean; config: LLMConfig }> {
  const resp = await fetch(`${API_URL}/api/settings/llm`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(config),
  })
  return resp.json()
}

// Agent 配置（完整的 AgentConfig：metadata + agents + mcp_servers）
export async function getAgentsConfig(): Promise<AgentConfig> {
  const resp = await fetch(`${API_URL}/api/settings/agents`)
  return resp.json()
}

export async function updateAgentsConfig(config: AgentConfig): Promise<{ success: boolean; config: AgentConfig }> {
  const resp = await fetch(`${API_URL}/api/settings/agents`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(config),
  })
  return resp.json()
}

export async function deleteAgentByName(name: string): Promise<{ success: boolean }> {
  const resp = await fetch(`${API_URL}/api/settings/agents/${name}`, {
    method: 'DELETE',
  })
  return resp.json()
}

// Skill 配置
export async function getSkillsConfig(): Promise<SkillMeta[]> {
  const resp = await fetch(`${API_URL}/api/settings/skills`)
  return resp.json()
}

export async function upsertSkill(skill: SkillMeta): Promise<{ success: boolean; skill: SkillMeta }> {
  const resp = await fetch(`${API_URL}/api/settings/skills`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(skill),
  })
  return resp.json()
}

export async function deleteSkillByName(name: string): Promise<{ success: boolean }> {
  const resp = await fetch(`${API_URL}/api/settings/skills/${name}`, {
    method: 'DELETE',
  })
  return resp.json()
}

// MCP Server 配置
export async function getMcpServersConfig(): Promise<MCPServerResp[]> {
  const resp = await fetch(`${API_URL}/api/settings/mcp-servers`)
  return resp.json()
}

export async function upsertMcpServer(server: MCPServerConfig): Promise<{ success: boolean; server: MCPServerConfig }> {
  const resp = await fetch(`${API_URL}/api/settings/mcp-servers`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(server),
  })
  return resp.json()
}

export async function deleteMcpServerByName(name: string): Promise<{ success: boolean }> {
  const resp = await fetch(`${API_URL}/api/settings/mcp-servers/${name}`, {
    method: 'DELETE',
  })
  return resp.json()
}
