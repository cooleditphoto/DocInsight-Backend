import sys
import os
# 确保脚本能找到 app 目录
sys.path.append(os.getcwd())

from sqlalchemy.orm import Session
from app.core.database import SessionLocal, engine
from app.models import all_models
from app.services.embedding_service import embedding_service

# 1. 确保表已创建
all_models.Base.metadata.create_all(bind=engine)

def test_chunk_and_embed():
    db = SessionLocal()
    try:
        # 模拟一份简单的简历文本
        test_resume_text = """
        Muzi Qiu, Senior Full Stack Engineer. 
        Experienced in API modernization from SOAP to GraphQL.
        Skilled in Python, FastAPI, and PostgreSQL.
        Built a RAG system using pgvector and OpenAI.
        """
        
        # 先创建一个模拟简历记录，拿到 ID
        temp_resume = all_models.Resume(
            filename="test_resume.pdf",
            extracted_text=test_resume_text
        )
        db.add(temp_resume)
        db.commit()
        db.refresh(temp_resume)
        
        print(f"✅ 模拟简历已创建，ID: {temp_resume.id}")

        # 2. 调用我们之前写好的切片和向量化服务
        print("🚀 正在启动切片与向量化流水线...")
        embedding_service.chunk_and_embed(temp_resume.id, test_resume_text, db)
        
        # 3. 验证结果
        chunks = db.query(all_models.ResumeChunk).filter_by(resume_id=temp_resume.id).all()
        print(f"📊 成功生成了 {len(chunks)} 个片段。")
        
        for i, chunk in enumerate(chunks):
            # 打印向量的前 5 位，看看长什么样
            vector_preview = chunk.embedding[:5]
            print(f"   片段 {i+1} 预览: {chunk.content[:30]}...")
            print(f"   向量预览 (前5维): {vector_preview}")

    except Exception as e:
        print(f"❌ 出错了: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    test_chunk_and_embed()