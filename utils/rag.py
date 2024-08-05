import os
import faiss
from io import BytesIO
from dotenv import load_dotenv, find_dotenv
from llama_index.vector_stores.faiss import FaissVectorStore
from llama_index.core import StorageContext, SimpleDirectoryReader, Document,VectorStoreIndex, load_index_from_storage, Settings
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.llms.openai_like import OpenAILike
from typing import List, Dict
from modelscope import snapshot_download, AutoModel, AutoTokenizer


class RAG:

    def __init__(self, api_key:str,persist_dir: str = './storage', embed_model_name: str = "models/AI-ModelScope/bge-small-zh-v1___5",model_type:str='deepseek'):
        self.persist_dir = persist_dir
        self.embed_model_name = embed_model_name
        self.model_type = model_type
        
         # Check if the embedding model exists, if not, download it
        if not os.path.exists(self.embed_model_name):
            self.download_embedding_model()
        # Initialize embedding model
        self.embed_model = HuggingFaceEmbedding(model_name=self.embed_model_name)
        Settings.embed_model = self.embed_model
        # Initialize FAISS index
        self.faiss_index = faiss.IndexFlatL2(512)
        self.vector_store = FaissVectorStore(faiss_index=self.faiss_index)
        self.storage_context = StorageContext.from_defaults(vector_store=self.vector_store)
        if model_type == 'deepseek':
            self.llm = OpenAILike(
                api_base="https://api.deepseek.com/beta", 
                api_key=api_key,
                model="deepseek-chat",
            )
            os.environ["OPENAI_API_KEY"] = api_key
            os.environ["OPENAI_BASE_URL"] = "https://api.deepseek.com"

            Settings.llm = self.llm   
        elif model_type == 'ipex_llm':
            from llama_index.llms.ipex_llm import IpexLLM
            self.llm = IpexLLM.from_model_id_low_bit(
                model_name="models/qwen2chat_int4",
                tokenizer_name="models/qwen2chat_int4",
                context_window=4096,
                max_new_tokens=2048,
                generate_kwargs={"temperature": 0.0, "do_sample": False},
                completion_to_prompt=self.completion_to_prompt,
                messages_to_prompt=self.messages_to_prompt,
                device_map="cpu",
            )
            Settings.llm = self.llm   

    def download_embedding_model(self):
        """
        Download the embedding model if it does not exist.
        """
        print(f"Downloading embedding model: {self.embed_model_name}")
        snapshot_download("AI-ModelScope/bge-small-zh-v1.5", cache_dir='models', revision='master')
        print(f"Embedding model downloaded and saved to: {self.embed_model_name}")
    # def split_pdf(self, file_stream: BytesIO, max_length: int = 5000):
    #     reader = PyPDF2.PdfFileReader(file_stream)
    #     text_chunks = []
    #     for page_num in range(reader.numPages):
    #         page = reader.getPage(page_num)
    #         text = page.extract_text()
    #         text_chunks.extend([text[i:i+max_length] for i in range(0, len(text), max_length)])
    #     return text_chunks

    # def split_txt(self, file_stream: BytesIO, max_length: int = 5000):
    #     text = file_stream.read().decode('utf-8')
    #     text_chunks = [text[i:i+max_length] for i in range(0, len(text), max_length)]
    #     return text_chunks
    def completion_to_prompt(self, completion: str, **kwargs) -> str:
        """
        将完成转换为提示格式

        Args:
            completion (str): 完成的文本

        Returns:
            str: 格式化后的提示
        """
        return f"\n</s>\n\n{completion}</s>\n\n"




    def messages_to_prompt(self, messages: List[Dict[str, str]]) -> str:
        """
        将消息列表转换为提示格式

        Args:
            messages (List[Dict[str, str]]): 消息列表

        Returns:
            str: 格式化后的提示
        """
        prompt = ""
        for message in messages:
            if message['role'] == "system":
                prompt += f"\n{message['content']}</s>\n"
            elif message['role'] == "user":
                prompt += f"\n{message['content']}</s>\n"
            elif message['role'] == "assistant":
                prompt += f"\n{message['content']}</s>\n"

        if not prompt.startswith("\n"):
            prompt = "\n</s>\n" + prompt

        prompt = prompt + "\n"

        return prompt

    
    def build_index_from_file(self):
        documents = SimpleDirectoryReader("./data").load_data()
        index = VectorStoreIndex.from_documents(
            documents, storage_context=self.storage_context
        )
        index.storage_context.persist() # 保存到本地，这里暂时屏蔽
        self.index_db = index
        

    # 加载本地向量数据库
    def load_index(self):
        self.vector_store = FaissVectorStore.from_persist_dir(self.persist_dir)
        self.storage_context = StorageContext.from_defaults(
            vector_store=self.vector_store, persist_dir=self.persist_dir
        )
        return load_index_from_storage(storage_context=self.storage_context)

    # 检索内容
    def query_index(self, query: str):
        index_db = self.load_index()
        query_engine = index_db.as_query_engine()
        response = query_engine.query(query)
        return response
