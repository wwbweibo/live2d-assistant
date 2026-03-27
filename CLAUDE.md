# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概览

**Live2D Assistant** 是一个多端（Web/Electron）助手平台，集成 Live2D 虚拟形象和 AI 对话功能。

```
live2d-assistant/
├── live2d-assistant-fe/     # 前端：Vue 3 + Vite + TypeScript
├── live2d-assistant-server/ # 后端：Python FastAPI (Python 3.12+)
├── electron-live2d/          # Electron 桌面端
├── Makefile
└── CLAUDE.md
```

## 常用命令

### 前端
```bash
cd live2d-assistant-fe
npm install
npm run dev          # 开发服务器 (localhost:5173)
npm run build        # 生产构建 → dist/
```

### 后端
```bash
cd live2d-assistant-server
uv sync              # 安装依赖
uv run fastapi run main.py --host 0.0.0.0 --port 8000 --static_path ../live2d-assistant-fe/dist
```
注意：`--static_path` 指向已构建的前端 `dist/` 目录；去掉该参数则仅启动 API 服务。

### Electron 桌面端
```bash
cd electron-live2d
npm install
npm run start         # 开发模式
npm run package       # 打包桌面应用
```

## 架构

### 前端 → 后端通信
- REST + **SSE 流式响应**（`/api/agentic/chat`）
- 后端 CORS 允许所有来源

### Agent 系统（agentic-agents 多代理）

核心框架：**agentic-agents**（作为 git submodule 引入：`external/agentic-agent`）

核心文件：
- [router.py](live2d-assistant-server/live2d_server/router.py) — API 入口，`/api/agentic/chat` 端点
- [agentic/agent_builder.py](live2d-assistant-server/live2d_server/agentic/agent_builder.py) — Agent 工厂，根据前端 AgentConfig 构建 Agent
- [agentic/model.py](live2d-assistant-server/live2d_server/agentic/model.py) — AgentConfig 数据模型

执行流程：
```
用户输入 → AgentSession → SQLiteSessionStorage 持久化
                        → Router Agent（入口调度）
                        → transfer_to_Router（直接闲聊）
                        → transfer_to_<AgentName>（转交专家）
                        → 专家 Agent 执行任务
                        → transfer_to_Router
                        → 用户接收结果
```

SSE 事件格式：`{"type": "text"|"tool_calls"|"done"|"error"}`

## 依赖说明

后端 Agent 框架：**agentic-agents**（作为 git submodule 引入：`external/agentic-agent`）
- `AgentSession`：会话管理，支持 SQLite 持久化
- `Agent`：单个代理实例，支持 ReAct 执行模式

## 关键配置

### 前端设置（SystemSettings）
存储在 `localStorage`：
```typescript
interface SystemSettings {
  serverUrl: string;
  backgroundPath: string;
  assistantSettings: {
    assistantName: string;
    sysPrompt?: string;
    model: string;        // 如 "qwen2.5"
    baseUrl?: string;     // LLM API 地址
    apiKey?: string;
    agents?: string;      // JSON 数组（AgentConfig）
  };
  live2DSettings: { modelPath, offsetX, offsetY, scale, themeColor };
}
```

### Agent 配置（AgentConfig）
```typescript
interface AgentConfig {
  name: string;         // Agent 名称
  description: string;  // Agent 描述
  prompt?: string;      // Agent 专属提示词
}
```

## 依赖版本要求

- 前端：Node.js
- 后端：**Python 3.12+**（使用 `uv` 管理依赖）

## 推荐阅读顺序（快速上手）

1. [router.py](live2d-assistant-server/live2d_server/router.py) — 后端 API 入口，了解所有端点
2. [agent_builder.py](live2d-assistant-server/live2d_server/agentic/agent_builder.py) — Agent 构建流程
3. [chat.vue](live2d-assistant-fe/src/components/chat.vue) — 前端对话实现，SSE 流式响应
4. [Home.vue](live2d-assistant-fe/src/pages/Home.vue) — 前端页面入口
