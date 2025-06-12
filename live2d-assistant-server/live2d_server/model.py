from pydantic import BaseModel
from typing import Literal, Any

class ToolFunction(BaseModel):
    name: str
    description: str
    parameters: dict

class Tool(BaseModel):
    type: Literal["function"]
    function: ToolFunction
    server_name: str
    instance: Any | None = None
