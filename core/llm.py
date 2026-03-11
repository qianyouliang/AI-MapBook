"""
LLM 模块
AI-MapBook 语言模型封装
"""
import os
import re
import json
from typing import List, Dict
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()


class LLMModel:
    """DeepSeek LLM 模型"""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("DEEPSEEK_API_KEY", "")
        if not self.api_key:
            raise ValueError("请配置 DEEPSEEK_API_KEY")
        
        self.client = OpenAI(
            api_key=self.api_key,
            base_url="https://api.deepseek.com"
        )
    
    def chat(self, messages: List[Dict], stream: bool = True):
        return self.client.chat.completions.create(
            model="deepseek-chat",
            messages=messages,
            stream=stream
        )
    
    def get_event_list(self, text: str) -> List[str]:
        prompt = f"""分析以下文本，提取地理事件。
格式：事件描述 --- 事件描述
{text}"""
        
        response = self.client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": "你是地理事件提取专家。"},
                {"role": "user", "content": prompt}
            ],
            stream=False
        )
        
        content = response.choices[0].message.content
        return self._split_event(content)
    
    def process_event(self, event: str) -> Dict:
        prompt = f"""提取事件信息，返回JSON：
{{"event_title":"标题","event_type":"类型","event_content":"内容","address":"地址","keys":"关键词"}}
事件：{event}"""
        
        response = self.client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": "你是JSON提取器。"},
                {"role": "user", "content": prompt}
            ],
            stream=False
        )
        
        try:
            import re
            match = re.search(r'\{.+\}', response.choices[0].message.content, re.DOTALL)
            if match:
                return json.loads(match.group())
        except:
            pass
        
        return {"event_title": event[:20], "event_type": "未知", "address": ""}
    
    @staticmethod
    def _split_event(text: str) -> List[str]:
        if not text:
            return []
        events = re.split(r'---+', text)
        return [e.strip() for e in events if e.strip() and len(e) > 5]
