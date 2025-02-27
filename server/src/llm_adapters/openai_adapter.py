from openai import AsyncOpenAI
import os
from typing import Any
from .llm_adapter import LLMAdapter, provider_model_map
from .chat_response import ChatResponse, ToolCall
import json
from logging import Logger

class OpenAIAdapter(LLMAdapter):
    def __init__(self, provider:str, api_key: str, base_url: str, logger: Logger):
        self.openai_client = AsyncOpenAI(api_key=api_key, base_url=base_url)
        super().__init__(provider, logger)

    async def chat(self, model: str, messages: list[dict], tools: list[dict]) -> Any:
        if not self.model_available(model):
            raise ValueError(f"Model {model} for provider {self.provider} is not available, please use model in {provider_model_map[self.provider]}")
        response = await self.openai_client.chat.completions.create(model=model, messages=messages, tools=tools)
        self.logger.info(f"OpenAI response: {response}")
        return ChatResponse(
            model=response.model,
            role=response.choices[0].message.role,
            content=response.choices[0].message.content,
            tool_calls=[ToolCall(tool_call.id, tool_call.function.name, json.loads(tool_call.function.arguments)) for tool_call in response.choices[0].message.tool_calls] if response.choices[0].message.tool_calls else []
        )
    
    async def generate(self, model: str, prompt: str, format: dict = None) -> Any:
        response = await self.openai_client.chat.completions.create(model=model, messages=[{"role": "user", "content": prompt}], response_format=format)
        self.logger.info(f"OpenAI response: {response}")
        return response.choices[0].message.content
    
    def tool_call_process(self, response: ChatResponse, tool_call: ToolCall) -> dict:
        return {'role': response.role, 'content': response.content, 'function_call': None, 'tool_calls': [{'id': tool_call.id, 'function': {'arguments': json.dumps(tool_call.arguments), 'name': tool_call.name}, 'type': 'function'}]}