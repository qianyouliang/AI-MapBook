"""
RAG 模块
AI-MapBook - 使用开源 Embedding + DeepSeek
"""
import os
from typing import List, Dict, Optional
from pathlib import Path
import tempfile

# 可选依赖
try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False

try:
    import faiss
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False

from dotenv import load_dotenv

load_dotenv()


class RAGModel:
    """RAG 模型"""
    
    def __init__(self, api_key: str = None, model_type: str = "deepseek"):
        """
        初始化 RAG 模型
        
        Args:
            api_key: API 密钥
            model_type: 模型类型
        """
        self.api_key = api_key or os.getenv("DEEPSEEK_API_KEY", "")
        self.model_type = model_type
        self.embedding_model = None
        self.index = None
        self.chunks = []
        self.metadata = []
        
        # 初始化 embedding 模型
        self._init_embedding()
    
    def _init_embedding(self):
        """初始化 embedding 模型"""
        if not SENTENCE_TRANSFORMERS_AVAILABLE:
            print("Warning: sentence-transformers not installed")
            return
        
        # 使用开源 embedding 模型
        model_name = "BAAI/bge-small-zh-v1.5"
        try:
            self.embedding_model = SentenceTransformer(model_name)
            print(f"Loaded embedding model: {model_name}")
        except Exception as e:
            print(f"Failed to load embedding model: {e}")
    
    def build_index_from_file(self, file_path: str = None, chunk_size: int = 512):
        """
        从文件构建索引
        
        Args:
            file_path: 文件路径
            chunk_size: 块大小
        """
        if not file_path:
            # 使用默认数据目录
            data_dir = Path(__file__).parent.parent / "data"
            txt_files = list(data_dir.glob("*.txt"))
            if txt_files:
                file_path = str(txt_files[0])
        
        if not file_path or not os.path.exists(file_path):
            print("No file found for RAG")
            return
        
        # 读取文件
        with open(file_path, 'r', encoding='utf-8') as f:
            text = f.read()
        
        # 分块
        self.chunks = self._chunk_text(text, chunk_size)
        
        # 生成 embeddings
        if self.embedding_model and self.chunks:
            embeddings = self.embedding_model.encode(self.chunks)
            
            # 构建 FAISS 索引
            if FAISS_AVAILABLE and NUMPY_AVAILABLE:
                dimension = embeddings.shape[1]
                self.index = faiss.IndexFlatL2(dimension)
                self.index.add(embeddings)
                
                print(f"Built index with {len(self.chunks)} chunks")
    
    def _chunk_text(self, text: str, chunk_size: int) -> List[str]:
        """将文本分块"""
        # 简单按句子分块
        import re
        sentences = re.split(r'[。！？\n]', text)
        
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            
            if len(current_chunk) + len(sentence) <= chunk_size:
                current_chunk += sentence + "。"
            else:
                if current_chunk:
                    chunks.append(current_chunk)
                current_chunk = sentence + "。"
        
        if current_chunk:
            chunks.append(current_chunk)
        
        return chunks
    
    def query_index(self, query: str, top_k: int = 3) -> str:
        """
        查询索引
        
        Args:
            query: 查询文本
            top_k: 返回结果数量
        
        Returns:
            相关文本
        """
        if not self.index or not self.embedding_model:
            return ""
        
        # 生成 query embedding
        query_embedding = self.embedding_model.encode([query])
        
        # 搜索
        distances, indices = self.index.search(query_embedding, top_k)
        
        # 返回相关文本
        results = []
        for idx in indices[0]:
            if idx < len(self.chunks):
                results.append(self.chunks[idx])
        
        return "\n".join(results)


def create_rag(api_key: str = None) -> RAGModel:
    """创建 RAG 模型"""
    return RAGModel(api_key=api_key)
