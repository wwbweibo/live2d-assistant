from flask import Flask, request, send_from_directory
from flask_cors import CORS
from llm import OllamaClient
import os
import requests
import base64
from search import BingSearchEngine
from config import Config
import argparse

app = Flask(__name__)
tts_server = None
ollama_client = None
config = None

def init_config(path: str = None):
    """初始化配置"""
    global config
    # 可以从命令行参数或环境变量获取配置文件路径
    config_path = os.environ.get('CONFIG_PATH', path)
    if config_path is None:
        raise ValueError("配置文件路径不能为空")
    config = Config.load(config_path)
    print("当前配置：")
    print(config)

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

def init_ollama():
    """初始化Ollama客户端"""
    global ollama_client
    ollama_client = OllamaClient(config.OLLAMA_HOST)

# 允许所有跨域
CORS(app,
     resources=['/*'],
     origins=["*"],
     methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
     supports_credentials=True)

@app.route('/api/chat', methods=['POST'])
def chat():
    req_json = request.get_json()
    model = req_json['model']
    if 'web_search' in req_json and req_json['web_search']:
        search_engine = BingSearchEngine(ollama_client, model)
        search_text = req_json['messages'][-1]['content']
        search_result = search_engine.searh_workflow(search_text)
        req_json['messages'][-1]['content'] = '使用以下搜索结果作为上下文，回答用户的问题：' + '\n'.join(search_result) + '\n' + req_json['messages'][-1]['content']
    
    message = ollama_client.chat(req_json)
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
def text_to_speech():
    init_tts_if_needed()
    data = request.get_json()
    text = data.get('text', '')
    wav_data = tts_server.tts(text)
    return wav_data

@app.route('/api/tags')
def tags():
    resp = requests.get(config.OLLAMA_HOST + '/api/tags')
    return resp.json()

@app.route('/health')
def health():
    return {
        'status': 'OK',
        'wwwPath': config.STATIC_PATH,
        'indexExists': os.path.exists(os.path.join(config.STATIC_PATH, 'index.html'))
    }

@app.route('/')
def index():
    return send_from_directory(config.STATIC_PATH, 'index.html')

@app.route('/<path:path>')
def send_static_file(path):
    return send_from_directory(config.STATIC_PATH, path)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="启动Web服务器")
    parser.add_argument('--config', type=str, default='config.json', help='配置文件路径')
    args = parser.parse_args()
    init_config(args.config)
    init_ollama()
    app.run(host=config.HOST, port=config.PORT)

