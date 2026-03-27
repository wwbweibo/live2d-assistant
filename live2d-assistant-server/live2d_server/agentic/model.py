# Re-export from agentic-agents
from agentic_agents.agents import AgentMeta, AgentConfig
from agentic_agents.agents.agent_meta import MCPServerConfig
from pydantic import BaseModel


class SkillMeta(BaseModel):
    """技能元信息，与 agentic-agents Skill dataclass 的可配置部分对齐."""
    name: str
    description: str
    instruction: str


__all__ = ["AgentMeta", "AgentConfig", "MCPServerConfig", "SkillMeta"]
