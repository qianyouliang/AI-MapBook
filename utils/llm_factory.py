"""
多API支持模块
AI-MapBook 支持多种LLM API
"""
import os
from typing import Optional, Dict, Any
from abc import ABC, abstractmethod


class BaseLLM(ABC):
    """LLM 基类"""
    
    @abstractmethod
    def chat(self, messages: list) -> str:
        """发送聊天请求"""
        pass
    
    @abstractmethod
    def get_event_list(self, text: str) -> list:
        """提取事件列表"""
        pass
    
    @abstractmethod
    def process_event(self, event: str, **kwargs) -> Dict:
        """处理单个事件"""
        pass


class DeepSeekLLM(BaseLLM):
    """DeepSeek API"""
    
    def __init__(self, api_key: str, base_url: str = "https://api.deepseek.com"):
        from openai import OpenAI
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        self.model = "deepseek-chat"
    
    def chat(self, messages: list) -> str:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            stream=False
        )
        return response.choices[0].message.content
    
    def get_event_list(self, text: str) -> list:
        # 使用现有的 prompt
        pass
    
    def process_event(self, event: str, **kwargs) -> Dict:
        pass


class ClaudeLLM(BaseLLM):
    """Claude API"""
    
    def __init__(self, api_key: str):
        # 需要 anthropic SDK
        pass
    
    def chat(self, messages: list) -> str:
        pass
    
    def get_event_list(self, text: str) -> list:
        pass
    
    def process_event(self, event: str, **kwargs) -> Dict:
        pass


class GeminiLLM(BaseLLM):
    """Gemini API"""
    
    def __init__(self, api_key: str):
        pass
    
    def chat(self, messages: list) -> str:
        pass
    
    def get_event_list(self, text: str) -> list:
        pass
    
    def process_event(self, event: str, **kwargs) -> Dict:
        pass


class LLMFactory:
    """LLM 工厂类"""
    
    _providers = {
        "deepseek": DeepSeekLLM,
        "claude": ClaudeLLM,
        "gemini": GeminiLLM,
    }
    
    @classmethod
    def create(cls, provider: str, api_key: str, **kwargs) -> Optional[BaseLLM]:
        """
        创建 LLM 实例
        
        Args:
            provider: 提供商名称
            api_key: API 密钥
            **kwargs: 其他参数
        
        Returns:
            LLM 实例
        """
        if provider not in cls._providers:
            raise ValueError(f"不支持的提供商: {provider}")
        
        return cls._providers[provider](api_key, **kwargs)
    
    @classmethod
    def get_available_providers(cls) -> list:
        """获取支持的提供商列表"""
        return list(cls._providers.keys())


def create_llm(model_type: str, api_key: str = None, **kwargs) -> BaseLLM:
    """
    创建 LLM 实例的便捷函数
    
    Args:
        model_type: 模型类型
        api_key: API 密钥
        **kwargs: 其他参数
    
    Returns:
        LLM 实例
    """
    if not api_key:
        from dotenv import load_dotenv
        load_dotenv()
        api_key = os.getenv(f"{model_type.upper()}_API_KEY")
    
    return LLMFactory.create(model_type, api_key, **kwargs)
