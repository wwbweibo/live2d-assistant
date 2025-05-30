from .search_engine import BaseSearchEngine, SearchResultItem
from openai_adapter import OpenAIAdapter as LLMAdapter
from utils.selenium import WebDriverManager
from bs4 import BeautifulSoup

class DuckDuckGoSearchEngine(BaseSearchEngine):
    def __init__(self, llm_adapter: LLMAdapter, model: str):
        super().__init__(llm_adapter, model)
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

