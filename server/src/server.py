from flask import Flask, request, send_from_directory
from flask_cors import CORS
import os
import requests
import base64
from search import BingSearchEngine
from config import Config
import argparse
import logging
import json
from mcp.client import MCPClient
from llm_adapters import new_llm_adapter


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)
tts_server = None
llm_adapter = None
mcp_client = None

def init_tts_if_needed():
    """初始化TTS服务"""
    global tts_server
    if config.TTS_ENABLED and tts_server is None:
        from tts import tts_init, TtsServer
        cosyvoice, prompt_speech_16k = tts_init(
            config.TTS_COSYVOICE_INSTALL_PATH,
            config.TTS_MODULE_PATH,
            config.TTS_PROMPT_PATH,
            config.TTS_PROMPT_SAMPLE_RATE,
            config.TTS_PROMPT_TEXT
        )
        tts_server = TtsServer(cosyvoice, prompt_speech_16k, config.TTS_PROMPT_TEXT)

# 允许所有跨域
CORS(app,
     resources=['/*'],
     origins=["*"],
     methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
     supports_credentials=True)

@app.route('/api/chat', methods=['POST'])
async def chat():
    req_json = request.get_json()
    model = req_json['model']
    if 'web_search' in req_json and req_json['web_search']:
        search_engine = BingSearchEngine(llm_adapter, model)
        search_text = req_json['messages'][-1]['content']
        search_result = search_engine.searh_workflow(search_text)
        req_json['messages'][-1]['content'] = '使用以下搜索结果作为上下文，回答用户的问题：' + '\n'.join(search_result) + '\n' + req_json['messages'][-1]['content']
    message, history = await mcp_client.process_query(model, req_json['messages'][-1]['content'])
    base64_waves = []
    
    if req_json['tts_enabled']:
        init_tts_if_needed()
        wav_data = tts_server.tts(message)
        for data in wav_data:
            base64_waves.append(base64.b64encode(data).decode('utf-8'))
            
    return {
        "message": message,
        "wav_data": base64_waves
    }

@app.route('/api/tts', methods=['POST'])
async def text_to_speech():
    init_tts_if_needed()
    data = request.get_json()
    text = data.get('text', '')
    wav_data = tts_server.tts(text)
    return wav_data

@app.route('/api/tags')
async def tags():
    resp = requests.get(config.OLLAMA_HOST + '/api/tags')
    return resp.json()

@app.route('/api/settings', methods=['GET'])
async def get_settings():
    '''
    获取系统设置
    '''
    return config

@app.route('/api/settings', methods=['POST'])
async def set_settings():
    '''
    设置系统设置
    '''
    data = request.get_json()
    config.update(data)
    return config

@app.route('/health')
async def health():
    return {
        'status': 'OK',
        'wwwPath': config.STATIC_PATH,
        'indexExists': os.path.exists(os.path.join(config.STATIC_PATH, 'index.html'))
    }

@app.route('/')
async def index():
    return send_from_directory(config.STATIC_PATH, 'index.html')

@app.route('/<path:path>')
async def send_static_file(path):
    return send_from_directory(config.STATIC_PATH, path)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="启动Web服务器")
    parser.add_argument('--config', type=str, default='config.json', help='配置文件路径')
    args = parser.parse_args()
    if os.path.exists(args.config):
        with open(args.config, 'r') as f:
            config = json.load(f)
    llm_adapter = new_llm_adapter(config['llm']['provider'], config['llm']['config'], logger)
    mcp_client = MCPClient(config['mcp_servers'], llm_adapter, logger)
    app.run(host=config.HOST, port=config.PORT)

