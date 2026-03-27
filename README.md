# Live2D Assistant

## 项目简介

**Live2D Assistant** 是一个集成了 Live2D 虚拟形象和 AI 智能对话的多端（Web/Electron 桌面）助手平台。项目支持自定义 Live2D 模型、AI 大语言模型（LLM）接入，适合二次元互动、AI 助手、智能桌搭等多种场景。

## 主要特性
- **Live2D 虚拟形象**：支持自定义模型、背景、缩放与位置调整。
- **AI 智能对话**：集成多种 LLM（如 Qwen、OpenAI、Gemini 等），支持上下文多轮对话。
- **多代理系统**：基于 agentic-agents 框架，支持 Router + 专家 Agent 协作。
- **多端支持**：Web 端（Vite+Vue3）、桌面端（Electron）一键切换。
- **丰富设置**：支持助手名称、系统提示词、模型参数、背景等多项自定义。

## 目录结构
```
├── live2d-assistant-fe/        # 前端项目（Vue3 + Vite）
│   ├── src/
│   │   ├── components/         # Vue 组件
│   │   ├── pages/             # 页面组件
│   │   ├── types/             # TypeScript 类型定义
│   │   └── utils/             # 工具函数
│   └── ...
├── live2d-assistant-server/    # 后端项目（Python FastAPI）
│   ├── live2d_server/
│   │   ├── router.py          # API 路由
│   │   └── agentic/           # Agent 模块
│   └── ...
├── electron-live2d/            # Electron 桌面端
├── Makefile
└── README.md
```

## 安装与运行

### 前端
```bash
cd live2d-assistant-fe
npm install
npm run dev          # 开发服务器 (localhost:5173)
npm run build        # 生产构建
```

### 后端
```bash
cd live2d-assistant-server
uv sync
uv run fastapi run main.py --host 0.0.0.0 --port 8000 --static_path ../live2d-assistant-fe/dist
```

### Electron 桌面端
```bash
cd electron-live2d
npm install
npm run start        # 开发模式
npm run package      # 打包
```

## Agent 系统

项目采用 **agentic-agents** 多代理架构：

### 核心概念
- **Router Agent**：入口接待员，理解用户意图并分发任务
- **专家 Agent**：执行具体任务，如需协作可 transfer_to_Router

### Agent 配置
```typescript
interface AgentConfig {
  name: string;         // Agent 名称
  description: string; // Agent 描述
  prompt?: string;      // Agent 专属提示词
}
```

### SSE 事件格式
- `{"type": "text", "content": "..."}` - 文本响应
- `{"type": "tool_calls", "content": [...]}` - 工具调用
- `{"type": "done"}` - 结束
- `{"type": "error", "content": "..."}` - 错误

## License
MIT
