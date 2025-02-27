from ollama import AsyncClient, GenerateResponse
from logging import Logger
from typing import Any
from .llm_adapter import LLMAdapter
from .chat_response import ChatResponse, ToolCall
from ollama import ChatResponse as OllamaChatResponse
import uuid

class OllamaAdapter(LLMAdapter):
    def __init__(self, host: str, logger: Logger):
        super().__init__("ollama", logger)
        self.ollama_host = host
        self.client = AsyncClient(self.ollama_host)

    async def chat(self, model: str, messages: list[dict], tools: list[dict]) -> ChatResponse:
        response: OllamaChatResponse = await self.client.chat(model=model, messages=messages, tools=tools)
        self.logger.info(f"Ollama response: {response}")
        return ChatResponse(
            model=response.model,
            role='assistant',
            content=response.message.content,
            tool_calls=[ToolCall(str(uuid.uuid4()), tool_call.function.name, tool_call.function.arguments) for tool_call in response.message.tool_calls] if response.message.tool_calls else []
        )
    
    async def generate(self, model: str, message: str, format: dict = None) -> Any:
        response: GenerateResponse = await self.client.generate(model=model, prompt=message, format=format)
        self.logger.info(f"Ollama response: {response}")
        return response.response

    def tool_call_process(self, response: ChatResponse, tool_call: ToolCall) -> dict:
        return {'role': response.role, 'content': response.content, 'function_call': None, 'tool_calls': [{'id': tool_call.id, 'function': {'arguments': tool_call.arguments, 'name': tool_call.name}, 'type': 'function'}]}