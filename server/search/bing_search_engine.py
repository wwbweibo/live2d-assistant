from .search_engine import BaseSearchEngine, SearchResultItem
from openai_adapter import OpenAIAdapter as LLMAdapter
from utils.selenium import WebDriverManager
from bs4 import BeautifulSoup

class BingSearchEngine(BaseSearchEngine):
    def __init__(self, llm_adapter: LLMAdapter, model: str):
        super().__init__(llm_adapter, model)
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


