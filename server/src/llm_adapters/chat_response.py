class ToolCall:
    def __init__(self, id: str, name: str, arguments: dict):
        self.id: str = id
        self.name: str = name
        self.arguments: dict = arguments

    def __str__(self):
        return f"ToolCall(id={self.id}, name={self.name}, arguments={self.arguments})"

class ChatResponse:
    def __init__(self, model: str, role: str, content: str, tool_calls: list[ToolCall]):
        self.model = model
        self.role = role
        self.content = content
        self.tools_calls = tool_calls

    def __str__(self):
        return f"OpenAIChatResponse(model={self.model}, role={self.role}, content={self.content}, tools_calls={', '.join([str(tool_call) for tool_call in self.tools_calls])})"
