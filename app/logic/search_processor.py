# app/logic/search_processor.py

from sqlalchemy.orm import Session
from app.services.embedding_service import embedding_service
from app.models.all_models import ResumeChunk

class SearchProcessor:
    @staticmethod
    def semantic_search(db: Session, query: str, top_k: int = 3):
        # 1. 向量化用户问题
        query_vector = embedding_service.get_embeddings([query])[0]
        
        # 2. 向量搜索 (使用 pgvector 的余弦距离)
        results = db.query(ResumeChunk).order_by(
            ResumeChunk.embedding.cosine_distance(query_vector)
        ).limit(top_k).all()
        
        return results