import requests
import re
from bs4 import BeautifulSoup
from llm import OllamaClient
from utils.selenium import WebDriverManager
from concurrent.futures import ThreadPoolExecutor

class SearchResultItem:
    def __init__(self, title: str, preview: str, url: str):
        self.title = title
        self.preview = preview
        self.url = url

class BaseSearchEngine():
    def __init__(self, ollama_client: OllamaClient):
        self.ollama_client = ollama_client

    def find_top_bese_match_article(self, text: str, result_list: list) -> str:
        format_result_list_2_text = ""
        for idx, result in enumerate(result_list):
            format_result_list_2_text += f"{idx + 1}: 标题：{result.title}; 内容：{result.preview};\n"
        prompt = f"""接下来给出的是一段话是由搜索引擎返回的搜索结果，请根据搜索结果，返回最符合用户搜索意图的搜索结果的前5条记录，你无需给出搜索结果的内容，仅需要返回满足条件的搜索结果序号即可。
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
        以下是你需要根据用户提供的搜索意图，返回最符合用户搜索意图的搜索结果的前5条记录，你无需给出搜索结果的内容，仅需要返回满足条件的搜索结果序号，使用英文逗号分隔，前后不要有空格。回答的前后不要有任何内容。
        搜索结果：
        {format_result_list_2_text}
        用户搜索意图：{text}
        """
        req = {
            "model": "deepseek-r1:14b",
            "prompt": prompt,   
            "stream": False
        }
        return self.ollama_client.generate(req)

    def before_search(self, text: str) -> str:
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
            "model": "deepseek-r1:14b",
            "prompt": prompt,   
            "stream": False
        }
        return self.ollama_client.generate(req)
    
    def read_search_result_detail(self, search_result: list[SearchResultItem], selected_result_idx: list[int]) -> str:
        # 多个搜索选中的结果，并发请求获取详情
        with ThreadPoolExecutor(max_workers=len(selected_result_idx)) as executor:
            futures = [executor.submit(self.get_search_result_detail, search_result[idx]) for idx in selected_result_idx]
            return [future.result() for future in futures]

    def get_search_result_detail(self, search_result: SearchResultItem) -> str:
        with WebDriverManager() as driver:
            content = driver.get_page_content(search_result.url)
            soup = BeautifulSoup(content, 'html.parser')
            return soup.text
        
    # 一个抽象的搜索方法，需要子类实现
    def search(self, query: str) -> list[SearchResultItem]:
        pass

    def searh_workflow(self, text: str) -> SearchResultItem:
        query = self.before_search(text)
        print("提取的查询语句：", query)
        result_list = self.search(query)
        print("搜索结果：", result_list)
        top_result =  self.find_top_bese_match_article(text, result_list)
        print("最符合用户搜索意图的搜索结果：", top_result)
        selected_result_idx = [int(idx) for idx in top_result.split(',')]
        selected_result_detail = self.read_search_result_detail(result_list, selected_result_idx)
        print("选中的搜索结果详情：", selected_result_detail)
        return selected_result_detail

class DuckDuckGoSearchEngine(BaseSearchEngine):
    def __init__(self, ollama_client: OllamaClient):
        super().__init__(ollama_client)
        self.engine_name = 'DuckDuckGO'
        self.url = "https://duckduckgo.com/?t=h_&ia=web&q="

    def search(self, query: str) -> list[SearchResultItem]:
        with WebDriverManager() as driver:
            if driver:
                driver.get(self.url + query)
                content = driver.page_source
                soup = BeautifulSoup(content, 'html.parser')
                # 提取网页内容中的标题和描述
                result_list = soup.find('li')
                formatted_result = []
                for result in result_list:
                # 提取标题和预览文本
                    title_html = result.find('h2')
                    title = title_html.text
                    preview = result.find('span').text
                    url = title_html.find('a')['href']
                    formatted_result.append(SearchResultItem(title, preview, url))
        return formatted_result


class BingSearchEngine(BaseSearchEngine):
    def __init__(self, ollama_client: OllamaClient):
        super().__init__(ollama_client)
        self.engine_name = 'Bing'
        self.url = "https://www.bing.com/search?q="

    def search(self, query: str) -> str:
        with WebDriverManager() as driver:
            content = driver.get_page_content(self.url + query)
            soup = BeautifulSoup(content, 'html.parser')
            # 获取 <li class="b_algo">
            li_list = soup.find_all('li', class_='b_algo')
            result_list = []
            for li in li_list:
                title = li.find('h2')
                url = title.find('a')['href']
                title_text = title.text
                preview = li.find('div', class_='b_caption')
                preview_text = preview.text
                result_list.append(SearchResultItem(title_text, preview_text, url))
            return result_list


