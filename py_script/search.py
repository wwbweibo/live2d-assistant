import requests
import re
from bs4 import BeautifulSoup
from llm import OllamaClient

class DuckDuckGoSearchEngine():
    def __init__(self, ollama_client: OllamaClient):
        self.engine_name = 'DuckDuckGO'
        self.ollama_client = ollama_client
        self.url = "https://duckduckgo.com/?t=h_&ia=web&q="

    def search(self, query: str) -> str:
        req = requests.get(self.url + query, headers={
            "user-agent": "Moz/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36 Edg/132.0.0.0",
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "accept-language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
            "cache-control": "no-cache",
            "pragma": "no-cache",
            "priority": "u=0, i",
            "referer": "https://duckduckgo.com/",
            "sec-ch-ua": '"Not A(Brand";v="8", "Chromium";v="132", "Microsoft Edge";v="132"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": "Windows",
            "sec-fetch-dest": "document",
            "sec-fetch-mode": "navigate",
            "sec-fetch-site": "same-origin",
            "sec-fetch-user": "?1",
            "upgrade-insecure-requests": "1",
            "priority": "u=0, i"
        })
        # 提取相应内容，获取到返回的网页内容
        content = req.text
        # 使用BeautifulSoup解析网页内容
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
            formatted_result.append(f"{title}\n{preview}\n{url}")
        return formatted_result

    def find_top_bese_match_article(self, text: str, result_list: list) -> str:
        format_result_list_2_text = ""
        for idx, result in enumerate(result_list):
            format_result_list_2_text += f"{idx + 1}: 标题：{result['title']}; 内容：{result['content']};\n"
        prompt = f"""接下来给出的是一段话是由搜索引擎返回的搜索结果，请根据搜索结果，返回最符合用户搜索意图的搜索结果的前5条记录，你无需给出搜索结果的内容，仅需要返回满足条件的搜索结果序号即可。
        搜索结果：{format_result_list_2_text}
        用户搜索意图：{text}
        最符合用户搜索意图的搜索结果：
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