from langgraph.graph import StateGraph
from langgraph.graph.graph import CompiledGraph
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import interrupt
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from live2d_server.client import MCPClient
import logging
from live2d_server.agent.model import AgentConfig, MessagesState
from live2d_server.agent.single_agent import SingleAgent

from langgraph.types import Command
from typing import Literal


logger = logging.getLogger(__name__)

class Agent:
    def __init__(self,
                model_name: str,
                llm: ChatOpenAI,
                 agents: list[AgentConfig],
                 mcp_client: MCPClient):
        self.agents = agents
        self.llm = llm
        self.model_name = model_name
        self.mcp_client = mcp_client
        self.system_prompt_template = """你是{assistant_name}，一个非常有帮助的AI助手，你的职责是{assistant_description}。
你在和其他的助手一起协作，来完成用户的任务；
下面是其他助手的描述：
{assistants}
---
以下是你执行任务时应该遵循的规则：
1. 请使用 思考-执行-观察 的循环来处理任务、
    1. 思考：思考当前任务需要做什么，以及如何完成任务
    2. 执行：你需要决定是否需要使用工具来完成任务
    3. 观察：根据可能的反馈，调整你的思考和执行
2. 在你做任何事之前，请先给出你的思考
3. 你仅应该关注当前步骤你应该做什么，不要考虑后续步骤
4. 如果需要用户提供更多信息，请使用 request_user_input 工具来询问用户
5. 如果当前步骤你无法完成，请使用工具将控制权移交给【决策者】
6. 如果你已经完成了你的工作，使用工具将控制权移交给【决策者】
"""

    def make_system_prompt_prefix(self, agent: AgentConfig, agents: list[AgentConfig]) -> str:
        decision_maker_desp = "decision_maker: 决策者，负责分步规划任务，并将每一步的任务转交给合适的助手来完成。"
        assistants_desc = "\n".join([f"{assistant.name}: {assistant.description}" for assistant in agents if assistant.name != agent.name and assistant.name in agent.hands_off])
        assistants_desc = decision_maker_desp + "\n" + assistants_desc
        return self.system_prompt_template.format(assistant_name=agent.name, assistant_description=agent.description, assistants=assistants_desc)

    async def __make_agent__(self, agent_config: AgentConfig) -> CompiledGraph:
        agent = SingleAgent(self.mcp_client, self.llm, self.model_name, agent_config, self.make_system_prompt_prefix(agent_config, self.agents))
        return await agent.build()

    async def build(self) -> CompiledGraph:
        """构建一个MultiAgent
        
        该MultiAgent将包含所有助手，并最终集成到MultiAgent中
        """
        graph = StateGraph(MessagesState)
        decision_maker = await create_decision_maker(self.mcp_client, self.llm, self.model_name, self.agents)
        graph.add_node("decision_maker", decision_maker)
        for agent_config in self.agents:
            agent = await self.__make_agent__(agent_config)
            graph.add_node(agent_config.name, agent)
        graph.add_node("interrupt", self.user_input_wait_node)
        graph.set_entry_point("decision_maker")
        graph.add_conditional_edges(
            "interrupt",
            self.should_resume_to_agent,
            {agent.name: agent.name for agent in self.agents} | {"decision_maker": "decision_maker"}
        )
        return graph.compile(checkpointer=MemorySaver())
    
   
    async def user_input_wait_node(self, state: MessagesState) -> dict:
        """中断节点 - 等待用户输入"""
        # 设置中断状态
        state["waiting_for_input"] = True
        logger.info('-'*100)
        logger.info(f"等待用户输入: {state}")
        
        # 使用interrupt暂停工作流
        user_input = interrupt({"prompt": "请提供所需信息"})
        
        # 当用户输入后恢复执行
        if user_input:
            # 添加用户消息到状态
            state["messages"].append(HumanMessage(content=user_input))
            state["waiting_for_input"] = False
        
        return state
    
    def should_resume_to_agent(self, state: MessagesState) -> str:
        """决定中断后恢复到哪个Agent"""
        # 从最后一条消息中提取原始调用Agent
        last_msg = state["messages"][-1]
        if hasattr(last_msg, 'tool_calls') and last_msg.tool_calls:
            for call in last_msg.tool_calls:
                if call["name"] == "request_user_input":
                    # 提取原始调用者
                    return call["args"].get("caller", "decision_maker")
        return "decision_maker"



async def create_decision_maker(mcp_client: MCPClient, llm: ChatOpenAI, model_name: str, assistants: list[AgentConfig]) -> SingleAgent:
    prompt_prefix = """你是decision_maker，一个非常有帮助的AI助手，你的职责是通过用户给出的需求，分步规划任务，并将每一步的任务转交给合适的助手来完成。
你需要表现得更主动，而不是被动地等待用户给出需求。
你将和其他的助手一起协作，来完成用户的任务；
下面是其他助手的描述：
{assistants}
---
以下是你执行任务规划和决策时应该遵循的规则：
1. 请使用 思考-执行-观察 的循环来处理任务、
    1. 思考：思考当前任务需要做什么，以及如何完成任务
    2. 执行：你需要决定是否需要将当前任务转交给其他助手来完成
    3. 观察：根据可能的反馈，调整你的思考和执行
2. 在你做任何事之前，请先给出你的思考
3. 你应该关注全局范围内的思考规划，而不是仅仅关注当前步骤
---
你应该遵循如下的规则来完成任务：
1. 如果用户请求的是一个一般性问题，例如，问候、对话，请直接回答
2. 如果涉及到任务规划，你需要首先输出任务步骤，然后根据步骤来分配任务给其他助手
3. 如果需要用户补充信息，请使用工具将控制权移交给【用户输入】，等待用户补充信息后，再继续执行任务
4. 如果用户需要你完成某个任务，你需要将任务分配给其他助手
5. 如果你认为任务已经完成，请以 END 的格式返回
5. 你可以使用 transfer_to_[助手名称] 的工具来将控制权移交给其他助手
6. 如果需要用户提供更多信息，请使用 request_user_input 工具
"""
    assistants_desc = "\n".join([f"{assistant.name}: {assistant.description}" for assistant in assistants])
    prompt_prefix = prompt_prefix.format(assistants=assistants_desc)
    decision_maker = SingleAgent(
        mcp_client,
        llm,
        model_name,
        AgentConfig(
            name="decision_maker",
            description="决策者，负责决策当前任务是否完成",
            tools=[],
            prompt="""你是一个决策者，负责决策当前任务是否完成。""",
            hands_off=[agent.name for agent in assistants]
        ),
        prompt_prefix
    )
    
    def user_input_wait_node(state: MessagesState) -> Command[Literal["call_model"]]:
        logger.info(f"user_input_wait_node: {state}")
        user_input = interrupt('')
        return {"messages": [{"role": "user", "content": user_input}]}
    
    graph = await decision_maker.pre_build()
    graph.add_node('user_input_wait_node', user_input_wait_node)
    logger.info(f"decision_maker的节点: {graph.nodes}")
    graph.add_edge("user_input_wait_node", "call_model")
    return graph.compile()
