from typing import Any
from logging import Logger
from .chat_response import ToolCall, ChatResponse

class LLMAdapter:
    def __init__(self, provider: str, logger: Logger):
        self.provider = provider
        self.logger = logger
    async def chat(self, model: str, messages: list[dict], tools: list[dict]) -> Any:
        pass

    async def generate(self, model: str, prompt:str, format: dict = None) -> Any:
        pass

    def model_available(self, model: str) -> bool:
        return model in provider_model_map[self.provider]

    def tool_call_process(self, response: ChatResponse, tool_call: ToolCall) -> dict:
        '''
        对于包含工具调用的模型响应，使用该函数转化成需要再次提交给模型对话的消息格式
        '''
        pass

provider_model_map = {
    "deepseek": [
        'deepseek-chat',
        'deepseek-reasoner'
    ]
}