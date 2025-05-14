from typing import TypedDict, Annotated, Literal
from langgraph.graph import add_messages, StateGraph, START, END
from langgraph.types import Command
from langchain_core.messages import BaseMessage
from langchain_openai import ChatOpenAI
from pydantic import BaseModel
from typing import Any
from langchain_core.runnables import RunnableLambda
from langgraph.prebuilt import create_react_agent

class MessagesState(TypedDict):
    messages: Annotated[list, add_messages]

class Assistant(BaseModel):
    name: str
    description: str
    tools: list[Any]
    prompt: str


class Agent:
    def __init__(self,
                 llm: ChatOpenAI,
                 assistant_map: dict[str, Assistant],
                 start_node: str):
        self.llm = llm
        self.assistant_map = assistant_map
        self.start_node = start_node


    def make_system_prompt(self, name: str, suffix: str) -> str:
        assistant_map = self.assistant_map  
        return (f"""你是一个AI助手，你的名字是{name}，你的职责是{assistant_map[name].description}。
你正在与其他的AI助手合作完成任务。
下面是其他AI助手的描述：
{"\n".join([f"{assistant.name}: {assistant.description}" for assistant in assistant_map.values() if assistant.name != name])}
你的可以使用提供给你的工具来处理任务。
如果任务需要多个工具，你可以使用多个工具来完成任务。
如果你无法完成任务，那也没关系，其他AI助手可以继续完成任务。
如果你们中有人得到了最终答案或交付物，请在回答中添加END，这样团队就知道任务完成了。
{suffix}
---
你的处理逻辑应该遵循如下规则：
1. 请使用 思考-执行-观察 的循环来处理任务、
    1. 思考：思考当前任务需要做什么，以及如何完成任务
    2. 执行：你需要决定是否需要使用工具来完成任务
    3. 观察：根据可能的反馈，调整你的思考和执行
2. 你仅应该关注当前步骤你应该做什么，不要考虑后续步骤
3. 如果当前步骤你无法完成，请将控制权移交给你认为可以完成当前任务的助手
4. 如果你认为已经完成任务，请以 END 的格式返回
---
你的返回应该遵循如下格式，
1. 如果是需要你进行处理的，直接返回消息
2. 如果需要分配给其他助手，请以 GOTO: assistant_name 的格式返回
3. 如果不需要分配给其他助手，请以 END 的格式返回
    """)

    @staticmethod
    def get_next_node(message: BaseMessage, current_node: str) -> Literal["research", "music_player", "decision_maker", END]:
        print(f"当前节点 {current_node} 返回结果 {message.content}")
        if "GOTO:" in message.content:
            return message.content.split("GOTO:")[1].strip()
        elif "END" in message.content:
            return END
        else:
            return current_node


    def create_node(self, name: str) -> RunnableLambda:
        assistant = self.assistant_map[name]
        agent = create_react_agent(
            self.llm,
            tools=assistant.tools,
            prompt=self.make_system_prompt(name, assistant.prompt),
        )
        async def node(
                state: MessagesState,
        ) -> Command[Literal["research", "music_player", "decision_maker", END]]:
            result = await agent.ainvoke(state)
            print(f"节点 {name} 返回结果 {result}")
            return_message: BaseMessage = result["messages"][-1]
            print(f"节点 {name} 返回消息 {return_message.content}")
            if return_message.additional_kwargs.get('tool_calls'):
                print(f"节点 {name} 使用工具 {return_message.additional_kwargs['tool_calls'][0]['function']['name']}")
            goto = self.get_next_node(return_message, name)
            print(f"节点 {name} 跳转至 {goto}")
            return Command(
                update={
                    "messages": result["messages"],
                },
                goto=goto,
            )
        print(f"创建节点 {name}")
        return node


    def create_workflow(self) -> StateGraph:
        workflow = StateGraph(MessagesState)
        for k, v in self.assistant_map.items():
            node = self.create_node(k)
            workflow.add_node(k, node)

        workflow.add_edge(START, self.start_node)
        graph = workflow.compile()
        return graph


