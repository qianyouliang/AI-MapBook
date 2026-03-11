"""
文件处理模块
AI-MapBook 支持多种文件格式
"""
import os
import re
from html.parser import HTMLParser
from io import BytesIO
from typing import List, Optional
import PyPDF2

# 尝试导入可选依赖
try:
    import docx
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False

try:
    import ebooklib
    from ebooklib import epub
    EPUB_AVAILABLE = True
except ImportError:
    EPUB_AVAILABLE = False

try:
    import mobi
    MOBI_AVAILABLE = True
except ImportError:
    MOBI_AVAILABLE = False


class _HtmlToText(HTMLParser):
    """从 HTML 内容提取纯文本"""
    def __init__(self):
        super().__init__()
        self.parts = []

    def handle_data(self, data: str) -> None:
        self.parts.append(data)

    def get_text(self) -> str:
        return "".join(self.parts)


class FileProcessor:
    """文件处理器 - 支持多种格式"""
    
    def __init__(self):
        self.supported_formats = {
            "pdf": self.extract_text_from_pdf,
            "txt": self.extract_text_from_txt,
            "docx": self.extract_text_from_docx,
            "doc": self.extract_text_from_docx,
            "epub": self.extract_text_from_epub,
            "mobi": self.extract_text_from_mobi,
            "md": self.extract_text_from_txt,  # Markdown 当作纯文本
        }
    
    def is_supported(self, filename: str) -> bool:
        """检查文件格式是否支持"""
        ext = filename.split('.')[-1].lower()
        return ext in self.supported_formats
    
    def get_supported_formats(self) -> List[str]:
        """获取支持的格式列表"""
        return list(self.supported_formats.keys())
    
    def get_missing_dependencies(self, filename: str) -> List[str]:
        """获取缺失的依赖"""
        ext = filename.split('.')[-1].lower()
        missing = []
        
        if ext in ["docx", "doc"] and not DOCX_AVAILABLE:
            missing.append("python-docx")
        elif ext == "epub" and not EPUB_AVAILABLE:
            missing.append("EbookLib")
        elif ext == "mobi" and not MOBI_AVAILABLE:
            missing.append("mobi")
        
        return missing
    
    def extract_text(self, file, filename: str) -> List[str]:
        """
        统一的文本提取接口
        
        Args:
            file: 文件对象
            filename: 文件名
        
        Returns:
            文本列表
        """
        ext = filename.split('.')[-1].lower()
        
        if ext not in self.supported_formats:
            raise ValueError(f"不支持的文件格式: {ext}，支持的格式: {', '.join(self.get_supported_formats())}")
        
        # 检查依赖
        missing = self.get_missing_dependencies(filename)
        if missing:
            raise ImportError(f"解析 {ext} 文件需要安装: {' '.join(missing)}")
        
        return self.supported_formats[ext](file)
    
    def extract_text_from_pdf(self, file) -> List[str]:
        """从 PDF 提取文本"""
        if isinstance(file, bytes):
            file = BytesIO(file)
        
        pdf_reader = PyPDF2.PdfReader(file)
        text_pages = []
        
        for page_num in range(len(pdf_reader.pages)):
            page = pdf_reader.pages[page_num]
            page_text = page.extract_text()
            if page_text:
                text_pages.append(page_text)
        
        return text_pages
    
    def extract_text_from_txt(self, file) -> List[str]:
        """从纯文本提取"""
        if isinstance(file, bytes):
            text = file.decode("utf-8")
        else:
            text = file.read().decode("utf-8")
        
        # 分块处理
        chunk_size = 5000
        return [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]
    
    def extract_text_from_docx(self, file) -> List[str]:
        """从 Word 文档提取文本"""
        if not DOCX_AVAILABLE:
            raise ImportError("需要安装 python-docx: pip install python-docx")
        
        if isinstance(file, bytes):
            file = BytesIO(file)
        
        doc = docx.Document(file)
        paragraphs = [para.text for para in doc.paragraphs if para.text.strip()]
        
        # 合并所有段落
        full_text = "\n".join(paragraphs)
        
        # 分块
        chunk_size = 5000
        return [full_text[i:i+chunk_size] for i in range(0, len(full_text), chunk_size)]
    
    def extract_text_from_epub(self, file) -> List[str]:
        """从 EPUB 提取文本（使用 EbookLib）"""
        if not EPUB_AVAILABLE:
            raise ImportError("需要安装 EbookLib: pip install EbookLib")

        if isinstance(file, bytes):
            import tempfile
            with tempfile.NamedTemporaryFile(suffix='.epub', delete=False) as tmp:
                tmp.write(file)
                tmp_path = tmp.name
            try:
                book = epub.read_epub(tmp_path)
            finally:
                os.unlink(tmp_path)
        else:
            book = epub.read_epub(file)

        parser = _HtmlToText()
        texts = []
        for item in book.get_items():
            if item.get_type() == ebooklib.ITEM_DOCUMENT:
                content = item.get_content()
                if content:
                    try:
                        html_str = content.decode("utf-8", errors="replace")
                    except Exception:
                        html_str = content.decode("latin-1", errors="replace")
                    parser.parts = []
                    parser.feed(html_str)
                    text = parser.get_text().strip()
                    if text:
                        texts.append(text)

        full_text = "\n".join(texts)
        chunk_size = 5000
        return [full_text[i:i+chunk_size] for i in range(0, len(full_text), chunk_size)]
    
    def extract_text_from_mobi(self, file) -> List[str]:
        """从 MOBI 提取文本"""
        if not MOBI_AVAILABLE:
            raise ImportError("需要安装 mobi: pip install mobi")
        
        if isinstance(file, bytes):
            book = mobi.Mobi(file)
        else:
            book = mobi.Mobi(file.read())
        
        # 提取内容
        text = book.read()
        
        # 分块
        chunk_size = 5000
        return [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]


def get_processor() -> FileProcessor:
    """获取文件处理器实例"""
    return FileProcessor()
