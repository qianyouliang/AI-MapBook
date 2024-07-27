import torch
from modelscope import snapshot_download, AutoModel, AutoTokenizer
import os
from ipex_llm.transformers import AutoModelForCausalLM
from transformers import  AutoTokenizer

if __name__ == '__main__':
    # 第一个参数表示下载模型的型号，第二个参数是下载后存放的缓存地址，第三个表示版本号，默认 master 配置llm
    model_dir = snapshot_download('Qwen/Qwen2-7B', cache_dir='models', revision='master')
    model_path = os.path.join(os.getcwd(),"models/Qwen/Qwen2-7B")
    model = AutoModelForCausalLM.from_pretrained(model_path, load_in_low_bit='sym_int4', trust_remote_code=True)
    tokenizer = AutoTokenizer.from_pretrained(model_path, trust_remote_code=True)
    model.save_low_bit('qwen2chat_int4')
    tokenizer.save_pretrained('qwen2chat_int4')
    # 配置embedding模型
    embedding_model_dir = snapshot_download('AI-ModelScope/bge-small-zh-v1.5', cache_dir='models', revision='master')