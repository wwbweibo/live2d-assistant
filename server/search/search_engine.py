import requests
import re
from bs4 import BeautifulSoup
from openai_adapter import OpenAIAdapter as LLMAdapter
from utils.selenium import WebDriverManager
from concurrent.futures import ThreadPoolExecutor
import json

class SearchResultItem:
    def __init__(self, title: str, preview: str, url: str):
        self.title = title
        self.preview = preview
        self.url = url

class BaseSearchEngine():
    def __init__(self, llm_adapter: LLMAdapter, model: str):
        self.llm_adapter = llm_adapter
        self.model = model

    async def find_top_best_match_article(self, text: str, result_list: list) -> str:
        format_result_list_2_text = ""
        for idx, result in enumerate(result_list):
            format_result_list_2_text += f"{idx + 1}: 标题：{result.title}; 内容：{result.preview};\n"
        prompt = f"""接下来给出的是一段话是由搜索引擎返回的搜索结果，请根据搜索结果，返回最符合用户搜索意图的搜索结果的前5条记录，你无需给出搜索结果的内容，仅需要返回满足条件的搜索结果序号即可,将其放入result数组中。
        ---
        以下是你应该遵循的示例：
        搜索结果：
        1: 标题：Python 单元测试; 内容：Python 单元测试是 Python 编程中的一种测试方法，用于测试代码的各个模块是否能够正常工作。;
        2: 标题：Python 单元测试; 内容：Python 单元测试是 Python 编程中的一种测试方法，用于测试代码的各个模块是否能够正常工作。;
        3: 标题：Python 单元测试; 内容：Python 单元测试是 Python 编程中的一种测试方法，用于测试代码的各个模块是否能够正常工作。;
        4: 标题：Python 单元测试; 内容：Python 单元测试是 Python 编程中的一种测试方法，用于测试代码的各个模块是否能够正常工作。;
        5: 标题：Python 单元测试; 内容：Python 单元测试是 Python 编程中的一种测试方法，用于测试代码的各个模块是否能够正常工作。;
        用户的搜索意图：我想学习Python的单元测试，应该怎么学？
        期望的返回结果：1,3
        ---
        搜索结果：
        {format_result_list_2_text}
        用户搜索意图：{text}
        """
        req = {
            "model": self.model,
            "prompt": prompt,   
            "stream": False,
            "format":{
                "type": "object",
                "properties":{
                    "result":{
                        "type": "array",
                        "description": "选中的复合用户预期的搜索结果"
                    }
                },
                "required": ["result"]
            }
        }
        result = await self.llm_adapter.generate(self.model, prompt, req['format'])
        result = json.loads(result)
        return result['result']

    async def before_search(self, text: str) -> str:
        prompt = f"""接下来的这段话是由用户提供的一段文本，其中包含了用户需要搜索的内容，请根据用户提供的内容，返回一组搜索引擎使用的查询关键词。你的回答只需要包含搜索查询语句，不要包含任何其他内容。
        这里是可供参考的示例：
        ```
        用户提供的内容为：明天下午的天气怎么样
        返回的搜索查询语句为：明天下午 天气
        ```
        用户提供的内容：{text}
        搜索查询语句：
        """
        req = {
            "model": self.model,
            "prompt": prompt,   
            "stream": False
        }
        return await self.llm_adapter.generate(self.model, prompt)
    
    async def read_search_result_detail(self, search_result: list[SearchResultItem], selected_result_idx: list[int]) -> str:
        detail_list = []
        selected_result_idx = [int(idx) for idx in selected_result_idx]
        for idx in selected_result_idx:
            search_result_detail = await self.get_search_result_detail(search_result[idx - 1])
            detail_list.append(search_result_detail)
        return detail_list

    async def get_search_result_detail(self, search_result: SearchResultItem) -> str:
        with WebDriverManager() as driver:
            content = driver.get_page_content(search_result.url)
            soup = BeautifulSoup(content, 'html.parser')
            return soup.text
        
    # 一个抽象的搜索方法，需要子类实现
    async def search(self, query: str) -> list[SearchResultItem]:
        pass

    async def searh_workflow(self, text: str) -> list[str]:
        '''
        搜索工作流，根据用户提供的文本，返回最符合用户搜索意图的搜索结果的前5条记录，并返回选中的搜索结果详情
        '''
        query = await self.before_search(text)
        print("提取的查询语句：", query)
        result_list = self.search(query)
        print("搜索结果：", result_list)
        top_result =  await self.find_top_best_match_article(text, result_list)
        print("最符合用户搜索意图的搜索结果：", top_result)
        selected_result_detail = await self.read_search_result_detail(result_list, top_result)
        print("选中的搜索结果详情：", selected_result_detail)
        return selected_result_detail


