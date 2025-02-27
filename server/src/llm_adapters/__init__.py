from .ollama_adapter import OllamaAdapter
from .openai_adapter import OpenAIAdapter
from .llm_adapter import LLMAdapter
from logging import Logger

def new_llm_adapter(provider: str, config: dict, logger: Logger) -> LLMAdapter:
    if provider == "ollama":
        return OllamaAdapter(config["ollamaHost"], logger)
    elif provider == "openai":
        return OpenAIAdapter(config["provider"], config["apiKey"], config["baseURL"], logger)
