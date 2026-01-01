from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Query
from langchain_community.vectorstores import PGVector
from langchain_openai import OpenAIEmbeddings
from sqlalchemy.orm import Session
from aiokafka import AIOKafkaProducer
import json

from app.core.database import get_db
from app.services.storage_service import StorageService
from app.services.pdf_service import PDFService
from app.services.llm_service import LLMService
from app.models import all_models
from app.logic.search_processor import SearchProcessor
import uuid
import os

router = APIRouter(prefix="/resumes", tags=["resumes"])
storage_service = StorageService()
llm_service = LLMService() 

# 配置 Redpanda 地址 (容器名:端口)
KAFKA_BOOTSTRAP_SERVERS = "redpanda:9092"

@router.post("/upload")
async def upload_resume(file: UploadFile = File(...), db: Session = Depends(get_db)):
    # 1. 存文件（只做这一件事，确保秒回）
    resume_id = str(uuid.uuid4())
    file_path = f"/app/app/data/{file.filename}" 
    with open(file_path, "wb") as f:
        f.write(await file.read())

    # 2. 【新增】在数据库中创建记录，状态设为 'processing'
    new_resume = all_models.Resume(
        id=resume_id,
        filename=file.filename,
        file_path=file_path,
        status="processing" 
    )
    db.add(new_resume)
    db.commit() # 必须 commit，否则 start 接口查不到

    # 2. 发消息给 Redpanda（告诉 Worker：活儿来了）
    producer = AIOKafkaProducer(bootstrap_servers='redpanda:9092')
    await producer.start()
    try:
        task = {"resume_id": resume_id, "file_path": file_path}
        await producer.send_and_wait("resume_tasks", json.dumps(task).encode('utf-8'))
    finally:
        await producer.stop()

    return {"status": "Processing in background", "resume_id": resume_id}

@router.post("/interview")
async def start_mock_interview(
    resume_text: str, 
    service: LLMService = Depends(LLMService) # 自动实例化
):
    question = service.generate_interview_question(resume_text)
    return {"question": question}


@router.post("/interview/start/{resume_id}")
async def start_interview(resume_id: str, db: Session = Depends(get_db)):
    # 1. 检查简历是否存在
    resume = db.query(all_models.Resume).filter(all_models.Resume.id == resume_id).first()
    if not resume:
        return {"error": "Resume not found"}

    # 2. 创建面试会话
    new_session = all_models.InterviewSession(resume_id=resume_id)
    db.add(new_session)
    db.commit()
    db.refresh(new_session)

    # 3. 让 AI 生成第一个问题
    first_question = llm_service.generate_first_question(resume.extracted_text)
    
    # 4. 把 AI 的第一个问题存入消息记录
    new_msg = all_models.InterviewMessage(
        session_id=new_session.id,
        role="assistant",
        content=first_question
    )
    db.add(new_msg)
    db.commit()

    return {
        "session_id": new_session.id,
        "first_question": first_question
    }
    
# 初始化 Embedding（必须和 Worker 里的模型一致）
embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
# 转换连接串格式 (PGVector 需要 postgresql:// 而非 postgresql+psycopg2://)
CONNECTION_STRING = os.getenv("DATABASE_URL").replace("+psycopg2", "")

@router.post("/interview/chat")
async def chat_interview(session_id: str, user_answer: str, db: Session = Depends(get_db)):
    # 1. 获取 Session 信息
    session = db.query(all_models.InterviewSession).filter(
        all_models.InterviewSession.id == session_id
    ).first()
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # 2. 【核心 RAG 步骤】去向量库检索与当前回答最相关的简历片段
    vector_store = PGVector(
        connection_string=CONNECTION_STRING,
        embedding_function=embeddings,
        collection_name="resumes_collection"
    )
    
    # 仅检索属于该简历的片段 (利用 Worker 存入的 metadata)
    docs = vector_store.similarity_search(
        user_answer, 
        k=3, 
        filter={"resume_id": session.resume_id}
    )
    context_text = "\n".join([doc.page_content for doc in docs])

    # 3. 获取历史记录（保持不变）
    history_records = db.query(all_models.InterviewMessage).filter(
        all_models.InterviewMessage.session_id == session_id
    ).order_by(all_models.InterviewMessage.created_at.asc()).all()
    chat_history = [{"role": msg.role, "content": msg.content} for msg in history_records]

    # 4. 调用 RAG 版 LLM 服务
    ai_response = llm_service.get_rag_chat_response(
        context=context_text,
        user_answer=user_answer,
        chat_history=chat_history
    )

    # 5. 存储对话记录并返回（保持不变）
    # ... db.add(user_msg), db.add(ai_msg) ...
    return {"ai_response": ai_response}

@router.get("/search")
async def search_resumes(
    query: str = Query(..., description="搜索关键词"), 
    db: Session = Depends(get_db)
):
    # 调用解耦后的 logic 层
    results = SearchProcessor.semantic_search(db, query)
    
    return [
        {
            "resume_id": r.resume_id, 
            "content": r.content,
            "metadata": r.metadata # 如果你有存的话
        } for r in results
    ]