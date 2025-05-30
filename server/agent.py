from typing import Annotated, Literal, Optional
from langgraph.graph import StateGraph, START, Graph
from langgraph.graph.graph import CompiledGraph
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import Command, interrupt
from langgraph.prebuilt import InjectedState
from langchain_openai import ChatOpenAI
from langchain_core.tools import InjectedToolCallId, BaseTool, tool
from pydantic import BaseModel
from typing import Any
from langchain_core.messages import ToolMessage, HumanMessage
from client import MCPClient
import logging
from mcp_tool_helper import new_convert_mcp_tool_to_langchain_tool
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages
from typing import TypedDict

logging.basicConfig(level=logging.INFO)

logger = logging.getLogger(__name__)

# class MessagesState(TypedDict):
#     messages: list[dict]
#     # messages: ÷÷Annotated[list, add_messages]

class MessagesState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    waiting_for_input: bool  # 添加中断状态标志
    thread_id: str  # 添加线程ID用于中断恢复

class Assistant(BaseModel):
    name: str
    description: str
    tools: list[Any]
    prompt: str

class ToolResouce(BaseModel):
    """定义一个工具资源
    
    用于指定将从何处初始化工具
    """
    source: Literal["mcp", "local", "langchain"] # 工具源, mcp: 从指定的MCP服务器获取工具, local: 从本地的Python文件获取工具
    mcp_server: Optional[str] = None # MCP 服务器的名称，该服务器应该被首先定义
    local_tool_path: Optional[str] = None # 本地工具路径，该路径应该是一个Python文件，该文件应该包含一个或多个可被导出的函数
    tool: Optional[Any] = None # 工具，该工具应该是一个LangChain工具

class AgentConfig(BaseModel):
    """定义一个Agent配置

    程序将使用该配置动态生成一个Agent，并最终集成到MultiAgent中
    """
    name: str # 助手名称
    description: str # 助手描述
    tools: list[ToolResouce] # 助手工具
    prompt: str # 助手提示词
    hands_off: list[str] # 助手可以跳转的节点，如果为空，则助手将无法转交控制权

class SingleAgent:
    def __init__(self, mcp_client: MCPClient, llm: ChatOpenAI, model_name: str, config: AgentConfig, prompt_prefix: str):
        self.mcp_client = mcp_client
        self.llm = llm
        self.model_name = model_name
        self.config = config
        self.tools = []
        self.prompt_prefix = prompt_prefix
        self.system_prompt = self.make_system_prompt()
        self.mcp_tools = {}

    def make_system_prompt(self) -> str:
        return (f"""{self.prompt_prefix}
---
{self.config.prompt}
    """)
    
    async def __make_agent_tools__(self) -> list[BaseTool]:
        tools = []
        for tool_resource in self.config.tools:
            if tool_resource.source == "langchain":
                tools.append(await self.__create_langchain_tools__(tool_resource))
            elif tool_resource.source == "mcp":
                tools.extend(await self.__create_mcp_tools__(tool_resource.mcp_server))
            else:
                raise ValueError(f"不支持的工具源: {tool_resource.source}")
        tools.append(await self.__create_interrupt_tool__())
        tools.extend(await self.__create_hands_off_tool__())
        return tools
    
    async def __create_mcp_tools__(self, mcp_server: str) -> list[BaseTool]:
        tools = await self.mcp_client.list_tools(mcp_server)
        converted_tools = []
        for tool_ in tools.tools:
            t = new_convert_mcp_tool_to_langchain_tool(session=await self.mcp_client.get_client_session(mcp_server), tool=tool_)
            converted_tools.append(t)
            self.mcp_tools[tool_.name] = (tool_, mcp_server)
        return converted_tools
    
    async def __create_hands_off_tool__(self) -> list[BaseTool]:
        """创建一个跳转工具
        
        该工具用于将控制权移交给其他助手
        """
        tools = []
        for goto in self.config.hands_off:
            t = await self.__create_transfer_to_goto_tool__(goto)
            tools.append(t)
        return tools
    
    async def __create_transfer_to_goto_tool__(self, goto: str) -> BaseTool:
        name = "transfer_to_" + goto
        description = f"将控制权移交给 {goto} 助手， 由 {goto} 助手来继续完成任务。"
        @tool(name, description=description)
        def transfer_to_goto(
            state: Annotated[MessagesState, InjectedState], 
            tool_call_id: Annotated[str, InjectedToolCallId],) -> Command:
            tool_message = {
                "role": "tool",
                "content": f"已经将控制权移交给 {goto} 助手。",
                "tool_call_id": tool_call_id,
                "name": name,
            }
            return Command(  
                goto=goto,
                update={"messages": state["messages"] + [tool_message]},  
                graph=Command.PARENT,  
            )
        return transfer_to_goto

    async def __create_langchain_tools__(self, tool_: ToolResouce) -> BaseTool:
        return tool_.tool
    
    async def __create_interrupt_tool__(self) -> BaseTool:
        name = "request_user_input"
        description = "中断当前任务，等待用户补充更多的信息。"
        @tool(name, description=description)
        def interrupt_tool(
            state: Annotated[MessagesState, InjectedState], 
            tool_call_id: Annotated[str, InjectedToolCallId],
            prompt: str = "请提供更多信息") -> Command:
            logger.info(f"agent {self.config.name} 使用 interrupt_tool 工具: {prompt}")
            state["waiting_for_input"] = True  
            user_input = interrupt({"prompt": prompt})
            logger.info(f"agent {self.config.name} 用户输入: {user_input}")
            # 设置中断状态
            # 创建中断消息
            tool_message = ToolMessage(
                content=f"{user_input}",
                tool_call_id=tool_call_id,
                name=name
            )
            return Command(
                goto='call_model',
                update={"messages": state["messages"] + [tool_message], "waiting_for_input": False}
            )
        return interrupt_tool

    async def call_model(self, state: MessagesState) -> Command[Literal["call_tools", "__end__"]]:
        messages = state["messages"]
        if self.system_prompt:
            messages = [{"role": "system", "content": self.system_prompt}] + messages

        response = await self.llm_with_tools.ainvoke(messages)
        if len(response.tool_calls) > 0:
            return Command(goto="call_tools", update={"messages": [response]})

        return {"messages": [response]}
    
    async def call_tools(self, state: MessagesState) -> Command[Literal["call_model"]]:
        tool_calls = state["messages"][-1].tool_calls
        results = []
        for tool_call in tool_calls:
            if tool_call["name"] in self.mcp_tools:
                # 直接使用mcp的调用方式
                tool_, server_name = self.mcp_tools[tool_call["name"]]
                resp = await self.mcp_client.call_tool(tool_call['name'], tool_call['args'], tool_call['id'], server_name=server_name)
                results.append(Command(update={"messages": [resp]}))
            else:
                tool_ = self.tools_by_name[tool_call["name"]]
                tool_input_fields = tool_.get_input_schema().model_json_schema()["properties"]

                # this is simplified for demonstration purposes and
                # is different from the ToolNode implementation
                if "state" in tool_input_fields:
                    # inject state
                    tool_call = {**tool_call, "args": {**tool_call["args"], "state": state}}

                tool_response = await tool_.ainvoke(tool_call)
                if isinstance(tool_response, ToolMessage):
                    results.append(Command(update={"messages": [tool_response]}))

                # handle tools that return Command directly
                elif isinstance(tool_response, Command):
                    results.append(tool_response)

        # NOTE: nodes in LangGraph allow you to return list of updates, including Command objects
        return results

    async def build(self) -> CompiledGraph:
        graph = await self.pre_build()
        return graph.compile()

    async def pre_build(self) -> Graph:
        tools = await self.__make_agent_tools__()
        self.tools = tools
        # self.tools_by_name = {tool.function.name: tool for tool in tools}
        self.tools_by_name = {tool.name: tool for tool in tools}
        self.llm_with_tools = self.llm.bind_tools(tools)
        graph = StateGraph(MessagesState)
        graph.add_node(self.call_model)
        graph.add_node(self.call_tools)
        graph.add_edge(START, "call_model")
        graph.add_edge("call_tools", "call_model")
        logger.info(f"构建{self.config.name}的Agent完成")
        logger.info(f"Agent的系统提示词: {self.system_prompt}")
        logger.info(f"Agent的工具: {[tool.name for tool in tools]}")
        return graph
    
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
        decision_maker = await __create_decision_maker__(self.mcp_client, self.llm, self.model_name, self.agents)
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

async def __create_decision_maker__(mcp_client: MCPClient, llm: ChatOpenAI, model_name: str, assistants: list[AgentConfig]) -> SingleAgent:
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