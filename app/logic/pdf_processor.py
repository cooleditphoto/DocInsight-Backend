import fitz  # PyMuPDF
from langchain_text_splitters import RecursiveCharacterTextSplitter

class PDFProcessor:
    @staticmethod
    def extract_text(file_path: str) -> str:
        """纯逻辑：从路径读取并提取文本"""
        text = ""
        try:
            with fitz.open(file_path) as doc:
                for page in doc:
                    text += page.get_text()
            return text
        except Exception as e:
            return f"Error: {str(e)}"

    @staticmethod
    def split_text(text: str):
        """纯逻辑：切分文本块"""
        splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
        return splitter.split_text(text)