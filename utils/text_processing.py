import PyPDF2
from io import BytesIO

class FileProcessor:
    def __init__(self):
        pass

    def extract_text_from_pdf(self, file):
        pdf_reader = PyPDF2.PdfReader(file)
        text_pages = []

        for page_num in range(len(pdf_reader.pages)):
            page = pdf_reader.pages[page_num]
            page_text = page.extract_text()
            text_pages.append(page_text)

        return text_pages

    def extract_text_from_txt(self, file):
        text = file.read().decode("utf-8")
        chunk_size = 5000
        return [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]