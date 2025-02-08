import os
import json
from typing import Any, Dict

class Config:
    # 服务器配置
    PYTHON_EXEC = ''
    SERVER_PATH = ''
    PORT = 5000
    HOST = '0.0.0.0'
    STATIC_PATH = 'static'
    
    # Ollama配置
    OLLAMA_HOST = 'http://127.0.0.1:11434'
    
    # TTS配置
    TTS_ENABLED = False
    TTS_MODULE_PATH = ''
    TTS_PROMPT_PATH = 'asset/zero_shot_prompt.wav'
    TTS_PROMPT_TEXT = '希望你以后能够做的比我还好呦。'
    TTS_PROMPT_SAMPLE_RATE = 16000
    TTS_COSYVOICE_INSTALL_PATH = '.'

    @classmethod
    def _convert_value(cls, original_value: Any, new_value: Any) -> Any:
        """根据原始值的类型转换新值"""
        if isinstance(original_value, bool):
            return str(new_value).lower() == 'true'
        elif isinstance(original_value, int):
            return int(new_value)
        elif isinstance(original_value, float):
            return float(new_value)
        return new_value

    @classmethod
    def _convert_key(cls, key: str) -> str:
        """将JSON配置键转换为类属性名"""
        return key.upper()

    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> 'Config':
        """从字典加载配置"""
        if 'server' in config_dict:
            server_config = config_dict['server']
            # 处理基础配置
            base_mappings = {
                'pythonExec': 'PYTHON_EXEC',
                'serverPath': 'SERVER_PATH',
                'port': 'PORT',
                'host': 'HOST',
                'staticPath': 'STATIC_PATH',
                'ollamaHost': 'OLLAMA_HOST'
            }
            
            for json_key, class_key in base_mappings.items():
                if json_key in server_config:
                    value = server_config[json_key]
                    if hasattr(cls, class_key):
                        original_value = getattr(cls, class_key)
                        converted_value = cls._convert_value(original_value, value)
                        setattr(cls, class_key, converted_value)

            # 处理TTS配置
            if 'tts' in server_config:
                tts_config = server_config['tts']
                tts_mappings = {
                    'enabled': 'TTS_ENABLED',
                    'modulePath': 'TTS_MODULE_PATH',
                    'promptPath': 'TTS_PROMPT_PATH',
                    'promptText': 'TTS_PROMPT_TEXT',
                    'sampleRate': 'TTS_PROMPT_SAMPLE_RATE',
                    'cosyvoiceInstallPath': 'TTS_COSYVOICE_INSTALL_PATH'
                }
                
                for json_key, class_key in tts_mappings.items():
                    if json_key in tts_config:
                        value = tts_config[json_key]
                        if hasattr(cls, class_key):
                            original_value = getattr(cls, class_key)
                            converted_value = cls._convert_value(original_value, value)
                            setattr(cls, class_key, converted_value)
        
        return cls

    @classmethod
    def from_json(cls, json_path: str) -> 'Config':
        """从JSON文件加载配置"""
        try:
            if not os.path.exists(json_path):
                print(f"配置文件 {json_path} 不存在，使用默认配置")
                return cls
            
            with open(json_path, 'r', encoding='utf-8') as f:
                config_dict = json.load(f)
            return cls.from_dict(config_dict)
        except Exception as e:
            print(f"读取配置文件失败: {str(e)}，使用默认配置")
            return cls

    @classmethod
    def from_env(cls) -> 'Config':
        """从环境变量加载配置"""
        for key in dir(cls):
            if key.isupper():
                env_value = os.environ.get(key)
                if env_value is not None:
                    original_value = getattr(cls, key)
                    converted_value = cls._convert_value(original_value, env_value)
                    setattr(cls, key, converted_value)
        return cls

    @classmethod
    def load(cls, json_path: str = None) -> 'Config':
        """
        加载配置的主入口
        优先级: 环境变量 > JSON文件 > 默认值
        """
        if json_path:
            cls.from_json(json_path)
        else:
            cls.from_env()
        return cls

    def to_dict(self) -> Dict[str, Any]:
        """将配置转换为字典格式"""
        server_config = {
            'pythonExec': self.PYTHON_EXEC,
            'serverPath': self.SERVER_PATH,
            'port': self.PORT,
            'host': self.HOST,
            'staticPath': self.STATIC_PATH,
            'ollamaHost': self.OLLAMA_HOST,
            'tts': {
                'enabled': self.TTS_ENABLED,
                'modulePath': self.TTS_MODULE_PATH,
                'promptPath': self.TTS_PROMPT_PATH,
                'promptText': self.TTS_PROMPT_TEXT,
                'sampleRate': self.TTS_PROMPT_SAMPLE_RATE,
                'cosyvoiceInstallPath': self.TTS_COSYVOICE_INSTALL_PATH
            }
        }
        return {'server': server_config}

    def save(self, json_path: str) -> None:
        """保存配置到JSON文件"""
        try:
            config_dict = self.to_dict()
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(config_dict, f, indent=4, ensure_ascii=False)
            print(f"配置已保存到: {json_path}")
        except Exception as e:
            print(f"保存配置文件失败: {str(e)}")

    def __str__(self) -> str:
        """返回当前配置的字符串表示"""
        config_items = []
        for key in dir(self):
            if key.isupper():
                value = getattr(self, key)
                config_items.append(f"{key} = {value}")
        return "\n".join(config_items) 