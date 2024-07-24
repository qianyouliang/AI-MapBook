# from openai import OpenAI
# import os
# import re
# import json
# from datetime import datetime


# class LLM:
#     def __init__(self,api_key: str,file_path:str = '../event_list.json' ,model_type:str = "deepseek",  ):
#         self.file_path = file_path
#         self.model_type = model_type
#         self.res = ''
#         if self.model_type=='deepseek':
#             # base_url = os.getenv("BASE_URL")
#             base_url = "https://api.deepseek.com"
#             # api_key = os.getenv("DEEPSEEK_API_KEY")
#             self.client = OpenAI(api_key=api_key, base_url=base_url)
   
#     def get_event_list(self,text:str):
#         prompt:str = '''
#                     您是一名地理分析师，您的任务是分析给定的历史或新闻情报等文本，定位关注事件的内容，发生的位置，时间，相关的人物和历史事件，以文本中地点变化为决定性指标划分文本为单独的事件(包含地理位置(必须包含)，事件内容等信息(可选)，并且按照事件前后顺序排列；
#             格式如下：
#             ```
#             xxx于xxx时间在xxx地做了xxx事情，造成了xxx影响；
#             ------
#             xxx于xxx时间在xxx地做了xxx事情，造成了xxx影响；
#             ------
#             xxx于xxx时间在xxx地做了xxx事情，造成了xxx影响；
#             ```
#             不同的事件严格要求使用 ------ 划分开来，完整且精炼的语言进行描述。
#             好的，请根据以下用户输入的问题进行分析划分事件,严格完整输出：
#                 {text}
#             '''.format(text = text)

#         response = self.client.chat.completions.create(
#             model="deepseek-chat",
#             messages=[
#                 {"role": "system", "content": "您是一名地理事件划分师，您的任务是从文本中提取事件并进行划分。"},
#                 {"role": "user", "content": prompt},
#             ],
#             stream=False
#         )
#         eventList = LLM.split_event(response.choices[0].message.content)

#         return eventList

#     def run(self,text:str,language:str = '中文'):

#         event_text_List = self.get_event_list(text)
#         eventList = []
#         for event_text in event_text_List:
#             prompt:str = '''
#                 您是一名地理分析师，您的任务是分析给定的历史或新闻情报，定位事件的内容，发生的位置，时间，相关的人物和历史事件，然后给出事件的地理描述，作为事件的属性信息。
#             你要生成的内容要包裹在```event```中，案例格式如下，要包含以下字段，：
#             ```event
      
#             "event_title": "有关ABC公司新产品的情报",
#             "event_type": "市场情报",
#             "event_content": "根据对社交媒体平台的监听和分析，我们发现了以下有关ABC公司新产品的情报：1. ABC公司将在本月底发布其新的智能手机，该手机将具有更快的处理器、更大的内存和更长的电池寿命。2. 该新产品将是ABC公司在智能手机市场上的重要攻势，旨在与竞争对手的旗舰产品竞争。3. 在社交媒体上，用户对该新产品的期待度较高，有些用户甚至表示愿意预订该产品。",
#             "keys": ["Twitter", "Facebook", "LinkedIn"],
#             "address": "中国北京",
#             ```
#             生成的address要求：
#             - 严格符合地理编码和OSM的规范，
#             - 国外地址用英语，
#             - 过去的地址使用现在的地址来表示，不然地理编码不能识别；
#             - 严格要求一个事件一个地址，不能同时表示多个地址
#             - 符合官方地名，最大化让地理编码器能识别；
#         生成的内容是一个json格式 用大括号json格式扩住,并将将生成的情报信息包裹在```event```中，要求使用中文、完整且精炼的语言进行描述。
#         好的，请根据以下用户输入的问题进行分析生成回答,严格{language}输出：
#             {event}
#         '''.format(event = event_text,language = language)
#             response = self.client.chat.completions.create(
#                 model="deepseek-chat",
#                 messages=[
#                     {"role": "system", "content": "您是一名地理事件分析技术专家，您的任务是从分析文本，定位地理信息并获取相关事件。"},
#                     {"role": "user", "content": prompt},
#                 ],
#                 stream=False
#             )
#             event = LLM.parse_event(response.choices[0].message.content)
#             eventList.append(event)    
#         self.save_event(event) # 保存任务
#         return eventList

#     @staticmethod
#     def parse_event(content): # 从模型生成中字符串匹配提取生成的代码
#         pattern = r'```event(.*?)```'  # 使用非贪婪匹配
#         match = re.search(pattern, content, re.DOTALL)
#         event = match.group(1) if match else content
#         event = json.loads(event,strict=False)  # 转换为json格式
#         return event

#     @staticmethod
#     def split_event(event_text: str) -> list:
#         # 使用 '------' 作为分隔符拆分字符串
#         events = event_text.split('------')
#         # 去除每个事件字符串的前后空白
#         events = [event.strip() for event in events if event.strip()]
#         return events

#     def save_event(self, event):
#         event['create_time'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
#         if os.path.exists(self.file_path):
#             with open(self.file_path, 'r',encoding='utf-8') as file:
#                 events = json.load(file,strict=False)
#             events.append(event)
#         else:
#             events = [event]
#         with open(self.file_path, 'w',encoding='utf-8') as file:
#             json.dump(events, file, ensure_ascii=False)

from openai import OpenAI
import os
import re
import json
from datetime import datetime

class LLM:
    def __init__(self, api_key: str, file_path: str = '../event_list.json', model_type: str = "deepseek"):
        self.file_path = file_path
        self.model_type = model_type
        self.res = ''
        if self.model_type == 'deepseek':
            base_url = "https://api.deepseek.com"
            self.client = OpenAI(api_key=api_key, base_url=base_url)

    def get_event_list(self, text: str):
        prompt: str = '''
        您是一名地理分析师，您的任务是分析给定的历史或新闻情报等文本，定位关注事件的内容，发生的位置，时间，相关的人物和历史事件，以文本中地点变化为决定性指标划分文本为单独的事件(包含地理位置(必须包含)，事件内容等信息(可选)，并且按照事件前后顺序排列；
        格式如下：
        ```
        xxx于xxx时间在xxx地做了xxx事情，造成了xxx影响；
        ------
        xxx于xxx时间在xxx地做了xxx事情，造成了xxx影响；
        ```
        不同的事件严格要求使用 ------ 划分开来，完整且精炼的语言进行描述。
        好的，请根据以下用户输入的问题进行分析划分事件,严格完整输出，上面的案例只是格式举例，实际输出请根据以下的内容：
            {text}
        '''.format(text=text)

        response = self.client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": "您是一名地理事件划分师，您的任务是从文本中提取事件并进行划分。"},
                {"role": "user", "content": prompt},
            ],
            stream=False
        )

        eventList = LLM.split_event(response.choices[0].message.content)

        return eventList

    def process_event(self, event_text: str, language: str = '英语'):
        prompt: str = '''
        您是一名地理分析师，您的任务是分析给定的历史或新闻情报，定位事件的内容，发生的位置，时间，相关的人物和历史事件，然后给出事件的地理描述，作为事件的属性信息。
        你要生成的内容要包裹在```event```中，案例格式如下，要包含以下字段，：
        ```event
        "event_title": "有关ABC公司新产品的情报",
        "event_type": "市场情报",
        "event_content": "根据对社交媒体平台的监听和分析，我们发现了以下有关ABC公司新产品的情报：1. ABC公司将在本月底发布其新的智能手机，该手机将具有更快的处理器、更大的内存和更长的电池寿命。2. 该新产品将是ABC公司在智能手机市场上的重要攻势，旨在与竞争对手的旗舰产品竞争。3. 在社交媒体上，用户对该新产品的期待度较高，有些用户甚至表示愿意预订该产品。",
        "keys": ["Twitter", "Facebook", "LinkedIn"],
        "address": "beijing",
        ```
        生成的address要求：
        - 严格符合地理编码和OSM的规范，
        - 地址address严格使用英语，
        - 过去的地址使用现在的地址来表示，不然地理编码不能识别；
        - 严格要求一个事件仅用一个地址来表达，不能同时用多个地址描述
        - 符合官方地名，最大化让地理编码器能识别；

        生成的内容是一个json格式 用大括号json格式扩住,并将将生成的情报信息包裹在```event```中，要求完整且精炼的语言进行描述。
        好的，请根据以下用户输入的问题进行分析生成回答，address字段内容严格使用{language}输出，其他字段内容中文输出：
            {event}
        '''.format(event=event_text, language=language)

        response = self.client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": "您是一名地理事件分析技术专家，您的任务是从分析文本，定位地理信息并获取相关事件。"},
                {"role": "user", "content": prompt},
            ],
            stream=False
        )
        event = LLM.parse_event(response.choices[0].message.content)
        # self.save_event(event)  # 保存任务
        
        return event

    def generate_text(self):
        pass

    @staticmethod
    def parse_event(content):  # 从模型生成中字符串匹配提取生成的代码
        pattern = r'```event(.*?)```'  # 使用非贪婪匹配
        match = re.search(pattern, content, re.DOTALL)
        event = match.group(1) if match else content
        event = json.loads(event, strict=False)  # 转换为json格式
        return event

    @staticmethod
    def split_event(event_text: str) -> list:
        # 使用 '------' 作为分隔符拆分字符串
        events = event_text.split('------')
        # 去除每个事件字符串的前后空白
        events = [event.strip() for event in events if event.strip()]
        return events

    def save_event(self, event):
        event['create_time'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if os.path.exists(self.file_path):
            with open(self.file_path, 'r', encoding='utf-8') as file:
                events = json.load(file, strict=False)
            events.append(event)
        else:
            events = [event]
        with open(self.file_path, 'w', encoding='utf-8') as file:
            json.dump(events, file, ensure_ascii=False)

