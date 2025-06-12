from typing import Annotated, Literal
from langgraph.graph import StateGraph, START, Graph
from langgraph.graph.graph import CompiledGraph
from langgraph.types import Command, interrupt
from langgraph.prebuilt import InjectedState
from langchain_openai import ChatOpenAI
from langchain_core.tools import InjectedToolCallId, BaseTool, tool
from langchain_core.messages import ToolMessage
from live2d_server.client import MCPClient
import logging
from live2d_server.mcp_tool_helper import new_convert_mcp_tool_to_langchain_tool
from live2d_server.agent.model import AgentConfig, MessagesState, ToolResouce
from live2d_server.agent.tools_loader import load_tools_from_local_file, load_tools_from_python_code
from live2d_server.agent.prebuild import prebuild_tools

logger = logging.getLogger(__name__)

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
            elif tool_resource.source == "prebuild":
                tools.append(await self.__create_prebuild_tools__(tool_resource.prebuild_name))
            elif tool_resource.source == "local_file":
                tools.extend(await load_tools_from_local_file(tool_resource.local_file_path))
            elif tool_resource.source == "python":
                tools.extend(await load_tools_from_python_code(tool_resource.python_code))
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
    
    async def __create_prebuild_tools__(self, prebuild_name: str) -> BaseTool:
        return prebuild_tools[prebuild_name]
    
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