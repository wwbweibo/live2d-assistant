"""提供一些预定义的Agent."""

import logging
from langchain.tools.searx_search.tool import SearxSearchResults
from live2d_server.search.searx import searx_search_wrapper

logger = logging.getLogger(__name__)

# 预定义的工具集，可以直接使用
searx_tool = SearxSearchResults(name="searx", description="使用searx搜索网络", wrapper=searx_search_wrapper)


prebuild_tools = {
    "searx": searx_tool
}