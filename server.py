import sys
sys.path.append('third_party/Matcha-TTS')
from cosyvoice.cli.cosyvoice import CosyVoice, CosyVoice2
from cosyvoice.utils.file_utils import load_wav
import torchaudio
import torch    
from flask import Flask, request, send_from_directory
from flask_cors import CORS
import argparse
import os
import requests
import base64
import io

app = Flask(__name__)
# 允许所有跨域
CORS(app,
     resources=['/*'],
     origins=["*"],
     methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
     supports_credentials=True)  

class TtsServer:
    def __init__(self, cosyvoice: CosyVoice2, 
                 prompt_speech: torch.Tensor,
                 prompt_text: str):
        self.cosyvoice = cosyvoice
        self.prompt_speech = prompt_speech
        self.prompt_text = prompt_text

    def tts(self, text:str):
        audios = []
        for i, j in enumerate(self.cosyvoice.inference_zero_shot(text, self.prompt_text, self.prompt_speech, stream=False)):
            audio_bytes = io.BytesIO()
            torchaudio.save(audio_bytes, j['tts_speech'], self.cosyvoice.sample_rate, format='wav')
            audios.append(audio_bytes.getvalue())
        return audios

@app.route('/api/chat', methods=['POST'])
def chat():
    req = requests.post(args.ollama_host + '/api/chat', json=request.get_json())
    message = req.json()['message']['content']
    wav_data = tts_server.tts(message)
    # wav_data 是多个wav文件的数据，拼接到一起返回
    base64_waves = []
    for data in wav_data:
        base64_waves.append(base64.b64encode(data).decode('utf-8'))
    return {
        "message": message,
        "wav_data": base64_waves
    }

@app.route('/api/tts', methods=['POST'])
def text_to_speech():
    data = request.get_json()
    text = data.get('text', '')
    prompt = data.get('prompt', '希望你以后能够做的比我还好呦。')
    # 生成语音
    wav_data = tts_server.tts(text)
    return wav_data

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

def tts_init(model_path:str, prompt_path:str, sample_rate:int, prompt_text:str):
    cosyvoice = CosyVoice2(model_path, load_jit=False, load_trt=False, fp16=False)
    prompt_speech_16k = load_wav(prompt_path, sample_rate)
    return cosyvoice, prompt_speech_16k

if __name__ == '__main__':
    # 添加命令行参数
    parser = argparse.ArgumentParser()
    parser.add_argument('--model_path', type=str, default='', help='模型路径')
    parser.add_argument('--prompt_path', type=str, default='asset/zero_shot_prompt.wav', help='提示音路径')
    parser.add_argument('--sample_rate', type=int, default=16000, help='采样率')
    parser.add_argument('--prompt_text', type=str, default='希望你以后能够做的比我还好呦。', help='提示文本')
    parser.add_argument('--port', type=int, default=5000, help='端口号')
    parser.add_argument('--host', type=str, default='0.0.0.0', help='主机地址')
    parser.add_argument('--static_path', type=str, default='static', help='静态文件路径')
    parser.add_argument('--ollama_host', type=str, default='http://127.0.0.1:11434', help='ollama地址')
    args = parser.parse_args()
    cosyvoice, prompt_speech_16k = tts_init(args.model_path, args.prompt_path, args.sample_rate, args.prompt_text)
    tts_server = TtsServer(cosyvoice, prompt_speech_16k, args.prompt_text)
    app.run(host=args.host, port=args.port)

