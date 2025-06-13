from fastapi import APIRouter, Request, Depends
from fastapi.responses import StreamingResponse
import os
import requests
import base64
import json
import asyncio
from typing import List, Optional, AsyncGenerator
from pydantic import BaseModel
from live2d_server.configuration import Config
from live2d_server.client import get_mcp_client, MCPClientConfig, init_mcp_client
import logging
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph
from langgraph.types import Command
from langchain_core.messages import ToolMessage
from live2d_server.agent.agent import Agent
from live2d_server.agent.model import AgentConfig
from live2d_server.search.searx import search
from datetime import datetime
from live2d_server.rag.rag import search_knowledge_base

logger = logging.getLogger(__name__)

router = APIRouter()

class ChatRequest(BaseModel):
    model: str
    chat_id: str
    messages: List[dict]
    is_resume: Optional[bool] = False
    web_search: Optional[bool] = False
    rag: Optional[bool] = False
    tts_enabled: Optional[bool] = False
    agents: Optional[List[AgentConfig]] = None

class ChatResponse(BaseModel):
    message: str
    wav_data: List[str]

class TTSRequest(BaseModel):
    text: str

# 全局变量
config = None
tts_server = None
llm_adapter = None
# 一个agent缓存，用于处理agent再入的问题
agents = {}

def set_config(_config: Config):
    global config
    logger.info(f"set_config: {_config}")
    config = _config

def get_config():
    global config
    logger.info(f"get_config: {config}")
    return config

def get_tts_server():
    return tts_server

def get_llm_adapter():
    return llm_adapter

def init_tts_if_needed(config: Config, tts_server=None):
    """初始化TTS服务"""
    if config.server.tts.enabled and tts_server is None:
        from tts import tts_init, TtsServer
        cosyvoice, prompt_speech_16k = tts_init(
            config.server.tts.cosyvoiceInstallPath,
            config.server.tts.modulePath,
            config.server.tts.promptPath,
            config.server.tts.sampleRate,
            config.server.tts.promptText
        )
        return TtsServer(cosyvoice, prompt_speech_16k, config.server.tts.promptText)
    return tts_server

async def stream_chat_response(
    request: ChatRequest,
    config: Config = Depends(get_config),
    llm_adapter = Depends(get_llm_adapter),
    tts_server = Depends(get_tts_server)
) -> AsyncGenerator[str, None]:
    """生成流式聊天响应"""
    try:
        if request.web_search:
            # 由大模型构建搜索词之后进行搜索
            # yield f"data: {json.dumps({'type': 'text', 'content': '正在搜索中，请稍等...'})}\n\n"
            search_query = await get_mcp_client().get_llm_adapter().generate(model=request.model, prompt=f"""
            你是一个搜索专家，请根据用户的历史对话内容和当前的问题构建搜索词并返回，你应该仅返回搜索词，不要返回任何其他内容。
            用户的问题是：{request.messages[-1]['content']}
            用户的对话历史是：{request.messages[1:]}
            当前时间是：{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
            """)
            logger.info(f"search query: {search_query}")
            search_result = search(search_query)
            # 替换掉最后一个消息的content
            request.messages[-1]['content'] = f"使用如下的信息回答用户的问题：{search_result}，用户的问题是：{request.messages[-1]['content']}"
        if request.rag:
            # 使用RAG进行查询            
            search_query = await get_mcp_client().get_llm_adapter().generate(model=request.model, prompt=f"""
            你是一个搜索专家，请根据用户的历史对话内容和当前的问题构建RAG搜索词并返回，你应该仅返回搜索词，不要返回任何其他内容。
            用户的问题是：{request.messages[-1]['content']}
            用户的对话历史是：{request.messages[1:]}
            当前时间是：{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
            """)
            logger.info(f"search query: {search_query}")
            search_result = await search_knowledge_base(search_query)
            logger.info(f"search result: {search_result}")
            request.messages[-1]['content'] = f"使用如下的信息回答用户的问题：{search_result}，用户的问题是：{request.messages[-1]['content']}"
        async for chunk in get_mcp_client().stream_process_query(request.model, request.messages[-1]['content'], request.messages[:-1]):
            logger.info(f"stream_chat_response: {chunk}")
            yield f"data: {json.dumps(chunk)}\n\n"
            await asyncio.sleep(0)  # 让出控制权给其他协程
        
        # 如果需要TTS，生成音频数据c
        if request.tts_enabled:
            tts_server = init_tts_if_needed(config, tts_server)
            wav_data = tts_server.tts(chunk)
            for data in wav_data:
                base64_wave = base64.b64encode(data).decode('utf-8')
                yield f"data: {json.dumps({'type': 'audio', 'content': base64_wave})}\n\n"
                await asyncio.sleep(0)
        
        # 发送完成信号
        yield f"data: {json.dumps({'type': 'done'})}\n\n"
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        logger.error(f"Error in stream_chat_response: {str(e)}")
        yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"

@router.post('/api/chat')
async def chat(
    request: ChatRequest,
    config: Config = Depends(get_config),
    llm_adapter = Depends(get_llm_adapter),
    tts_server = Depends(get_tts_server)
):
    """流式聊天接口"""
    return StreamingResponse(
        stream_chat_response(request, config, llm_adapter, tts_server),
        media_type="text/event-stream"
    )

@router.post('/api/agentic/chat')
async def agentic_chat(
    request: ChatRequest
):
    """Agent 入口"""
    mcp_client = get_mcp_client()
    # from langchain_community.tools.searx_search.tool import SearxSearchRun
    # from langchain_community.utilities import SearxSearchWrapper
    # search_tool= SearxSearchRun(wrapper=SearxSearchWrapper(searx_host="http://127.0.0.1:8001", k=3))
    if request.chat_id not in agents:
        llm_adapter = mcp_client.get_llm_adapter()
        llm = ChatOpenAI(model=request.model, base_url=llm_adapter.base_url, api_key=llm_adapter.api_key)
        logger.info(f"agentic_chat: {request.agents}")
        agent = Agent(
            model_name=request.model,
            llm=llm,
            agents=request.agents,
            mcp_client=mcp_client,
        )
        graph: StateGraph = await agent.build()
        agents[request.chat_id] = graph
    else:
        graph = agents[request.chat_id]
    async def process():
        input_data = None
        if request.is_resume:
            input_data = Command(resume=request.messages[-1]['content'])
        else:
            input_data = {
                "messages": [
                    (
                        "user",
                        request.messages[-1]['content']
                    )
                ],
                "thread_id": request.chat_id,
                "waiting_for_input": False
            }
        stream = graph.astream(
            input_data,
            {"configurable": {"thread_id": request.chat_id}, "recursion_limit": 150},
            subgraphs=True,
            stream_mode="messages",
        )
        cache_tool_calls = {}
        async for s in stream:
            logger.info('-'*100)
            logger.info(s)
            logger.info('-'*100)
            agent, message_chunk = s
            message_chunk, _ = message_chunk
            if isinstance(message_chunk, ToolMessage):
                continue
            if hasattr(message_chunk, 'tool_call_chunks') and len(message_chunk.tool_call_chunks) > 0:
                tool_call_chunk = message_chunk.tool_call_chunks[0]
                logger.info(f"agentic_chat: {message_chunk.tool_call_chunks}")
                index = tool_call_chunk.get('index', 0)
                if not index:
                    index = 0
                name = tool_call_chunk.get('name', '')
                if not name:
                    name = ''
                arguments = tool_call_chunk.get('args', '')
                if not arguments:
                    arguments = ''
                if index not in cache_tool_calls:
                    cache_tool_calls[index] = {
                        "name": name,
                        "arguments": arguments
                    }
                else:
                    cache_tool_calls[index]['name'] += name
                    cache_tool_calls[index]['arguments'] += arguments
            elif hasattr(message_chunk, 'response_metadata') and message_chunk.response_metadata.get('finish_reason') == 'tool_calls':
                logger.info(f"agentic_chat: {message_chunk}")
                call = []
                logger.info(f"agentic_chat: {cache_tool_calls}")
                for c in cache_tool_calls.values():
                    c['arguments'] = json.loads(c['arguments'])
                    call.append(c)
                cache_tool_calls = {}
                # 如果工具调用中有 request_user_input 工具，则需要等待用户输入
                # if any(c['name'] == 'request_user_input' for c in call):
                #     tc = next(c for c in call if c['name'] == 'request_user_input')
                #     yield f"data: {json.dumps({'type': 'text', 'content': tc['arguments']['prompt']})}\n\n"
                #     break
                yield f"data: {json.dumps({'type': 'tool_calls', 'content': call})}\n\n"
            else:
                yield f"data: {json.dumps({'type': 'text', 'content': message_chunk.content})}\n\n" 
    
    return StreamingResponse(
        process(),
        media_type="text/event-stream",
    )

@router.post('/api/tts')
async def text_to_speech(
    request: TTSRequest,
    config: Config = Depends(get_config),
    tts_server = Depends(get_tts_server)
):
    tts_server = init_tts_if_needed(config, tts_server)
    wav_data = tts_server.tts(request.text)
    return wav_data

@router.get('/api/tags')
async def tags(config: Config = Depends(get_config)):
    resp = requests.get(config.OLLAMA_HOST + '/api/tags')
    return resp.json()

@router.get('/api/settings')
async def get_settings(config: Config = Depends(get_config)):
    '''
    获取系统设置
    '''
    return config

@router.post('/api/settings')
async def set_settings(request: Request):
    '''
    设置系统设置
    '''
    json_data = await request.body()
    request_data = MCPClientConfig.model_validate_json(json_data)
    await init_mcp_client(request_data)

@router.get('/api/mcp_servers/{name}/status')
async def get_mcp_servers(name: str, config: Config = Depends(get_config)):
    '''
    获取MCP服务器状态
    '''
    return await get_mcp_client().get_server_details(name)



@router.get('/health')
async def health(config: Config = Depends(get_config)):
    return {
        'status': 'OK',
        'wwwPath': config.server.staticPath,
        'indexExists': os.path.exists(os.path.join(config.server.staticPath, 'index.html'))
    }
