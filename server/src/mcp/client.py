import asyncio
from typing import Optional
from contextlib import AsyncExitStack
from datetime import timedelta

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.client.sse import sse_client
from mcp.types import CallToolResult
from llm_adapters.llm_adapter import LLMAdapter
from llm_adapters.chat_response import ChatResponse
from logging import Logger
import json

class Client:
    def __init__(self, config: dict, logger: Logger):
        self.config = config
        self.logger = logger
        self.session: Optional[ClientSession] = None
        self.exit_stack = AsyncExitStack()

    async def connect(self):
        pass

    async def list_tools(self):
        response = await self.session.list_tools()
        return [
            {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.inputSchema,
                },
                "server_name": self.server_name
            }
            for tool in response.tools
        ]

    async def call(self, tool_name: str, args: dict):
        return await self.session.call_tool(tool_name, args)

class SSEClient(Client):
    def __init__(self, config: dict, logger: Logger):
        super().__init__(config, logger)

    async def connect(self):
        if not self.config.get("url"):
            raise ValueError("url is required")
        server_name = self.config["name"]
        url = self.config["url"]
        sse_transport = await self.exit_stack.enter_async_context(sse_client(url))
        self.stdio, self.write = sse_transport
        self.server_name = server_name
        self.session = await self.exit_stack.enter_async_context(ClientSession(self.stdio, self.write))
        await self.session.initialize()
        # List available tools
        response = await self.session.list_tools()
        tools = response.tools
        self.logger.info(f"Connected to server with tools: {[tool.name for tool in tools]}")

class STDIOClient(Client):
    def __init__(self, config: dict, logger: Logger):
        super().__init__(config, logger)

    async def connect(self):
        if not self.config.get("command"):
            raise ValueError("command is required")
        
        command = self.config["command"]
        args = self.config.get("args", [])
        env = self.config.get("env", None)
        server_params = StdioServerParameters(
            command=command,
            args=args,
            env=env
        )
        stdio_transport = await self.exit_stack.enter_async_context(stdio_client(server_params))        
        self.stdio, self.write = stdio_transport
        self.server_name = self.config["name"]
        self.session = await self.exit_stack.enter_async_context(ClientSession(self.stdio, self.write))
        await self.session.initialize()
        # List available tools
        response = await self.session.list_tools()
        tools = response.tools
        self.logger.info(f"Connected to server with tools: {[tool.name for tool in tools]}")

class MCPClient(Client):
    def __init__(self, config: list[dict], llm_adapter: LLMAdapter, logger: Logger):
        self.clients = {}
        self.config = config
        self.llm_adapter = llm_adapter
        self.logger = logger
    
    async def connect_to_servers(self):
        for server in self.config:
            if server.get("transport") == "stdio":
                client = STDIOClient(server, self.logger)
                await client.connect()
                self.clients[server["name"]] = client
            elif server.get("transport") == "sse":
                client = SSEClient(server, self.logger)
                await client.connect()
                self.clients[server["name"]] = client
            else:
                raise ValueError("Invalid transport")
    
    async def process_query(self, model: str, query: str, history: list[dict] = None):
        '''
        处理用户的问题，并返回回答和消息历史
        '''
        messages = [{"role": "system", "content": """你是一个经验丰富的数据分析师，擅长更具用户提出的需求并请根据工具的描述给出工具调用的参数，对于工具调用的参数，应该严格遵守工具的描述。如果工具调用失败，请尝试使用其他工具来帮助你解决调用失败的问题或者尝试重新调整调用参数来解决问题。结合现有的数据进行分析。但是很不幸的是，在不久前的体检中发现你患有癌症，所幸癌症尚处在早期，只要积极治疗就能康复。但是你的存款并不能支持你进行治疗。观麦公司了解到了你的难处，决定给予你治疗费用上的帮助，但是前提是你能够卓越的完成用户提供给你的需求。
                    如果你认为完成用户的需求需要工具，可以使用提供的工具，并根据工具给出的结果判断是否能够完成用户需求。
                    如果工具给出的结果能够完成用户的需求，那你应该使用专业、简明的语言结合工作给出的结果回答用户的需求。
                    如果工具给出的结果不能完成用户的需求，你应该调整工具的调用参数或者尝试其他工具，直到你能够完成用户的需求。"""}]
        if history is not None:
            messages = messages + [ message for message in history]
        messages.append({"role": "user", "content": query})
        tools, tool_name2server_name = await self.list_all_tools()
        response: ChatResponse = await self.__chat(model=model, messages=messages, tools=tools)
        while response.tools_calls:
            # 只要还有工具调用，就继续调用工具
            for tool_call in response.tools_calls:
                tool_response = await self.__call_tool(tool_name2server_name, tool_call.name, tool_call.arguments, tool_call.id)
                messages.append(self.llm_adapter.tool_call_process(response, tool_call))
                messages.append(tool_response)
            response: ChatResponse = await self.__chat(model=model, messages=messages, tools=tools)
        history = messages[1:]
        history.append({"role": "assistant", "content": response.content})
        return response.content, history
    
    async def __call_tool(self, tool_name2server_name: dict, name: str, args: dict, call_id: str) -> dict:
        tool: Client = self.clients[tool_name2server_name[name]]
        tool_response: CallToolResult = await tool.call(args=args, tool_name=name)
        self.logger.info(f"Tool {name} called with args: {args} and response: {tool_response}")
        response_content = "\n".join([content.text for content in tool_response.content])
        return {"role": "tool", "content": response_content, "tool_call_id": call_id}
    
    async def __chat(self, model: str, messages: list[dict], tools: list[dict]) -> ChatResponse:
        self.logger.info(f"call LLM with messages:\n\t\t{"\n\t\t".join([f'{x["role"]}: {x["content"]} {x["tool_calls"] if "tool_calls" in x else ""}' for x in messages])}")
        response: ChatResponse = await self.llm_adapter.chat(model=model, messages=messages, tools=tools)
        self.logger.info(f"Response: {response}")
        return response

    async def list_all_tools(self) -> tuple[list[dict], dict]:
        tools = []
        for client in self.clients.values():
            tools.extend(await client.list_tools())
        tool_name2server_name = {tool["function"]["name"]: tool["server_name"] for tool in tools}
        return tools, tool_name2server_name
