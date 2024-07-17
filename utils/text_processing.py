import PyPDF2
from io import BytesIO
from utils.ModelBack import LLM

class FileProcessor:
    def __init__(self):
        self.llm = LLM()  # 假设LLM类已经定义并可以初始化

    def extract_text_from_pdf(self, file):
        pdf_reader = PyPDF2.PdfReader(file)
        text = ""
        for page_num in range(len(pdf_reader.pages)):
            page = pdf_reader.pages[page_num] 
            text += page.extract_text()
        return text

    def extract_text_from_txt(self, file):
        return file.read().decode("utf-8")

    def process_text(self, text):
        # 调用LLM类的run方法，返回一个包含地理信息的列表
        geo_info_list = self.llm.run(text, language='中文')
        return geo_info_list
