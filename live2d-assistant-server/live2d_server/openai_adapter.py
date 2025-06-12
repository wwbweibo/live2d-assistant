from openai import AsyncOpenAI
from typing import Any, AsyncGenerator, Literal, overload
from live2d_server.chat_response import ChatResponse, ToolCall
import json
# from typing_extensions import overload
import logging
from live2d_server.model import Tool

logger = logging.getLogger(__name__)

class OpenAIAdapter():
    def __init__(self, provider:str, api_key: str, base_url: str):
        self.provider = provider
        self.api_key = api_key
        self.base_url = base_url
        self.openai_client = AsyncOpenAI(api_key=api_key, base_url=base_url)

    @overload
    async def chat(self, model: str, messages: list[dict], tools: list[Tool], stream: Literal[True] = True) -> AsyncGenerator[ChatResponse, None]:
        ...

    @overload
    async def chat(self, model: str, messages: list[dict], tools: list[Tool], stream: Literal[False] | None = False) -> ChatResponse:
        ...

    async def chat(self, model: str, messages: list[dict], tools: list[Tool], stream: bool | None = False) -> ChatResponse | AsyncGenerator[ChatResponse, None]:
        if stream:
            return self._chat_stream(model, messages, tools)
        else:
            return await self._chat_none_stream(model, messages, tools)

    
    async def _chat_none_stream(self, model: str, messages: list[dict], tools: list[Tool]) -> ChatResponse:
        response = await self.openai_client.chat.completions.create(model=model, messages=messages, tools=self.tool_to_openai_tool(tools))
        return ChatResponse(
            model=response.model,
            role=response.choices[0].message.role,
            content=response.choices[0].message.content,
        )
    

    async def _chat_stream(self, model: str, messages: list[dict], tools: list[Tool]) -> AsyncGenerator[ChatResponse, None]:
        resp = await self.openai_client.chat.completions.create(model=model, messages=messages, tools=self.tool_to_openai_tool(tools), stream=True)
        tool_calls = {}
        async for chunk in resp:
            if len(chunk.choices) > 0:
                if chunk.choices[0].delta.tool_calls is not None:
                    # 如果有工具调用，在这里等待工具调用完了之后再返回
                    for tool_call in chunk.choices[0].delta.tool_calls:
                        id = tool_call.id
                        index = tool_call.index
                        name = tool_call.function.name
                        arguments = tool_call.function.arguments
                        previous_tool_call = tool_calls.get(index)
                        if previous_tool_call is None:
                            tool_calls[index] = ToolCall(id=id, name=name, arguments=arguments)
                        else:
                            tool_calls[index].arguments +=  arguments if arguments is not None else ''
                            tool_calls[index].name += name if name is not None else ''
                            tool_calls[index].id += id if id is not None else ''
                if chunk.choices[0].delta.content is not None:
                    # 如果content不为空，则返回
                    yield ChatResponse(
                        model=chunk.model,
                        role=chunk.choices[0].delta.role if chunk.choices[0].delta.role is not None else 'assistant',
                        content=chunk.choices[0].delta.content if chunk.choices[0].delta.content is not None else ''
                    )
                if len(tool_calls) > 0 and chunk.choices[0].delta.tool_calls is None:
                    # 如果工具调用完了，则返回
                    yield ChatResponse(
                        model=chunk.model,
                        role=chunk.choices[0].delta.role if chunk.choices[0].delta.role is not None else 'assistant',
                        content=chunk.choices[0].delta.content if chunk.choices[0].delta.content is not None else '',
                        tool_calls=list(tool_calls.values())
                    )

    async def generate(self, model: str, prompt: str, format: dict = None) -> str:
        response = await self.openai_client.chat.completions.create(model=model, messages=[{"role": "user", "content": prompt}], response_format=format)
        logger.info(f"OpenAI response: {response}")
        return response.choices[0].message.content
    
    def tool_call_process(self, response: ChatResponse, tool_call: ToolCall) -> dict:
        return {'role': response.role, 'content': response.content, 'function_call': None, 'tool_calls': [{'id': tool_call.id, 'function': {'arguments': json.dumps(tool_call.arguments), 'name': tool_call.name}, 'type': 'function'}]}
    
    def tool_to_openai_tool(self, tools: list[Tool]) -> list[dict]:
        if tools is None or len(tools) == 0:
            return None
        return [
            {
                "type": "function",
                "function": {
                    "name": tool.function.name,
                    "description": tool.function.description,
                    "parameters": tool.function.parameters,
                },
            }
            for tool in tools
        ]