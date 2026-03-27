"""
Agent 工厂：根据 AgentMeta 动态构建 agentic-agents Agent 实例。
"""

import logging
from agentic_agents import Agent, OpenAIClient, AnthropicClient
from agentic_agents.llm.base import LLMClient
from agentic_agents.agents import AgentMeta

logger = logging.getLogger(__name__)


class GoogleAIClient(LLMClient):
    """
    Gemini LLM 客户端，使用 Google Generative Language API。
    """

    def __init__(self, model: str, api_key: str, **kwargs):
        self.model = model
        self.api_key = api_key
        self.base_url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/{model}"
        )

    async def chat(
        self,
        messages: list[dict],
        tools: list[dict] | None = None,
        **kwargs,
    ):
        import httpx
        import json
        from agentic_agents.llm.base import AgentMessage, ChatResult, ToolCall

        contents = []
        system_instruction = None
        for msg in messages:
            role = msg.get("role")
            content = msg.get("content", "")

            if role == "system":
                system_instruction = content
            elif role == "user":
                parts = [{"text": content}] if content else []
                contents.append({"role": "user", "parts": parts})
            elif role == "assistant":
                parts = []
                if content:
                    parts.append({"text": content})
                if msg.get("tool_calls"):
                    for tc in msg["tool_calls"]:
                        func = tc.get("function", {})
                        args = func.get("arguments", {})
                        if isinstance(args, str):
                            args = json.loads(args)
                        parts.append({
                            "functionCall": {
                                "name": func.get("name", ""),
                                "args": args,
                            }
                        })
                contents.append({"role": "model", "parts": parts})
            elif role == "tool":
                parts = [{"text": content}]
                contents.append({"role": "user", "parts": parts})

        body: dict = {"contents": contents}
        if system_instruction:
            body["systemInstruction"] = {"parts": [{"text": system_instruction}]}

        if tools:
            declarations = []
            for t in tools:
                func = t.get("function", t)
                declarations.append({
                    "name": func["name"],
                    "description": func.get("description", ""),
                    "parameters": func.get(
                        "parameters",
                        {"type": "object", "properties": {}},
                    ),
                })
            body["tools"] = [{"functionDeclarations": declarations}]

        url = f"{self.base_url}:generateContent?key={self.api_key}"
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(url, json=body)
            resp.raise_for_status()
            data = resp.json()

        candidate = data.get("candidates", [{}])[0]
        content_blocks = candidate.get("content", {}).get("parts", [])

        text_parts = []
        tool_calls = []
        for block in content_blocks:
            if "text" in block:
                text_parts.append(block["text"])
            elif "functionCall" in block:
                fc = block["functionCall"]
                tool_calls.append(ToolCall(
                    id="gc_" + fc.get("name", ""),
                    name=fc.get("name", ""),
                    arguments=fc.get("args", {}),
                ))

        return ChatResult(
            message=AgentMessage(
                role="assistant",
                content="\n".join(text_parts),
                tool_calls=tool_calls,
            ),
            raw=data,
        )

    def supports_tools(self) -> bool:
        return True


def create_llm(provider: str, model: str, api_key: str, base_url: str) -> LLMClient:
    """根据模型名称创建对应的 LLM 客户端"""
    if provider.lower() in ['openai', 'openai_compatible']:
        return OpenAIClient(model=model, api_key=api_key, base_url=base_url)
    elif provider.lower() == 'anthropic':
        return AnthropicClient(model=model, api_key=api_key, base_url=base_url)
    else:
        raise ValueError(f"Unsupported LLM provider: {provider}")

async def build_single_agent(
    config: AgentMeta,
    llm: LLMClient,
) -> Agent:
    """
    根据 AgentMeta 构建单个 agentic-agents Agent。
    """
    from agentic_agents import create_transfer_tool
    from agentic_agents.tools.basic_tools import current_time

    # 固定工具
    tools = [
        create_transfer_tool(
            "Router",
            "当完成当前任务后，使用此工具将控制权交还给 Router。",
        ),
        current_time,
    ]

    # 优先使用 system_prompt，否则使用 duty
    custom_prompt = config.system_prompt or config.duty

    system_prompt = f"""你是一个专业的任务执行代理，名为 {config.name}。

【你的职责】
{custom_prompt}

【工作流程】
1. 理解用户的需求
2. 使用 ReAct 模式完成任务：思考 -> 行动 -> 观察
3. 完成任务后，调用 transfer_to_Router 返回控制权

【重要规则】
1. 用中文回复
2. 不要编造信息，不知道就说不知道
"""

    return Agent(
        name=config.name,
        description=config.duty,
        llm=llm,
        tools=tools,
        system_prompt=system_prompt,
        max_epochs=50,
    )


async def build_session_agents(
    configs: list[AgentMeta],
    llm: LLMClient,
) -> dict[str, Agent]:
    """
    根据 AgentMeta 列表构建所有 Agent，返回 {name: Agent} 字典。
    """
    from agentic_agents import create_transfer_tool

    agents: dict[str, Agent] = {}

    for cfg in configs:
        agents[cfg.name] = await build_single_agent(cfg, llm)

    # 构建 Router Agent
    router_tools = [
        create_transfer_tool(
            cfg.name,
            f"当用户提出与 {cfg.duty} 相关的问题或任务时，转交给 {cfg.name}。",
        )
        for cfg in configs
    ]
    router_tools.append(create_transfer_tool(
        "Router",
        "当你自己可以回答或处理用户的问题时使用。",
    ))

    agents["Router"] = Agent(
        name="Router",
        description="多代理系统的入口接待员，负责理解用户意图并分发任务。",
        llm=llm,
        tools=router_tools,
        system_prompt=f"""你是一个多智能体系统的接待员 (Router)。
可用专家代理：
{chr(10).join([f"- {cfg.name}: {cfg.duty}" for cfg in configs])}

请理解用户的意图，使用对应的 transfer 工具分发任务。
如果用户只是闲聊或打招呼，可以直接回答。
所有回答请使用中文。""",
        max_epochs=50,
    )

    return agents
