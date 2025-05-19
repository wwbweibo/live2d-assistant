from fastapi import APIRouter, Request, Depends
from fastapi.responses import StreamingResponse
import os
import requests
import base64
import json
import asyncio
from search import BingSearchEngine
from typing import List, Optional, AsyncGenerator
from pydantic import BaseModel
from configuration import Config
from client import get_mcp_client, MCPClientConfig, init_mcp_client
import logging
logger = logging.getLogger(__name__)

router = APIRouter()

class ChatRequest(BaseModel):
    model: str
    messages: List[dict]
    web_search: Optional[bool] = False
    tts_enabled: Optional[bool] = False

class ChatResponse(BaseModel):
    message: str
    wav_data: List[str]

class TTSRequest(BaseModel):
    text: str

# 全局变量
config = None
tts_server = None
llm_adapter = None

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
        # 处理网络搜索
        if request.web_search:
            search_engine = BingSearchEngine(llm_adapter, request.model)
            search_text = request.messages[-1]['content']
            search_result = search_engine.searh_workflow(search_text)
            request.messages[-1]['content'] = '使用以下搜索结果作为上下文，回答用户的问题：' + '\n'.join(search_result) + '\n' + request.messages[-1]['content']
        
        # 流式处理查询
        async for chunk in get_mcp_client().stream_process_query(request.model, request.messages[-1]['content'], request.messages[:-1]):
            logger.info(f"stream_chat_response: {chunk}")
            yield f"data: {json.dumps({'type': 'text', 'content': chunk})}\n\n"
            await asyncio.sleep(0)  # 让出控制权给其他协程
        
        # 如果需要TTS，生成音频数据
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
