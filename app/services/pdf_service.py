import os
import shutil
from fastapi import UploadFile
from sqlalchemy.orm import Session
from app.logic.pdf_processor import PDFProcessor
from app.services.embedding_service import embedding_service
import app.models.all_models as all_models

class PDFService:
    @staticmethod
    async def process_and_store_resume(file: UploadFile, db: Session):
        """Web 接口专用：处理上传、持久化并触发向量化"""
        # 1. 确保临时存储路径（供 Airflow 扫描或立即处理使用）
        upload_dir = "temp/incoming"
        os.makedirs(upload_dir, exist_ok=True)
        file_path = os.path.join(upload_dir, file.filename)
        
        # 保存文件
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        try:
            # 2. 调用逻辑层提取文本（不再在 Service 里写 fitz.open）
            extracted_text = PDFProcessor.extract_text(file_path)
        
            # 3. 存入数据库
            new_resume = all_models.Resume(
                filename=file.filename, 
                extracted_text=extracted_text
            )
            db.add(new_resume)
            db.commit()
            db.refresh(new_resume)
    
            # 4. 立即向量化（如果 Airflow 没开的话作为保底）
            embedding_service.chunk_and_embed(new_resume.id, extracted_text, db)
    
            return new_resume
            
        except Exception as e:
            db.rollback()
            print(f"❌ 处理简历失败: {e}")
            raise e
        # 注意：这里暂时不删 file_path，因为 Airflow 可能还要扫描它