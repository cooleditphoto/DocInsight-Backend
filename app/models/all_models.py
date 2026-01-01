from sqlalchemy import Column, String, Text, ForeignKey, DateTime, Integer
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector
from app.core.database import Base
from app.core.database import Base
import uuid
from datetime import datetime

class Resume(Base):
    __tablename__ = "resumes"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    filename = Column(String)
    # 修改或统一名称：建议使用 file_path 或 storage_url
    file_path = Column(String) 
    extracted_text = Column(Text) 
    # 新增状态字段，方便前端判断 RAG 是否处理完
    status = Column(String, default="processing") 
    created_at = Column(DateTime, default=datetime.utcnow)

    sessions = relationship("InterviewSession", back_populates="resume")

class InterviewSession(Base):
    __tablename__ = "interview_sessions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    resume_id = Column(String, ForeignKey("resumes.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    resume = relationship("Resume", back_populates="sessions")
    messages = relationship("InterviewMessage", back_populates="session")

class InterviewMessage(Base):
    __tablename__ = "interview_messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String, ForeignKey("interview_sessions.id"))
    role = Column(String)  # 'user' 或 'assistant'
    content = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    session = relationship("InterviewSession", back_populates="messages")

class ResumeChunk(Base):
    __tablename__ = "resume_chunks"
    
    id = Column(Integer, primary_key=True)
    resume_id = Column(String, ForeignKey("resumes.id"))
    content = Column(Text)  # 文本片段
    # OpenAI 的 text-embedding-3-small 维度是 1536
    embedding = Column(Vector(1536))