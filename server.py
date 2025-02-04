import sys
from flask import Flask, request, send_from_directory
from flask_cors import CORS
import argparse
import os
import requests
import base64
import io
import re

app = Flask(__name__)
tts_server = None

def init_tts_if_needed():
    global tts_server
    if args.tts_enabled and tts_server is None:
        from tts import tts_init, TtsServer
        cosyvoice, prompt_speech_16k = tts_init(args.tts_cosyvoice_install_path,
                                               args.tts_module_path, 
                                               args.tts_prompt_path, 
                                               args.tts_prompt_sample_rate, 
                                               args.tts_prompt_text)
        tts_server = TtsServer(cosyvoice, prompt_speech_16k, args.tts_prompt_text)

# 允许所有跨域
CORS(app,
     resources=['/*'],
     origins=["*"],
     methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
     supports_credentials=True)  

@app.route('/api/chat', methods=['POST'])
def chat():
    req_json = request.get_json()
    req = requests.post(args.ollama_host + '/api/chat', json=req_json)
    message = req.json()['message']['content']
    # 对于deepseek-r1的特殊处理
    if isinstance(message, dict):
        message = message['content']
        # 移除 <think> 和 </think>之间的内容
    message = re.sub(r'<think>.*(\n.*)*</think>\n*', '', message)
    base64_waves = []
    if req_json['tts_enabled']:
        init_tts_if_needed()
        wav_data = tts_server.tts(message)
        # wav_data 是多个wav文件的数据，拼接到一起返回
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
    prompt = data.get('prompt', '希望你以后能够做的比我还好呦。')
    # 生成语音
    wav_data = tts_server.tts(text)
    return wav_data

@app.route('/api/tags')
def tags():
    resp = requests.get(args.ollama_host + '/api/tags')
    return resp.json()

@app.route('/health')
def health():
    return {
        'status': 'OK',
        'wwwPath': args.static_path,
        'indexExists': os.path.exists(os.path.join(args.static_path, 'index.html'))
    }

@app.route('/')
def index():
    return send_from_directory(args.static_path, 'index.html')

#处理静态文件请求
@app.route('/<path:path>')
def send_static_file(path):
    print(os.path.join(args.static_path, path))
    return send_from_directory(args.static_path, path)


if __name__ == '__main__':
    # 添加命令行参数
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=5000, help='端口号')
    parser.add_argument('--host', type=str, default='0.0.0.0', help='主机地址')
    parser.add_argument('--static_path', type=str, default='static', help='静态文件路径')
    parser.add_argument('--ollama_host', type=str, default='http://127.0.0.1:11434', help='ollama地址')
    group = parser.add_argument_group('tts')
    group.add_argument('--tts_enabled', type=bool, default=False, help='是否启用tts')
    group.add_argument('--tts_module_path', type=str, default='', help='模型路径')
    group.add_argument('--tts_prompt_path', type=str, default='asset/zero_shot_prompt.wav', help='提示音路径')
    group.add_argument('--tts_prompt_text', type=str, default='希望你以后能够做的比我还好呦。', help='提示文本')
    group.add_argument('--tts_prompt_sample_rate', type=int, default=16000, help='采样率')
    group.add_argument('--tts_cosyvoice_install_path', type=str, default='.', help='cosyvoice安装路径')
    args = parser.parse_args()
    app.run(host=args.host, port=args.port)

