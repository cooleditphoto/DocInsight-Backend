from airflow import DAG
from airflow.operators.python import PythonVirtualenvOperator # 补上这个导入
from datetime import datetime, timedelta
import os

# 1. 实例化 DAG 对象
default_args = {
    'owner': 'airflow',
    'start_date': datetime(2025, 1, 1),
    'retries': 1,
}

dag = DAG(
    'resume_auto_vectorizer',
    default_args=default_args,
    schedule_interval='@hourly',
    catchup=False
)

# 2. 定义业务逻辑函数
def process_new_resumes():
    # 注意：Virtualenv 内部是全新的环境，必须在函数内重新 import
    import sys
    import os
    
    # 关键：手动加入代码搜索路径
    sys.path.append('/opt/airflow/app_code')
    
    # 因为 requirements 里已经装好了，这里直接 import 即可
    from app.logic.pdf_processor import PDFProcessor
    from app.core.database import SessionLocal
    from app.services.embedding_service import embedding_service
    import app.models.all_models as all_models
    
    print("✅ 虚拟环境隔离启动成功，正在扫描...")
    
    db = SessionLocal()
    scan_dir = "/opt/airflow/data/incoming" 
    
    if not os.path.exists(scan_dir):
        os.makedirs(scan_dir, exist_ok=True)

    for filename in os.listdir(scan_dir):
        if filename.endswith(".pdf"):
            file_path = os.path.join(scan_dir, filename)
            print(f"🔍 发现文件: {filename}")
            
            extracted_text = PDFProcessor.extract_text(file_path)
            
            existing = db.query(all_models.Resume).filter(all_models.Resume.filename == filename).first()
            if not existing:
                new_resume = all_models.Resume(filename=filename, extracted_text=extracted_text)
                db.add(new_resume)
                db.commit()
                db.refresh(new_resume)
                
                embedding_service.chunk_and_embed(new_resume.id, extracted_text, db)
                print(f"✅ {filename} 向量化处理完成")
            else:
                print(f"⏩ {filename} 跳过")
    db.close()

# 3. 任务定义
process_task = PythonVirtualenvOperator(
    task_id='run_pdf_processing',
    python_callable=process_new_resumes,
    requirements=[
        "pydantic>=2.10.0", 
        "pydantic-settings",
        "langchain-text-splitters",
        "pymupdf",
        "openai",
        "pgvector",
        "sqlalchemy",
        "psycopg2-binary" 
    ],
    system_site_packages=False, 
    dag=dag,
)