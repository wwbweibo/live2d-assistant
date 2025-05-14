<script setup lang="ts">
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

export type { Message, LLMSettings, ChatHistory, SystemSettings, Live2DSettings };
</script>