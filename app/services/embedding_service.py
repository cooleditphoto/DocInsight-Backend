import openai
from app.core.config import settings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from app.models import all_models # 确保导入了模型

class EmbeddingService:
    def __init__(self):
        self.client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
        # 设置分块器：每块 500 字，重叠 50 字防止语境断裂
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=50
        )

    def get_vector(self, text: str):
        """调用 OpenAI 获取向量"""
        response = self.client.embeddings.create(
            model="text-embedding-3-small",
            input=text
        )
        return response.data[0].embedding

    def chunk_and_embed(self, resume_id: str, full_text: str, db):
        """核心逻辑：切分 -> 向量化 -> 存入 pgvector"""
        chunks = self.text_splitter.split_text(full_text)
        
        for chunk_text in chunks:
            vector = self.get_vector(chunk_text)
            new_chunk = all_models.ResumeChunk(
                resume_id=resume_id,
                content=chunk_text,
                embedding=vector
            )
            db.add(new_chunk)
        db.commit()

embedding_service = EmbeddingService()