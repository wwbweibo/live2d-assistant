from langchain_community.utilities.searx_search import SearxSearchWrapper

searx_search_wrapper = SearxSearchWrapper(searx_host="http://localhost:8080", k=5)

def search(query: str) -> str:
    return searx_search_wrapper.run(query, engines=["bing", "duckduckgo", "baidu"])