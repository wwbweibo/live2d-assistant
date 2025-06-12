"""加载工具"""

from langchain_core.tools import BaseTool
import os
import importlib.util

async def load_tools_from_local_file(file_path: str) -> list[BaseTool]:
    """从本地文件加载工具"""
    # check if the file is a python file
    if not file_path.endswith(".py"):
        raise ValueError("文件路径必须是一个Python文件")
    # check if the file exists
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"文件不存在: {file_path}")
    # load file using importlib
    spec = importlib.util.spec_from_file_location("tools", file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.tools

async def load_tools_from_python_code(code: str) -> list[BaseTool]:
    """从Python代码加载工具"""
    # 创建一个空的命名空间来执行代码
    namespace = {}
    
    try:
        # 执行代码字符串
        exec(code, namespace)
        
        # 检查是否存在tools变量
        if 'tools' not in namespace:
            raise ValueError("代码中没有找到tools变量")
        
        tools = namespace['tools']
        
        # 检查tools是否为列表类型
        if not isinstance(tools, list):
            raise ValueError("tools变量必须是一个列表")
        
        # 检查列表中的每个元素是否为BaseTool类型
        for tool in tools:
            if not isinstance(tool, BaseTool):
                raise ValueError(f"tools列表中包含非BaseTool类型的对象: {type(tool)}")
        
        return tools
        
    except Exception as e:
        raise RuntimeError(f"执行代码时发生错误: {str(e)}")