import asyncio
import threading
from typing import Any

from langchain_core.tools import BaseTool, StructuredTool
from langchain_mcp_adapters.tools import NonTextContent, _convert_call_tool_result
from mcp import ClientSession

from mcp.types import (
    Tool as MCPTool
)

_loop = asyncio.new_event_loop()

_thr = threading.Thread(target=_loop.run_forever, name="Async Runner",
                        daemon=True)

# This will block the calling thread until the coroutine is finished.
# Any exception that occurs in the coroutine is raised in the caller
def run_async(coro):  # coro is a couroutine, see example
    """
    Ref: https://stackoverflow.com/a/74710015
    """
    if not _thr.is_alive():
        _thr.start()
    future = asyncio.run_coroutine_threadsafe(coro, _loop)
    return future.result()

def new_convert_mcp_tool_to_langchain_tool(
    session: ClientSession,
    tool: MCPTool,
) -> BaseTool:
    """Convert an MCP tool to a LangChain tool.

    NOTE: this tool can be executed only in a context of an active MCP client session.

    Args:
        session: MCP client session
        tool: MCP tool to convert

    Returns:
        a LangChain tool
    """

    async def acall_tool(
        **arguments: dict[str, Any],
    ) -> tuple[str | list[str], list[NonTextContent] | None]:
        print(f"调用工具 {tool.name} 参数 {arguments}")
        call_tool_result = await session.call_tool(tool.name, arguments)
        print(f"工具 {tool.name} 返回结果 {call_tool_result}")
        return _convert_call_tool_result(call_tool_result)

    def call_tool(
        **arguments: dict[str, Any],
    ) -> tuple[str | list[str], list[NonTextContent] | None]:
        return run_async(acall_tool(**arguments))

    return StructuredTool(
        name=tool.name,
        description=tool.description or "",
        args_schema=tool.inputSchema,
        func=call_tool,  #
        # coroutine=acall_tool,
        response_format="content_and_artifact",
    )
