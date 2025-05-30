# Live2D Assistant

## 项目简介

**Live2D Assistant** 是一个集成了 Live2D 虚拟形象、AI 智能对话、插件化工具调用能力的多端（Web/Electron 桌面）助手平台。项目支持自定义 Live2D 模型、AI 大语言模型（LLM）接入、TTS 语音合成、MCP 多工具服务器扩展，适合二次元互动、AI 助手、智能桌搭等多种场景。

## 主要特性
- 🎨 **Live2D 虚拟形象**：支持自定义模型、背景、缩放与位置调整。
- 🤖 **AI 智能对话**：通过OpenAi适配接口集成多种 LLM（如 Qwen、Ollama、本地/云端 OpenAI 等），支持上下文多轮对话。
- 🔍 **Web 搜索 (WIP)**：支持通过 Web 搜索获取信息。
- 🗣️ **TTS 语音合成 (WIP)**：可选集成语音播报，支持 CosyVoice、ChatTTS 等。
- 🧩 **MCP 插件扩展**：支持通过 MCP 协议扩展音乐播放、搜索、RAG 检索等工具。
- 🖥️ **多端支持**：Web 端（Vite+Vue3）、桌面端（Electron）一键切换。
- 🛠️ **丰富设置**：支持助手名称、系统提示词、模型参数、背景等多项自定义。

## 目录结构
```
├── src/                # 前端主代码（Vue3）
│   ├── pages/          # 页面（如 Home.vue）
│   ├── components/     # 组件（如 chat、settings 等）
│   └── ...
├── server/             # 后端服务（FastAPI，Python）
│   ├── server.py       # 主服务入口
│   ├── client.py       # MCP 客户端与 LLM 适配
│   ├── router.py       # API 路由
│   └── ...
├── electron-live2d/    # Electron 桌面端
│   ├── src/            # Electron 主进程与服务
│   └── ...
├── package.json        # 前端依赖与脚本
├── requirements.txt    # 后端依赖
├── Makefile            # 构建脚本
└── README.md           # 项目说明
```

## 安装与运行

### 1. 前端 Web 版
```bash
# 安装依赖
npm install
# 启动开发环境
npm run dev
# 构建生产包
npm run build
```

### 2. 桌面 Electron 版
```bash
cd electron-live2d
npm install
# 启动 Electron 桌面端
npm run start
# 打包桌面应用
npm run package
```

### 3. 后端服务（Python FastAPI）
```bash
# 建议使用虚拟环境
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
# 启动后端服务，请确保 config.json 配置正确
python server/server.py --config electron-live2d/src/config.json
```

## 配置说明
- **Live2D 模型与背景**：可在前端设置页面自定义模型路径、缩放、偏移、背景图片。
- **AI 助手参数**：支持自定义助手名称、系统提示词、模型类型、API Key、Base URL 等。
- **MCP 工具服务器**：可在 config.json 中添加自定义工具服务器（如音乐播放器、RAG 检索等）。

## 扩展与 MCP 服务
- 项目支持通过 MCP 协议扩展工具能力，你可以通过 MCP 协议扩展更多工具。

mcp的示例配置如下
```json
[
  {
    "name": "music_player",
    "transport": "sse",
    "url": "http://127.0.0.1:8000/erp-mcp/sse"
  }
]
```
## 依赖说明
- 前端：Vue3、Vite、Ant Design Vue、Element Plus、pixi.js、pixi-live2d-display 等
- 后端：FastAPI、Uvicorn、Pydantic、Ollama、OpenAI、LangChain、Torch、Selenium、BeautifulSoup4 等
- 桌面端：Electron、Express、fs-extra、node-fetch 等

## 常见问题

TODO

## 开发计划
- [x] Live2D 模型支持
- [x] 多轮对话支持
- [x] MCP 工具集成
- [x] 可拓展的 multi-agent 支持
- [ ] Streamable mcp 支持
- [ ] 支持 TTS 语音合成
- [ ] 支持 Web 搜索
- [ ] 本地知识库支持

## License
MIT 