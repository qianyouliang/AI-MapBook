# 设置OpenMP线程数为8
import os
import time
os.environ["OMP_NUM_THREADS"] = "8"

import torch
from typing import Any, List, Optional


# 从llama_index库导入HuggingFaceEmbedding类，用于将文本转换为向量表示
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
# 从llama_index库导入ChromaVectorStore类，用于高效存储和检索向量数据
from llama_index.vector_stores.chroma import ChromaVectorStore
# 从llama_index库导入PyMuPDFReader类，用于读取和解析PDF文件内容
from llama_index.readers.file import PyMuPDFReader
# 从llama_index库导入NodeWithScore和TextNode类
# NodeWithScore: 表示带有相关性分数的节点，用于排序检索结果
# TextNode: 表示文本块，是索引和检索的基本单位。节点存储文本内容及其元数据，便于构建知识图谱和语义搜索
from llama_index.core.schema import NodeWithScore, TextNode
# 从llama_index库导入RetrieverQueryEngine类，用于协调检索器和响应生成，执行端到端的问答过程
from llama_index.core.query_engine import RetrieverQueryEngine
# 从llama_index库导入QueryBundle类，用于封装查询相关的信息，如查询文本、过滤器等
from llama_index.core import QueryBundle
# 从llama_index库导入BaseRetriever类，这是所有检索器的基类，定义了检索接口
from llama_index.core.retrievers import BaseRetriever
# 从llama_index库导入SentenceSplitter类，用于将长文本分割成句子或语义完整的文本块，便于索引和检索
from llama_index.core.node_parser import SentenceSplitter
# 从llama_index库导入VectorStoreQuery类，用于构造向量存储的查询，支持语义相似度搜索
from llama_index.core.vector_stores import VectorStoreQuery
# 向量数据库
import chromadb
from ipex_llm.llamaindex.llms import IpexLLM

class Config:
    """配置类,存储所有需要的参数"""
    model_path = "qwen2chat_int4"
    tokenizer_path = "qwen2chat_int4"
    question = "How does Llama 2 perform compared to other open-source models?"
    data_path = "./data/llamatiny.pdf"
    persist_dir = "./chroma_db"
    embedding_model_path = "qwen2chat_src/AI-ModelScope/bge-small-zh-v1___5"
    max_new_tokens = 64

def load_vector_database(persist_dir: str) -> ChromaVectorStore:
    """
    加载或创建向量数据库
    
    Args:
        persist_dir (str): 持久化目录路径
    
    Returns:
        ChromaVectorStore: 向量存储对象
    """
    # 检查持久化目录是否存在
    if os.path.exists(persist_dir):
        print(f"正在加载现有的向量数据库: {persist_dir}")
        chroma_client = chromadb.PersistentClient(path=persist_dir)
        chroma_collection = chroma_client.get_collection("llama2_paper")
    else:
        print(f"创建新的向量数据库: {persist_dir}")
        chroma_client = chromadb.PersistentClient(path=persist_dir)
        chroma_collection = chroma_client.create_collection("llama2_paper")
    print(f"Vector store loaded with {chroma_collection.count()} documents")
    return ChromaVectorStore(chroma_collection=chroma_collection)

def load_data(data_path: str) -> List[TextNode]:
    """
    加载并处理PDF数据
    
    Args:
        data_path (str): PDF文件路径
    
    Returns:
        List[TextNode]: 处理后的文本节点列表
    """
    loader = PyMuPDFReader()
    documents = loader.load(file_path=data_path)

    text_parser = SentenceSplitter(chunk_size=384)
    text_chunks = []
    doc_idxs = []
    for doc_idx, doc in enumerate(documents):
        cur_text_chunks = text_parser.split_text(doc.text)
        text_chunks.extend(cur_text_chunks)
        doc_idxs.extend([doc_idx] * len(cur_text_chunks))

    nodes = []
    for idx, text_chunk in enumerate(text_chunks):
        node = TextNode(text=text_chunk)
        src_doc = documents[doc_idxs[idx]]
        node.metadata = src_doc.metadata
        nodes.append(node)
    return nodes

class VectorDBRetriever(BaseRetriever):
    """向量数据库检索器"""

    def __init__(
        self,
        vector_store: ChromaVectorStore,
        embed_model: Any,
        query_mode: str = "default",
        similarity_top_k: int = 2,
    ) -> None:
        self._vector_store = vector_store
        self._embed_model = embed_model
        self._query_mode = query_mode
        self._similarity_top_k = similarity_top_k
        super().__init__()

    def _retrieve(self, query_bundle: QueryBundle) -> List[NodeWithScore]:
        """
        检索相关文档
        
        Args:
            query_bundle (QueryBundle): 查询包
        
        Returns:
            List[NodeWithScore]: 检索到的文档节点及其相关性得分
        """
        query_embedding = self._embed_model.get_query_embedding(
            query_bundle.query_str
        )
        vector_store_query = VectorStoreQuery(
            query_embedding=query_embedding,
            similarity_top_k=self._similarity_top_k,
            mode=self._query_mode,
        )
        query_result = self._vector_store.query(vector_store_query)

        nodes_with_scores = []
        for index, node in enumerate(query_result.nodes):
            score: Optional[float] = None
            if query_result.similarities is not None:
                score = query_result.similarities[index]
            nodes_with_scores.append(NodeWithScore(node=node, score=score))
        print(f"Retrieved {len(nodes_with_scores)} nodes with scores")
        return nodes_with_scores

def completion_to_prompt(completion: str) -> str:
    """
    将完成转换为提示格式
    
    Args:
        completion (str): 完成的文本
    
    Returns:
        str: 格式化后的提示
    """
    return f"<|system|>\n</s>\n<|user|>\n{completion}</s>\n<|assistant|>\n"

def messages_to_prompt(messages: List[dict]) -> str:
    """
    将消息列表转换为提示格式
    
    Args:
        messages (List[dict]): 消息列表
    
    Returns:
        str: 格式化后的提示
    """
    prompt = ""
    for message in messages:
        if message.role == "system":
            prompt += f"<|system|>\n{message.content}</s>\n"
        elif message.role == "user":
            prompt += f"<|user|>\n{message.content}</s>\n"
        elif message.role == "assistant":
            prompt += f"<|assistant|>\n{message.content}</s>\n"

    if not prompt.startswith("<|system|>\n"):
        prompt = "<|system|>\n</s>\n" + prompt

    prompt = prompt + "<|assistant|>\n"

    return prompt

def setup_llm(config: Config) -> IpexLLM:
    """
    设置语言模型
    
    Args:
        config (Config): 配置对象
    
    Returns:
        IpexLLM: 配置好的语言模型
    """
    return IpexLLM.from_model_id_low_bit(
        model_name=config.model_path,
        tokenizer_name=config.tokenizer_path,
        context_window=384,
        max_new_tokens=config.max_new_tokens,
        generate_kwargs={"temperature": 0.7, "do_sample": False},
        model_kwargs={},
        messages_to_prompt=messages_to_prompt,
        completion_to_prompt=completion_to_prompt,
        device_map="cpu",
    )
def main():
    """主函数"""
    config = Config()
    
    # 设置嵌入模型
    embed_model = HuggingFaceEmbedding(model_name=config.embedding_model_path)
    
    # 设置语言模型
    llm = setup_llm(config)
    
    # 加载向量数据库
    vector_store = load_vector_database(persist_dir=config.persist_dir)
    
    # 加载和处理数据
    nodes = load_data(data_path=config.data_path)
    for node in nodes:
        node_embedding = embed_model.get_text_embedding(
            node.get_content(metadata_mode="all")
        )
        node.embedding = node_embedding
    
    # 将 node 添加到向量存储
    vector_store.add(nodes)
    
    # 设置查询
    query_str = config.question
    query_embedding = embed_model.get_query_embedding(query_str)
    
    # 执行向量存储检索
    print("开始执行向量存储检索")
    query_mode = "default"
    vector_store_query = VectorStoreQuery(
        query_embedding=query_embedding, similarity_top_k=2, mode=query_mode
    )
    query_result = vector_store.query(vector_store_query)

    # 处理查询结果
    print("开始处理检索结果")
    nodes_with_scores = []
    for index, node in enumerate(query_result.nodes):
        score: Optional[float] = None
        if query_result.similarities is not None:
            score = query_result.similarities[index]
        nodes_with_scores.append(NodeWithScore(node=node, score=score))
    
    # 设置检索器
    retriever = VectorDBRetriever(
        vector_store, embed_model, query_mode="default", similarity_top_k=1
    )
    
    print(f"Query engine created with retriever: {type(retriever).__name__}")
    print(f"Query string length: {len(query_str)}")
    print(f"Query string: {query_str}")
    
    # 创建查询引擎
    print("准备与llm对话")
    query_engine = RetrieverQueryEngine.from_args(retriever, llm=llm)

    # 执行查询
    print("开始RAG最后生成")
    start_time = time.time()
    response = query_engine.query(query_str)

    # 打印结果
    print("------------RESPONSE GENERATION---------------------")
    print(str(response))
    print(f"inference time: {time.time()-start_time}")

if __name__ == "__main__":
    main()
