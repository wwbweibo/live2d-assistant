from typing import Optional, abstractmethod,  Literal, AsyncGenerator, overload
from contextlib import AsyncExitStack
from mcp import ClientSession, StdioServerParameters, ListToolsResult
from mcp.client.stdio import stdio_client
from mcp.client.sse import sse_client
from mcp.types import CallToolResult
from live2d_server.chat_response import ChatResponse
from live2d_server.openai_adapter import OpenAIAdapter
import logging
import json
from pydantic import BaseModel, Field
from live2d_server.model import Tool, ToolFunction

logger = logging.getLogger(__name__)


class MCPServerConfig(BaseModel):
    name: str
    transport: Literal["stdio", "sse"]
    url: Optional[str] = None
    command: Optional[str] = None
    args: Optional[list[str]] = None
    env: Optional[dict[str, str]] = None

class LLMConfig(BaseModel):
    api_key: str
    base_url: str = Field(default="https://api.openai.com/v1")
    sys_prompt: Optional[str] = None

class MCPClientConfig(BaseModel):
    mcp_servers: list[MCPServerConfig]
    llm: LLMConfig

class Client:
    config: MCPServerConfig
    session: Optional[ClientSession] = None
    exit_stack: AsyncExitStack
    server_name: str

    def __init__(self, config: MCPServerConfig):
        self.config = config
        self.session: Optional[ClientSession] = None
        self.exit_stack = AsyncExitStack()
        self.server_name = config.name
    
    @abstractmethod
    async def connect(self):
        ...

    async def list_tools(self):
        response = await self.session.list_tools()
        return [
            Tool(
                type="function",
                function=ToolFunction(
                    name=tool.name,
                    description=tool.description,
                    parameters=tool.inputSchema,
                ),
                server_name=self.server_name
            )
            for tool in response.tools
        ]
    
    async def list_tools_raw(self) -> ListToolsResult:
        return await self.session.list_tools()

    async def call(self, tool_name: str, args: dict | str):
        if isinstance(args, str):
            args = json.loads(args)
        return await self.session.call_tool(tool_name, args)

class SSEClient(Client):
    def __init__(self, config: MCPServerConfig):
        super().__init__(config)

    async def connect(self):
        if not self.config.url:
            raise ValueError("url is required")
        try: 
            url = self.config.url
            sse_transport = await self.exit_stack.enter_async_context(sse_client(url))
            self.stdio, self.write = sse_transport
            self.session = await self.exit_stack.enter_async_context(ClientSession(self.stdio, self.write))
            await self.session.initialize()
            # List available tools
            response = await self.session.list_tools()
            tools = response.tools
            logger.info(f"Connected to server with tools: {[tool.name for tool in tools]}")
        except Exception as e:
            import traceback
            traceback.print_exc()
            logger.error(f"Failed to connect to server {self.config.name}: {e}")

class STDIOClient(Client):
    def __init__(self, config: MCPServerConfig):
        super().__init__(config)

    async def connect(self):
        if not self.config.command:
            raise ValueError("command is required")
        
        command = self.config.command
        args = self.config.args
        env = self.config.env
        server_params = StdioServerParameters(
            command=command,
            args=args,
            env=env
        )
        stdio_transport = await self.exit_stack.enter_async_context(stdio_client(server_params))        
        self.stdio, self.write = stdio_transport
        self.session = await self.exit_stack.enter_async_context(ClientSession(self.stdio, self.write))
        await self.session.initialize()
        # List available tools
        response = await self.session.list_tools()
        tools = response.tools
        logger.info(f"Connected to server with tools: {[tool.name for tool in tools]}")

class MCPClient:
    __clients: dict[str, Client] = {}
    __config: MCPClientConfig
    __llm_adapter: OpenAIAdapter

    def __init__(self):
        self.__clients = {}
        self.__config = None
        self.__llm_adapter = None

    async def init(self, config: MCPClientConfig):
        self.__config = config
        self.__llm_adapter = OpenAIAdapter('', config.llm.api_key, config.llm.base_url)
        await self.connect_to_servers()
        logger.info(f"MCPClient initialized with config: {config}")

    async def connect_to_servers(self):
        del self.__clients
        self.__clients = {}
        for server in self.__config.mcp_servers:
            try:
                if server.transport == "stdio":
                    client = STDIOClient(server)
                    await client.connect()
                    self.__clients[server.name] = client
                elif server.transport == "sse":
                    client = SSEClient(server)
                    await client.connect()
                    self.__clients[server.name] = client
                else:
                    raise ValueError("Invalid transport")
            except Exception as e:
                logger.error(f"Failed to connect to server {server.name}: {e}")
    
    async def process_query(self, model: str, query: str, history: list[dict] = None):
        '''
        处理用户的问题，并返回回答和消息历史
        '''
        messages = [{"role": "system", "content": self.__config.llm.sys_prompt}]
        if history is not None:
            messages = messages + [ message for message in history]
        messages.append({"role": "user", "content": query})
        tools, tool_name2server_name = await self.list_all_tools()
        response: ChatResponse = await self.chat(model=model, messages=messages, tools=tools, stream=False)
        logger.info(f"Response: {response}")
        while response.tool_calls:
            # 只要还有工具调用，就继续调用工具
            for tool_call in response.tool_calls:
                tool_response = await self.__call_tool(tool_name2server_name, tool_call.name, tool_call.arguments, tool_call.id)
                messages.append(self.__llm_adapter.tool_call_process(response, tool_call))
                messages.append(tool_response)
            response: ChatResponse = await self.chat(model=model, messages=messages, tools=tools, stream=False)
        history = messages[1:]
        history.append({"role": "assistant", "content": response.content})
        return response.content, history

    async def stream_process_query(self, model: str, query: str, history: list[dict] = None):
        '''
        流式处理用户的问题
        '''
        messages = []
        if history is not None:
            messages = messages + [message for message in history]
        messages.append({"role": "user", "content": query})
        tools, tool_name2server_name = await self.list_all_tools()

        while True:
            resp = await self.chat(model, messages, tools, stream=True)
            async for chunk in resp:
                logger.info(f"stream_process_query chunk: {chunk}")
                if chunk.tool_calls:
                    # 处理工具调用
                    tool_call_resp = []
                    for tool_call in chunk.tool_calls:
                        tool_response = await self.__call_tool(tool_name2server_name, tool_call.name, tool_call.arguments, tool_call.id)
                        messages.append(self.__llm_adapter.tool_call_process(chunk, tool_call))
                        messages.append(tool_response)
                        call = tool_call.model_dump()
                        call['response'] = tool_response['content']
                        tool_call_resp.append(call)
                    yield {"type": "tool_calls", "content": tool_call_resp}
                    break
                else:
                    yield {"type": "text", "content": chunk.content}
            else:
                # 没有 tool_calls，正常结束
                break

    async def __call_tool(self, tool_name2server_name: dict, name: str, args: dict, call_id: str) -> dict:
        tool: Client = self.__clients[tool_name2server_name[name]]
        tool_response: CallToolResult = await tool.call(args=args, tool_name=name)
        logger.info(f"Tool {name} called with args: {args} and response: {tool_response}")
        response_content = "\n".join([content.text for content in tool_response.content])
        return {"role": "tool", "content": response_content, "tool_call_id": call_id}
    
    async def call_tool(self, name: str, args: dict, call_id: str, server_name: str) -> dict:
        tool: Client = self.__clients[server_name]
        tool_response: CallToolResult = await tool.call(args=args, tool_name=name)
        logger.info(f"Tool {name} called with args: {args} and response: {tool_response}")
        response_content = "\n".join([content.text for content in tool_response.content])
        return {"role": "tool", "content": response_content, "tool_call_id": call_id}

    @overload
    async def chat(self, model: str, messages: list[dict], tools: list[Tool], stream: Literal[True] = True) -> AsyncGenerator[ChatResponse, None]:
        ...

    @overload
    async def chat(self, model: str, messages: list[dict], tools: list[Tool], stream: Literal[False] | None = False) -> ChatResponse:
        ...

    async def chat(self, model: str, messages: list[dict], tools: list[Tool], stream: bool | None = False) -> ChatResponse | AsyncGenerator[ChatResponse, None]:
        logger.info(f"messages: {messages}")
        logger.info(f"call LLM with messages:\n\t\t{"\n\t\t".join([f'{x["role"]}: {x["content"]} {x["tool_calls"] if "tool_calls" in x else ""}' for x in messages])}")
        logger.info(f"is stream: {stream}")
        if stream:
            return self.__chat_stream(model, messages, tools)
        else:
            return await self.__chat_none_stream(model, messages, tools)

    async def __chat_stream(self, model: str, messages: list[dict], tools: list[Tool]) -> AsyncGenerator[ChatResponse, None]:
        resp = await self.__llm_adapter.chat(model=model, messages=messages, tools=tools, stream=True)
        async for chunk in resp:
            logger.info(f"chunk: {chunk}")
            yield chunk

    async def __chat_none_stream(self, model: str, messages: list[dict], tools: list[Tool]) -> ChatResponse:
        response: ChatResponse = await self.__llm_adapter.chat(model=model, messages=messages, tools=tools, stream=False)
        return response

    async def list_all_tools(self) -> tuple[list[dict], dict]:
        tools = []
        for client in self.__clients.values():
            tools.extend(await client.list_tools())
        tool_name2server_name = {tool.function.name: tool.server_name for tool in tools}
        if len(tool_name2server_name) == 0:
            return None, None
        return tools, tool_name2server_name

    async def list_tools(self, name: str) -> ListToolsResult:
        return await self.__clients[name].list_tools_raw()
    
    async def get_client_session(self, name: str) -> ClientSession:
        return self.__clients[name].session
    
    async def get_server_details(self, name: str) -> dict:
        if name not in self.__clients:
            return {
                "status": "error",
                "message": "Server not found"
            }
        try:
            tools = await self.list_tools(name)
            return {
                "status": "success",
                "message": "Server details",
                "details": {
                    "tools": [{
                        "name": tool.name,
                        "description": tool.description
                    } for tool in tools.tools]
                }
            }
        except Exception as e:
            return {
                "status": "error",
                "message": str(e)
            }

    def get_llm_adapter(self) -> OpenAIAdapter:
        return self.__llm_adapter

client : MCPClient = MCPClient()

def get_mcp_client() -> MCPClient:
    global client
    if client is None:
        raise ValueError("MCPClient not initialized")
    return client

async def init_mcp_client(config: MCPClientConfig):
    global client
    await client.init(config)
