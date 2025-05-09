from openai import AsyncOpenAI
from typing import Any, AsyncGenerator, Literal, overload
from chat_response import ChatResponse, ToolCall
import json
# from typing_extensions import overload
import logging

logger = logging.getLogger(__name__)

class OpenAIAdapter():
    def __init__(self, provider:str, api_key: str, base_url: str):
        self.openai_client = AsyncOpenAI(api_key=api_key, base_url=base_url)

    @overload
    async def chat(self, model: str, messages: list[dict], tools: list[dict], stream: Literal[True] = True) -> AsyncGenerator[ChatResponse, None]:
        ...

    @overload
    async def chat(self, model: str, messages: list[dict], tools: list[dict], stream: Literal[False] | None = False) -> ChatResponse:
        ...

    async def chat(self, model: str, messages: list[dict], tools: list[dict], stream: bool | None = False) -> ChatResponse | AsyncGenerator[ChatResponse, None]:
        if stream:
            return self._chat_stream(model, messages, tools)
        else:
            return await self._chat_none_stream(model, messages, tools)

    
    async def _chat_none_stream(self, model: str, messages: list[dict], tools: list[dict]) -> ChatResponse:
        response = await self.openai_client.chat.completions.create(model=model, messages=messages, tools=tools)
        return ChatResponse(
            model=response.model,
            role=response.choices[0].message.role,
            content=response.choices[0].message.content,
        )
    

    async def _chat_stream(self, model: str, messages: list[dict], tools: list[dict]) -> AsyncGenerator[ChatResponse, None]:
        resp = await self.openai_client.chat.completions.create(model=model, messages=messages, tools=tools, stream=True)
        async for chunk in resp:
            if len(chunk.choices) > 0:
                yield ChatResponse(
                    model=chunk.model,
                    role=chunk.choices[0].delta.role,
                    content=chunk.choices[0].delta.content,
                    tool_calls=[
                        ToolCall(
                            id=tool_call.id, 
                            name=tool_call.function.name, 
                            arguments=tool_call.function.arguments
                        ) 
                        for tool_call in chunk.choices[0].delta.tool_calls
                    ] if chunk.choices[0].delta.tool_calls else None
                )
            # else:
            #     yield ChatResponse(
            #         model=chunk.model,
            #         role=chunk.choices[0].message.role,
            #         content=chunk.choices[0].message.content,
            #         tool_calls=chunk.choices[0].message.tool_calls,
            #     )


    async def generate(self, model: str, prompt: str, format: dict = None) -> Any:
        response = await self.openai_client.chat.completions.create(model=model, messages=[{"role": "user", "content": prompt}], response_format=format)
        logger.info(f"OpenAI response: {response}")
        return response.choices[0].message.content
    
    def tool_call_process(self, response: ChatResponse, tool_call: ToolCall) -> dict:
        return {'role': response.role, 'content': response.content, 'function_call': None, 'tool_calls': [{'id': tool_call.id, 'function': {'arguments': json.dumps(tool_call.arguments), 'name': tool_call.name}, 'type': 'function'}]}