"""
RAG 模块
AI-MapBook 检索增强生成
"""
import os
import re
from typing import List
from pathlib import Path

try:
    from sentence_transformers import SentenceTransformer
    from sentence_transformers import __version__ as st_version
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False

try:
    import faiss
    import numpy as np
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False


class RAGModel:
    """RAG 检索模型"""
    
    def __init__(self):
        self.embedding_model = None
        self.index = None
        self.chunks = []
        
        if SENTENCE_TRANSFORMERS_AVAILABLE:
            try:
                self.embedding_model = SentenceTransformer("BAAI/bge-small-zh-v1.5")
            except Exception as e:
                print(f"加载 embedding 模型失败: {e}")
    
    def build_index(self, text: str, chunk_size: int = 512):
        """构建索引"""
        if not self.embedding_model:
            return
        
        self.chunks = self._chunk_text(text, chunk_size)
        
        if self.chunks and FAISS_AVAILABLE:
            embeddings = self.embedding_model.encode(self.chunks)
            dimension = embeddings.shape[1]
            self.index = faiss.IndexFlatL2(dimension)
            self.index.add(embeddings)
    
    def query(self, query: str, top_k: int = 3) -> str:
        """查询"""
        if not self.index or not self.embedding_model:
            return ""
        
        query_embedding = self.embedding_model.encode([query])
        _, indices = self.index.search(query_embedding, top_k)
        
        results = [self.chunks[i] for i in indices[0] if i < len(self.chunks)]
        return "\n".join(results)
    
    @staticmethod
    def _chunk_text(text: str, chunk_size: int) -> List[str]:
        sentences = re.split(r'[。！？\n]', text)
        chunks = []
        current = ""
        
        for s in sentences:
            s = s.strip()
            if not s:
                continue
            if len(current) + len(s) <= chunk_size:
                current += s + "。"
            else:
                if current:
                    chunks.append(current)
                current = s + "。"
        
        if current:
            chunks.append(current)
        
        return chunks
