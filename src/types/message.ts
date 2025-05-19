interface Message {
  id: number;
  content: string;
  role: string;
  timestamp: string | undefined;
  loading: boolean | undefined;
}

interface LLMSettings {
    assistantName: string;
    sysPrompt: string | undefined;
    model: string;   
    baseUrl: string | undefined;
    apiKey: string | undefined;
    mcpServers: string | undefined;
}

interface Live2DSettings {
    modelPath: string;
    offsetX: number;
    offsetY: number;
    scale: number;
}

interface ChatHistory {
    role: string
    content: string
}

interface SystemSettings {
    serverUrl: string;
    backgroundPath: string;
    assistantSettings: LLMSettings;
    live2DSettings: Live2DSettings;
}

interface MCPServerTool {
    name: string;
    description: string;
}

interface MCPServer {
    name: string;
    transport: string;
    url: string | undefined;
    command: string | undefined;
    args: string | undefined;
    tools: MCPServerTool[] | undefined;
    status: string | undefined;
}

interface MCPServerStatus {
    status: string;
    message: string;
    details: {
        tools: MCPServerTool[];
    };
}

interface Conversation {
    key: string;
    label: string;
    messages: Message[];
    createdAt: number;
    updatedAt: number;
    group: string | undefined;
}

export type { Message, LLMSettings, ChatHistory, SystemSettings, Live2DSettings, MCPServer, MCPServerStatus, MCPServerTool, Conversation };