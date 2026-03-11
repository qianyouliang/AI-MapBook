"""
日志管理模块
AI-MapBook 统一日志记录
"""
import logging
import os
from datetime import datetime
from pathlib import Path


def setup_logger(
    name: str = "AI-MapBook",
    log_level: int = logging.INFO,
    log_file: str = None,
    format_string: str = None
) -> logging.Logger:
    """
    设置日志记录器
    
    Args:
        name: 日志记录器名称
        log_level: 日志级别
        log_file: 日志文件路径（可选）
        format_string: 日志格式字符串（可选）
    
    Returns:
        配置好的 Logger 实例
    """
    logger = logging.getLogger(name)
    logger.setLevel(log_level)
    
    # 避免重复添加 handler
    if logger.handlers:
        return logger
    
    # 默认格式
    if format_string is None:
        format_string = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
    
    formatter = logging.Formatter(format_string, datefmt="%Y-%m-%d %H:%M:%S")
    
    # 控制台输出
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # 文件输出
    if log_file:
        log_dir = os.path.dirname(log_file)
        if log_dir:
            os.makedirs(log_dir, exist_ok=True)
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    else:
        # 默认日志文件
        log_dir = Path(__file__).parent.parent / "logs"
        log_dir.mkdir(exist_ok=True)
        default_log_file = log_dir / f"app_{datetime.now().strftime('%Y%m%d')}.log"
        file_handler = logging.FileHandler(default_log_file, encoding="utf-8")
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger


# 默认日志记录器
logger = setup_logger()


class LogMixin:
    """日志混入类，为其他类提供日志功能"""
    
    @property
    def logger(self) -> logging.Logger:
        """获取日志记录器"""
        name = f"AI-MapBook.{self.__class__.__name__}"
        return logging.getLogger(name)


def log_exception(logger: logging.Logger, e: Exception, context: str = ""):
    """
    记录异常信息
    
    Args:
        logger: 日志记录器
        e: 异常对象
        context: 上下文信息
    """
    import traceback
    msg = f"{context}: {type(e).__name__}: {str(e)}" if context else f"{type(e).__name__}: {str(e)}"
    logger.error(msg)
    logger.debug(traceback.format_exc())


def log_function_call(logger: logging.Logger, func_name: str, *args, **kwargs):
    """
    记录函数调用
    
    Args:
        logger: 日志记录器
        func_name: 函数名
        *args: 位置参数
        **kwargs: 关键字参数
    """
    args_str = ", ".join([repr(a) for a in args])
    kwargs_str = ", ".join([f"{k}={repr(v)}" for k, v in kwargs.items()])
    params = ", ".join(filter(None, [args_str, kwargs_str]))
    logger.debug(f"Calling {func_name}({params})")
