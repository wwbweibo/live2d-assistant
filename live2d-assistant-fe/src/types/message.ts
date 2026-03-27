export interface AgentMeta {
  name: string
  duty: string
  skills: string[]
  system_prompt: string
  mcp_servers: string[]
}

export interface MCPServerConfig {
  name: string
  transport: string
  command?: string
  args?: string[]
  env?: Record<string, string>
  cwd?: string
  url?: string
  auth?: string
  headers?: Record<string, string>
}

export interface AgentConfig {
  metadata: Record<string, unknown>
  agents: AgentMeta[]
  mcp_servers: MCPServerConfig[]
}

export interface SkillMeta {
  name: string
  description: string
  instruction: string
}

export interface LLMConfig {
  provider: string
  api_key: string
  model: string
  base_url?: string
}

export interface Conversation {
  key: string;
  label: string;
  messages: Message[];
  createdAt: number;
  updatedAt: number;
  group: string | undefined;
}

export interface Message {
  id: number;
  content: string;
  role: string;
  timestamp: string | undefined;
  loading: boolean | undefined;
}

export interface LLMSettings {
  assistantName: string;
  sysPrompt: string | undefined;
  model: string;
  baseUrl: string | undefined;
  apiKey: string | undefined;
  agents: string | undefined;
}

export interface Live2DSettings {
  modelPath: string;
  offsetX: number;
  offsetY: number;
  scale: number;
  themeColor: string;
}

export interface ChatHistory {
  role: string;
  content: string;
}

export interface SystemSettings {
  backgroundPath: string;
  assistantSettings: LLMSettings;
  live2DSettings: Live2DSettings;
}

export type {
  Message,
  LLMSettings,
  ChatHistory,
  SystemSettings,
  Live2DSettings,
  Conversation,
  AgentMeta,
  MCPServerConfig,
  AgentConfig,
  SkillMeta,
  LLMConfig,
};
