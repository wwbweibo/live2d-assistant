"""定义一些Agent的模型."""

from typing import TypedDict, Annotated, Literal, Optional, Any
from pydantic import BaseModel
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages

class MessagesState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    waiting_for_input: bool  # 添加中断状态标志
    thread_id: str  # 添加线程ID用于中断恢复

class Assistant(BaseModel):
    name: str
    description: str
    tools: list[Any]
    prompt: str

class ToolResouce(BaseModel):
    """定义一个工具资源
    
    用于指定将从何处初始化工具
    """
    source: Literal["mcp", "local_file", "python", "prebuild"] # 工具源, mcp: 从指定的MCP服务器获取工具, local_file: 从本地的文件获取工具, python: 给定一段代码并加载工具, prebuild: 从预定义的工具中获取工具
    mcp_server: Optional[str] = None # MCP 服务器的名称，该服务器应该被首先定义
    local_file_path: Optional[str] = None # 本地工具路径，该路径应该是一个Python文件，该文件应该包含一个或多个可被导出的函数
    python_code: Optional[str] = None # 给定一段代码并加载工具
    prebuild_name: Optional[str] = None # 预定义的工具名称，该名称应该被定义在prebuild.py中

class AgentConfig(BaseModel):
    """定义一个Agent配置

    程序将使用该配置动态生成一个Agent，并最终集成到MultiAgent中
    """
    name: str # 助手名称
    description: str # 助手描述
    tools: list[ToolResouce] # 助手工具
    prompt: str # 助手提示词
    hands_off: list[str] # 助手可以跳转的节点，如果为空，则助手将无法转交控制权