import sys
import os
import torchaudio
import torch
import io

def tts_init(install_path: str, model_path: str, prompt_path: str, sample_rate: int, prompt_text: str):
    # Convert to absolute paths
    install_path = os.path.abspath(install_path)
    cosyvoice_path = os.path.join(install_path)
    matcha_tts_path = os.path.join(install_path, 'third_party', 'Matcha-TTS')

    # Add to sys.path
    sys.path.append(cosyvoice_path)
    sys.path.append(matcha_tts_path)
    print("Current sys.path:", sys.path)    
    # Now import the modules
    from cosyvoice.cli.cosyvoice import CosyVoice, CosyVoice2
    from cosyvoice.utils.file_utils import load_wav

    cosyvoice = CosyVoice2(model_path, load_jit=False, load_trt=False, fp16=False)
    prompt_speech_16k = load_wav(prompt_path, sample_rate)
    return cosyvoice, prompt_speech_16k

class TtsServer:
    def __init__(self, cosyvoice, prompt_speech: torch.Tensor, prompt_text: str):
        self.cosyvoice = cosyvoice
        self.prompt_speech = prompt_speech
        self.prompt_text = prompt_text

    def tts(self, text: str):
        audios = []
        for i, j in enumerate(self.cosyvoice.inference_zero_shot(text, self.prompt_text, self.prompt_speech, stream=False)):
            audio_bytes = io.BytesIO()
            torchaudio.save(audio_bytes, j['tts_speech'], self.cosyvoice.sample_rate, format='wav')
            audios.append(audio_bytes.getvalue())
        return audios