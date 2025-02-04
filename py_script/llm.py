import requests
import re

class OllamaClient:
    def __init__(self, base_url:str):
        self.base_url = base_url

    def chat(self, req_data: dict) -> str:
        req = requests.post(self.base_url + '/api/chat', json=req_data)
        message = req.json()['message']['content']
        return self.__common_preprocess(message)

    def generate(self, req_data: dict) -> str:
        req = requests.post(self.base_url + '/api/generate', json=req_data)
        return self.__common_preprocess(req.json()['response'])

    def __common_preprocess(self, message: str) -> str:
        # 移除 <think> 和 </think>之间的内容
        message = re.sub(r'<think>.*(\n.*)*</think>\n*', '', message)
        return message

