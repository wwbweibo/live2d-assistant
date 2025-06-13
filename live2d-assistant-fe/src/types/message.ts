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
    agents: string | undefined;
}

interface Live2DSettings {
    modelPath: string;
    offsetX: number;
    offsetY: number;
    scale: number;
    themeColor: string;
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

interface ToolResouce {
    source: string;
    mcp_server: string | undefined;
    local_tool_path: string | undefined;
    tool: any | undefined;
}

interface AgentConfig {
    name: string;
    description: string;
    tools: ToolResouce[] | undefined;
    prompt: string | undefined;
    hands_off: string[] | undefined;
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

interface KnowledgeFile {
    id: string;
    metadata: any;
    text: string;
}

export type { Message, LLMSettings, ChatHistory, SystemSettings, Live2DSettings, MCPServer, MCPServerStatus, MCPServerTool, Conversation, AgentConfig, ToolResouce, KnowledgeFile };