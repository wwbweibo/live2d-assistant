from langchain_core.tools import tool
from datetime import datetime
from langchain_community.utilities.searx_search import SearxSearchWrapper

s = SearxSearchWrapper(searx_host="http://localhost:8080")

@tool
def get_current_time(state: dict) -> str:
    """获取当前时间"""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


tools = [get_current_time, s]