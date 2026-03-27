"""
SearxNG 网络搜索工具。

通过 SearxNG 实例执行网络搜索，返回格式化的搜索结果。
环境变量:
    SEARXNG_URL: SearxNG 实例地址，默认 http://localhost:8888
"""

import os

import httpx

from agentic_agents.tools import tool


SEARXNG_URL = os.getenv("SEARXNG_URL", "http://localhost:8888")


@tool()
async def searx_search(query: str, max_results: int = 5) -> str:
    """使用 SearxNG 搜索引擎搜索网络信息。

    Args:
        query: 搜索关键词
        max_results: 最大返回结果数，默认 5
    """
    params = {
        "q": query,
        "format": "json",
        "language": "auto",
    }

    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.get(f"{SEARXNG_URL}/search", params=params)
        resp.raise_for_status()
        data = resp.json()

    results = data.get("results", [])[:max_results]

    if not results:
        return f"未找到与 '{query}' 相关的搜索结果。"

    formatted = []
    for i, r in enumerate(results, 1):
        title = r.get("title", "无标题")
        url = r.get("url", "")
        content = r.get("content", "无摘要")
        formatted.append(f"[{i}] {title}\n    URL: {url}\n    摘要: {content}")

    return f"搜索 '{query}' 的结果:\n\n" + "\n\n".join(formatted)
