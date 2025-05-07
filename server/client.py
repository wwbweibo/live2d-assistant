from typing import Optional, abstractmethod,  Literal
from typing_extensions import overload
from contextlib import AsyncExitStack
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.client.sse import sse_client
from mcp.types import CallToolResult
from chat_response import ChatResponse
from openai_adapter import OpenAIAdapter
from typing import AsyncGenerator
import logging
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class MCPServerConfig(BaseModel):
    name: str
    transport: Literal["stdio", "sse"]
    url: Optional[str] = None
    command: Optional[str] = None
    args: Optional[list[str]] = None
    env: Optional[dict[str, str]] = None

class LLMConfig(BaseModel):
    provider: str
    api_key: str
    base_url: str = Field(default="https://api.openai.com/v1")
    sys_prompt: Optional[str] = None

class MCPClientConfig(BaseModel):
    mcp_servers: list[MCPServerConfig]
    llm: LLMConfig

class Client:
    __config: MCPServerConfig
    __session: Optional[ClientSession] = None
    __exit_stack: AsyncExitStack
    __server_name: str

    def __init__(self, config: MCPServerConfig):
        self.__config = config
        self.__session: Optional[ClientSession] = None
        self.__exit_stack = AsyncExitStack()
        self.__server_name = config.name
    
    @abstractmethod
    async def connect(self):
        ...

    async def list_tools(self):
        response = await self.__session.list_tools()
        return [
            {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.inputSchema,
                },
                "server_name": self.__server_name
            }
            for tool in response.tools
        ]

    async def call(self, tool_name: str, args: dict):
        return await self.__session.call_tool(tool_name, args)

class SSEClient(Client):
    def __init__(self, config: MCPServerConfig):
        super().__init__(config)

    async def connect(self):
        if not self.__config.url:
            raise ValueError("url is required")
        url = self.__config.url
        sse_transport = await self.__exit_stack.enter_async_context(sse_client(url))
        self.__stdio, self.__write = sse_transport
        self.__session = await self.__exit_stack.enter_async_context(ClientSession(self.__stdio, self.__write))
        await self.__session.initialize()
        # List available tools
        response = await self.__session.list_tools()
        tools = response.tools
        logger.info(f"Connected to server with tools: {[tool.name for tool in tools]}")

class STDIOClient(Client):
    def __init__(self, config: MCPServerConfig):
        super().__init__(config)

    async def connect(self):
        if not self.__config.command:
            raise ValueError("command is required")
        
        command = self.__config.command
        args = self.__config.args
        env = self.__config.env
        server_params = StdioServerParameters(
            command=command,
            args=args,
            env=env
        )
        stdio_transport = await self.__exit_stack.enter_async_context(stdio_client(server_params))        
        self.__stdio, self.__write = stdio_transport
        self.__session = await self.__exit_stack.enter_async_context(ClientSession(self.__stdio, self.__write))
        await self.__session.initialize()
        # List available tools
        response = await self.__session.list_tools()
        tools = response.tools
        logger.info(f"Connected to server with tools: {[tool.name for tool in tools]}")

class MCPClient(Client):
    __clients: dict[str, Client] = {}
    __config: MCPClientConfig
    __llm_adapter: OpenAIAdapter

    def __init__(self, config: MCPClientConfig):
        self.__clients = {}
        self.__config = config
        self.__llm_adapter = OpenAIAdapter(config.llm.provider, config.llm.api_key, config.llm.base_url)
    
    async def connect_to_servers(self):
        for server in self.__config.mcp_servers:
            if server.transport == "stdio":
                client = STDIOClient(server)
                await client.connect()
                self.__clients[server.name] = client
            elif server.transport == "sse":
                client = SSEClient(server)
                await client.connect()
                self.__clients[server["name"]] = client
            else:
                raise ValueError("Invalid transport")
    
    async def process_query(self, model: str, query: str, history: list[dict] = None):
        '''
        处理用户的问题，并返回回答和消息历史
        '''
        messages = [{"role": "system", "content": self.__config.llm.sys_prompt}]
        if history is not None:
            messages = messages + [ message for message in history]
        messages.append({"role": "user", "content": query})
        tools, tool_name2server_name = await self.list_all_tools()
        response: ChatResponse = await self.__chat(model=model, messages=messages, tools=tools)
        logger.info(f"Response: {response}")
        while response.tool_calls:
            # 只要还有工具调用，就继续调用工具
            for tool_call in response.tool_calls:
                tool_response = await self.__call_tool(tool_name2server_name, tool_call.name, tool_call.arguments, tool_call.id)
                messages.append(self.__llm_adapter.tool_call_process(response, tool_call))
                messages.append(tool_response)
            response: ChatResponse = await self.__chat(model=model, messages=messages, tools=tools)
        history = messages[1:]
        history.append({"role": "assistant", "content": response.content})
        return response.content, history

    async def stream_process_query(self, model: str, query: str, history: list[dict] = None):
        '''
        流式处理用户的问题
        '''
        messages = [{"role": "system", "content": self.__config.llm.sys_prompt}]
        if history is not None:
            messages = messages + [ message for message in history]
        messages.append({"role": "user", "content": query})
        tools, tool_name2server_name = await self.list_all_tools()
        response = await self.__chat(model=model, messages=messages, tools=tools, stream=True)
        async for chunk in response:
            if chunk.tool_calls:
                # 处理工具调用
                for tool_call in chunk.tool_calls:
                    tool_response = await self.__call_tool(tool_name2server_name, tool_call.name, tool_call.arguments, tool_call.id)
                    messages.append(self.__llm_adapter.tool_call_process(chunk, tool_call))
                    messages.append(tool_response)
                # 继续流式处理
                async for next_chunk in self.__chat(model=model, messages=messages, tools=tools, stream=True):
                    yield next_chunk.content
            else:
                yield chunk.content

    async def __call_tool(self, tool_name2server_name: dict, name: str, args: dict, call_id: str) -> dict:
        tool: Client = self.__clients[tool_name2server_name[name]]
        tool_response: CallToolResult = await tool.call(args=args, tool_name=name)
        logger.info(f"Tool {name} called with args: {args} and response: {tool_response}")
        response_content = "\n".join([content.text for content in tool_response.content])
        return {"role": "tool", "content": response_content, "tool_call_id": call_id}
    
    @overload
    async def __chat(self, model: str, messages: list[dict], tools: list[dict], stream: Literal[True] = True) -> AsyncGenerator[ChatResponse, None]:
        ...

    @overload
    async def __chat(self, model: str, messages: list[dict], tools: list[dict], stream: Literal[False] | None = False) -> ChatResponse:
        ...

    async def __chat(self, model: str, messages: list[dict], tools: list[dict], stream: bool | None = False) -> ChatResponse | AsyncGenerator[ChatResponse, None]:
        logger.info(f"call LLM with messages:\n\t\t{"\n\t\t".join([f'{x["role"]}: {x["content"]} {x["tool_calls"] if "tool_calls" in x else ""}' for x in messages])}")
        if stream:
            return self.__chat_stream(model, messages, tools)
        else:
            return await self.__chat_none_stream(model, messages, tools)

    async def __chat_stream(self, model: str, messages: list[dict], tools: list[dict]) -> AsyncGenerator[ChatResponse, None]:
        resp = await self.__llm_adapter.chat(model=model, messages=messages, tools=tools, stream=True)
        async for chunk in resp:
            yield chunk

    async def __chat_none_stream(self, model: str, messages: list[dict], tools: list[dict]) -> ChatResponse:
        response: ChatResponse = await self.__llm_adapter.chat(model=model, messages=messages, tools=tools)
        return response

    async def list_all_tools(self) -> tuple[list[dict], dict]:
        tools = []
        for client in self.__clients.values():
            tools.extend(await client.list_tools())
        tool_name2server_name = {tool["function"]["name"]: tool["server_name"] for tool in tools}
        return tools, tool_name2server_name
