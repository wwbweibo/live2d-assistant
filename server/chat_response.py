from typing import List, Optional

from pydantic import BaseModel

class ToolCall(BaseModel):
    id: str
    name: str 
    arguments: str

class ChatResponse(BaseModel):
    model: str
    role: str
    content: str
    tool_calls: Optional[List[ToolCall]] = None

