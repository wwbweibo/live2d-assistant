# Copilot Instructions — Live2D Assistant

## Project Overview

Multi-platform (Web/Electron) assistant with Live2D avatar + AI chat, powered by a multi-agent system.

```
live2d-assistant-fe/        → Vue 3 + Vite + TypeScript (UI)
live2d-assistant-server/    → Python FastAPI (API + Agent orchestration)
  external/agentic-agent/   → git submodule: agentic-agents framework
electron-live2d/            → Electron desktop shell
```

## Build & Run

### Frontend
```bash
cd live2d-assistant-fe
npm install && npm run dev          # dev → localhost:5173
npm run build                       # prod → dist/
```

### Backend
```bash
cd live2d-assistant-server
uv sync
uv run fastapi run main.py --host 0.0.0.0 --port 8000
# Add --static_path ../live2d-assistant-fe/dist to serve frontend
```

### Electron
```bash
cd electron-live2d && npm install && npm run start
```

## Architecture

### Communication
- REST API + **SSE streaming** (`POST /api/agentic/chat`)
- CORS: allow all origins

### SSE Event Format (from `AgentSession.process_message()`)

Events use `resp_type` field:

| `resp_type`    | Payload fields                                  | Description            |
|----------------|-------------------------------------------------|------------------------|
| `status`       | `content`                                       | Agent thinking status  |
| `text`         | `agent`, `content`                              | Streamed text output   |
| `tool_result`  | `agent`, `content`                              | Tool execution result  |
| `transfer`     | `from_agent`, `to_agent`, `reason`              | Agent handoff          |
| `error`        | `content`                                       | Error message          |
| `finished`     | `content`                                       | Task complete          |

### Agent System

**Framework**: `agentic-agents` (submodule at `external/agentic-agent`)

**Flow**: User → `AgentSession` → Router Agent → `transfer_to_<Name>()` → Specialist Agent → `transfer_to_Router()` → done

**Key abstractions**: `Agent`, `AgentSession`, `LLMClient`, `AgentTool`, `Skill`, `MCPClient`

### Config Storage

SQLite single-row JSON blob pattern in `config_store.py`:
- `llm_config` — provider, api_key, model, base_url
- `agents_config` — full AgentConfig JSON (metadata + agents + mcp_servers)
- `skills_config` — SkillMeta list
- `mcp_servers_config` — MCPServerConfig list

API: `GET/POST/DELETE /api/settings/{llm|agents|skills|mcp-servers}`

## Conventions

### Frontend
- **Components**: snake_case `.vue` files, PascalCase in template references
- **CSS**: Scoped CSS with CSS variable design tokens from `style.css` ("Aurora Glass" theme)
  - Glass effects: `rgba(255,255,255,0.6)` bg + `backdrop-filter: blur()`
  - Primary color: `#6366f1` (indigo), exposed as `var(--color-primary)`
  - Spacing: `var(--space-{xs|sm|md|lg|xl})`, Radius: `var(--radius-{sm|md|lg})`
- **UI Libraries**: ant-design-vue + ant-design-x-vue (chat bubbles), element-plus (legacy collapse)
- **API calls**: Native `fetch()` in `src/utils/configApi.ts`, env-driven `API_URL`
- **State**: Component-level `ref()`/`reactive()`, `localStorage` for system settings
- **Settings tabs pattern**: Each tab = standalone component with glass header bar + glass content wrapper

### Backend
- **Framework**: FastAPI with Pydantic models
- **Python**: 3.12+ required, managed by `uv`
- **Agent construction**: `agent_builder.py` dynamically creates Router + specialists from DB config
- **LLM clients**: OpenAI, Anthropic, Google Gemini (custom `GoogleAIClient`)
- **Data models in `agentic/model.py`**: Re-exports from agentic-agents + custom `SkillMeta`

### Shared Data Models

```
AgentMeta:     name, duty, skills[], system_prompt, mcp_servers[]
AgentConfig:   metadata{}, agents[], mcp_servers[]
MCPServerConfig: name, transport, command?, args?, env?, cwd?, url?, auth?, headers?
SkillMeta:     name, description, instruction
LLMConfig:     provider, api_key, model, base_url?
```

## Key Entry Points

| Area | Start here |
|------|------------|
| Backend API | [router.py](live2d-assistant-server/live2d_server/router.py) |
| Agent building | [agent_builder.py](live2d-assistant-server/live2d_server/agentic/agent_builder.py) |
| DB config | [config_store.py](live2d-assistant-server/live2d_server/config_store.py) |
| Chat UI | [chat.vue](live2d-assistant-fe/src/components/chat.vue) |
| Page layout | [Home.vue](live2d-assistant-fe/src/pages/Home.vue) |
| Settings tabs | [setting_modal.vue](live2d-assistant-fe/src/components/setting_modal.vue) |
| CSS tokens | [style.css](live2d-assistant-fe/src/style.css) |
| Agent framework | [external/agentic-agent/](live2d-assistant-server/external/agentic-agent/) |

## Pitfalls

- **Do NOT modify** files under `external/agentic-agent/` — it's a git submodule
- `config_store.py` uses `init_db()` with auto-migration for old table schemas; adding new tables must include init logic there
- Frontend mixes ant-design-vue and element-plus — prefer ant-design-vue for new components
- The `chat_message.vue` component is **legacy** (Options API, Element Plus), not used in current chat flow; `chat.vue` handles everything via `BubbleList`
- `model_settings.vue` is **legacy** — replaced by `llm_settings.vue`
