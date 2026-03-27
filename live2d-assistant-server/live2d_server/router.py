from fastapi import APIRouter
from fastapi.responses import StreamingResponse
import json
from typing import List, Optional
from pydantic import BaseModel
import logging
from agentic_agents import AgentSession, build_agents
from agentic_agents.session import SQLiteSessionStorage
from agentic_agents.agents import AgentConfig
from agentic_agents.agents.agent_meta import MCPServerConfig
from live2d_server.agentic.agent_builder import create_llm
from live2d_server.agentic.model import SkillMeta
from live2d_server.config_store import (
    get_llm_config,
    update_llm_config,
    get_agents_config,
    update_agents_config,
    delete_agent_by_name,
    get_skills_config,
    upsert_skill,
    delete_skill_by_name,
    get_mcp_servers_config,
    upsert_mcp_server,
    delete_mcp_server_by_name,
    mcp_status,
)

class MCPServerResp(MCPServerConfig):
    """MCP Server 响应模型，包含连接状态和可用工具列表."""
    connected: bool
    tools: list[str] = []

logger = logging.getLogger(__name__)

router = APIRouter()

# ─── 请求/响应模型 ───────────────────────────────────

class LLMConfigRequest(BaseModel):
    """LLM 配置请求"""
    provider: str = "openai_compatible"
    api_key: str = ""
    model: str = "qwen2.5"
    base_url: Optional[str] = None


class ChatRequest(BaseModel):
    """聊天请求"""
    chat_id: str
    message: str
    images: Optional[List[str]] = None

# ─── LLM 配置接口 ───────────────────────────────────

@router.get('/api/settings/llm', response_model=LLMConfigRequest)
async def get_llm_config_api():
    """获取当前 LLM 配置"""
    config = get_llm_config()
    return LLMConfigRequest(**config)


@router.post('/api/settings/llm')
async def update_llm_config_api(config: LLMConfigRequest):
    """更新 LLM 配置"""
    updated = update_llm_config(config.model_dump())
    return {"success": True, "config": updated}


# ─── Agent 配置接口 ─────────────────────────────────

@router.get('/api/settings/agents', response_model=AgentConfig)
async def get_agents_config_api():
    """获取完整的 Agent 配置（包含 metadata、agents、mcp_servers）"""
    config = get_agents_config()
    return AgentConfig(**config)


@router.post('/api/settings/agents')
async def update_agents_config_api(config: AgentConfig):
    """更新完整的 Agent 配置"""
    updated = update_agents_config(config.model_dump())
    return {"success": True, "config": updated}


@router.delete('/api/settings/agents/{name}')
async def delete_agent_config_api(name: str):
    """从配置中删除指定 Agent"""
    success = delete_agent_by_name(name)
    return {"success": success}


# ─── Skill 配置接口 ─────────────────────────────────

@router.get('/api/settings/skills', response_model=list[SkillMeta])
async def get_skills_config_api():
    """获取所有 Skill 配置"""
    skills = get_skills_config()
    return [SkillMeta(**s) for s in skills]


@router.post('/api/settings/skills')
async def upsert_skill_api(skill: SkillMeta):
    """创建或更新单个 Skill"""
    updated = upsert_skill(skill.model_dump())
    return {"success": True, "skill": updated}


@router.delete('/api/settings/skills/{name}')
async def delete_skill_api(name: str):
    """删除指定 Skill"""
    success = delete_skill_by_name(name)
    return {"success": success}


# ─── MCP Server 配置接口 ────────────────────────────

@router.get('/api/settings/mcp-servers', response_model=list[MCPServerResp])
async def get_mcp_servers_config_api():
    """获取所有 MCP Server 配置"""
    servers = get_mcp_servers_config()
    resp = []
    for s in servers:
        try:
            tools = await mcp_status(s["name"])
            resp.append(MCPServerResp(**s, connected=True, tools=[t.name for t in tools]))
        except Exception as e:
            logger.error(f"Failed to connect to MCP server '{s['name']}': {e}")
            resp.append(MCPServerResp(**s, connected=False, tools=[]))
    return resp


@router.post('/api/settings/mcp-servers')
async def upsert_mcp_server_api(server: MCPServerConfig):
    """创建或更新单个 MCP Server"""
    updated = await upsert_mcp_server(server.model_dump(exclude_none=True))
    return {"success": True, "server": updated}


@router.delete('/api/settings/mcp-servers/{name}')
async def delete_mcp_server_api(name: str):
    """删除指定 MCP Server"""
    success = await delete_mcp_server_by_name(name)
    return {"success": success}


# ─── 聊天接口 ────────────────────────────────────────

# Agent 会话缓存，用于处理 agent 再入的问题
_sessions: dict[str, object] = {}


@router.post('/api/agentic/chat')
async def agentic_chat(request: ChatRequest):
    """Agent 入口，使用 agentic-agents 框架"""
    llm_config = get_llm_config()
    db_agent_config= get_agents_config()
    agent_config = AgentConfig(**db_agent_config)
    agent_config.mcp_servers =[MCPServerConfig(**s) for s in get_mcp_servers_config()]
    llm = create_llm(
        llm_config['provider'],
        llm_config["model"],
        llm_config["api_key"],
        llm_config["base_url"] or ""
    )
    storage = SQLiteSessionStorage(
        session_id=request.chat_id,
        db_path="./.sessions/sessions.db",
    )
    logger.info(f"building agents with config: {agent_config.model_dump()}")
    session = AgentSession(
        session_id=request.chat_id,
        agent_factory=build_agents,
        storage=storage,
        agent_config=agent_config,
        llm=llm,
    )
    async def _process():
        try:
            async for event in session.process_message(request.message):
                yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
        except Exception as e:
            import traceback
            traceback.print_exc()
            logger.error(f"Error in agentic_chat: {traceback.format_exc()}")
            yield f"data: {json.dumps({'type': 'error', 'content': f'Internal server error: {str(e)}'}, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        _process(),
        media_type="text/event-stream",
    )


@router.get('/health')
async def health():
    return {'status': 'OK'}
