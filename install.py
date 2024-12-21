import os
import warnings
from contextlib import contextmanager
import torch
from modelscope import snapshot_download
from transformers import AutoModelForCausalLM, AutoTokenizer
import psutil
import logging
import gc

@contextmanager
def suppress_pytorch_warnings():
    with warnings.catch_warnings():
        warnings.filterwarnings('ignore', message='Initializing zero-element tensors is a no-op')
        warnings.filterwarnings('ignore', message='NumExpr detected.*')
        yield

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def check_system_resources():
    # 检查可用内存
    memory = psutil.virtual_memory()
    logger.info(f"系统内存使用情况:")
    logger.info(f"总内存: {memory.total / (1024**3):.2f} GB")
    logger.info(f"可用内存: {memory.available / (1024**3):.2f} GB")
    logger.info(f"内存使用率: {memory.percent}%")
    
    # 检查磁盘空间
    disk = psutil.disk_usage('.')
    logger.info(f"磁盘空间使用情况:")
    logger.info(f"总空间: {disk.total / (1024**3):.2f} GB")
    logger.info(f"可用空间: {disk.free / (1024**3):.2f} GB")
    logger.info(f"磁盘使用率: {disk.percent}%")

if __name__ == '__main__':
    try:
        # 检查系统资源
        logger.info("检查系统资源...")
        check_system_resources()

        # 清理GPU内存（如果使用GPU）
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        gc.collect()

        # 下载模型到本地
        logger.info("开始下载模型...")
        model_dir = snapshot_download('Qwen/Qwen2.5-3B-Instruct', cache_dir='models', revision='master')
        logger.info(f"模型下载完成，保存在: {model_dir}")
        
        # 下载embedding模型
        logger.info("开始下载embedding模型...")
        embedding_model_dir = snapshot_download('AI-ModelScope/bge-small-zh-v1.5', cache_dir='models', revision='master')
        logger.info(f"embedding模型下载完成，保存在: {embedding_model_dir}")
        
        # 测试模型加载
        logger.info("测试模型加载...")
        test_prompt = "你好，请做个自我介绍。"
        
        logger.info("加载模型和tokenizer...")
        model = AutoModelForCausalLM.from_pretrained(
            model_dir,
            torch_dtype="auto",
            device_map="auto",
            trust_remote_code=True
        )
        tokenizer = AutoTokenizer.from_pretrained(model_dir, trust_remote_code=True)
        
        messages = [
            {"role": "system", "content": "You are Qwen, created by Alibaba Cloud."},
            {"role": "user", "content": test_prompt}
        ]
        
        text = tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True
        )
        model_inputs = tokenizer([text], return_tensors="pt").to(model.device)
        
        logger.info("生成测试回答...")
        generated_ids = model.generate(
            **model_inputs,
            max_new_tokens=128
        )
        response = tokenizer.decode(generated_ids[0], skip_special_tokens=True)
        logger.info("测试回答：\n" + response)
        
    except Exception as e:
        logger.error(f"发生错误: {str(e)}", exc_info=True)
    finally:
        # 清理内存
        if 'model' in locals():
            del model
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        gc.collect()
        logger.info("程序执行完成，已清理内存")
