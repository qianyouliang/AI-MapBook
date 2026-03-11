"""
LLM 模型管理模块
AI-MapBook - 使用 DeepSeek API
"""
import os
import re
import json
from typing import List, Dict, Optional
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()


class LLMModel:
    """LLM 模型封装"""
    
    def __init__(self, api_key: str = None, model_type: str = "deepseek"):
        """
        初始化 LLM 模型
        
        Args:
            api_key: API 密钥
            model_type: 模型类型 (deepseek/qwen)
        """
        self.model_type = model_type
        self.api_key = api_key or os.getenv("DEEPSEEK_API_KEY", "")
        
        if not self.api_key:
            raise ValueError("请配置 DEEPSEEK_API_KEY")
        
        # 初始化 OpenAI 客户端
        from openai import OpenAI
        self.client = OpenAI(
            api_key=self.api_key,
            base_url="https://api.deepseek.com"
        )
    
    def chat(self, messages: List[Dict], stream: bool = True):
        """
        发送聊天请求
        
        Args:
            messages: 消息列表
            stream: 是否流式输出
        
        Returns:
            流式响应或完整响应
        """
        response = self.client.chat.completions.create(
            model="deepseek-chat",
            messages=messages,
            stream=stream
        )
        
        if stream:
            return response
        return response.choices[0].message.content
    
    def get_event_list(self, text: str) -> List[str]:
        """
        从文本中提取事件列表
        
        Args:
            text: 输入文本
        
        Returns:
            事件列表
        """
        prompt = f"""您是一名地理分析师，您的任务是分析给定的历史或新闻情报等文本，定位关注事件的内容，发生的位置，时间，相关的人物和历史事件，以文本中地点变化为决定性指标划分文本为单独的事件(包含地理位置(必须包含)，事件内容等信息(可选)，并且按照事件前后顺序排列；
        格式如下：
        xxx于xxx时间在xxx地做了xxx事情，造成了xxx影响；
        ---
        xxx于xxx时间在xxx地做了xxx事情，造成了xxx影响；
        ```
        不同的事件严格要求使用4个-组成的间隔符号 --- 划分开来，完整且精炼的语言进行描述。
        好的，请根据以下客户输入的问题进行分析划分事件,严格完整输出，上面的案例只是格式举例，实际输出请根据以下的内容：
            {text}
        """
        
        response = self.client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": "您是一名地理事件划分师，您的任务是从文本中提取事件并进行划分。"},
                {"role": "user", "content": prompt}
            ],
            stream=False
        )
        
        content = response.choices[0].message.content
        return self._split_event(content)
    
    def process_event(self, event: str, language: str = "中文") -> Dict:
        """
        处理单个事件，提取详细信息
        
        Args:
            event: 事件描述
            language: 输出语言
        
        Returns:
            事件信息字典
        """
        prompt = f"""请从以下事件描述中提取详细信息，以JSON格式返回：
        {{
            "event_title": "事件标题",
            "event_type": "事件类型（战争/政治/经济/文化/自然灾害等）",
            "event_content": "事件内容摘要",
            "address": "事件发生地点（必须包含国家、城市等详细信息）",
            "keys": "关键词（用逗号分隔）"
        }}
        
        事件描述：{event}
        
        请只返回JSON，不要其他内容。"""
        
        response = self.client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": "您是一个地理信息提取助手。"},
                {"role": "user", "content": prompt}
            ],
            stream=False
        )
        
        content = response.choices[0].message.content
        
        # 解析 JSON
        try:
            # 尝试提取 JSON
            import re
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except:
            pass
        
        # 返回默认值
        return {
            "event_title": event[:20],
            "event_type": "未知",
            "event_content": event,
            "address": "",
            "keys": ""
        }
    
    @staticmethod
    def _split_event(text: str) -> List[str]:
        """分割事件列表"""
        if not text:
            return []
        
        # 按 --- 分割
        events = re.split(r'---+', text)
        
        # 清理每个事件
        result = []
        for event in events:
            event = event.strip()
            if event and len(event) > 5:
                result.append(event)
        
        return result


def create_model(api_key: str = None, model_type: str = "deepseek") -> LLMModel:
    """
    创建 LLM 模型实例
    
    Args:
        api_key: API 密钥
        model_type: 模型类型
    
    Returns:
        LLMModel 实例
    """
    return LLMModel(api_key=api_key, model_type=model_type)
