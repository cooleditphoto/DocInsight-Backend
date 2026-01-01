import asyncio
import json
import os
import logging
import fitz  # PyMuPDF
from aiokafka import AIOKafkaConsumer
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import PGVector

# 1. 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 2. 环境变量加载 (确保你的 .env 映射到了容器)
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+psycopg2://myuser:password123@db:5432/resume_rag")
KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "redpanda:9092")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# 3. 初始化 AI 组件
# 注意：这里需要有效的 OPENAI_API_KEY
embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)

async def process_resume_rag(resume_id, file_path):
    """真正的 RAG 处理流程"""
    try:
        if not os.path.exists(file_path):
            logger.error(f"❌ 文件未找到: {file_path}")
            return

        # --- A. 提取文本 ---
        logger.info(f"📄 正在解析 PDF: {file_path}")
        text = ""
        with fitz.open(file_path) as doc:
            for page in doc:
                text += page.get_text()
        
        if not text.strip():
            logger.warning(f"⚠️ PDF 内容为空: {resume_id}")
            return

        # --- B. 文本切分 ---
        chunks = text_splitter.split_text(text)
        logger.info(f"✂️ 切分完成: {len(chunks)} 个文本块")

        # --- C. 向量化并存入 PGVector ---
        # 我们使用 PGVector 的 from_texts 方法
        # collection_name 可以让我们把不同的简历数据隔离开，或者统一放在一起通过 metadata 区分
        logger.info(f"🧬 正在生成向量并存入数据库...")
        
        # 将 SQLALCHEMY URL 转换为 PGVector 兼容格式
        # 注意：PGVector 通常需要特殊的连接字符串格式
        connection_str = DATABASE_URL.replace("postgresql+psycopg2://", "postgresql://")
        
        await asyncio.to_thread(
            PGVector.from_texts,
            texts=chunks,
            embedding=embeddings,
            connection_string=connection_str,
            collection_name="resumes_collection",
            metadatas=[{"resume_id": resume_id}] * len(chunks)
        )

        logger.info(f"✅ RAG 索引构建成功 | ID: {resume_id}")

    except Exception as e:
        logger.error(f"🔥 处理失败 {resume_id}: {str(e)}")

async def consume():
    consumer = AIOKafkaConsumer(
        'resume_tasks',
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        group_id="resume_rag_worker_group",
        auto_offset_reset='earliest'
    )
    await consumer.start()
    logger.info("📡 Worker 已上线，正在监听任务...")

    try:
        async for msg in consumer:
            data = json.loads(msg.value.decode('utf-8'))
            resume_id = data.get("resume_id")
            file_path = data.get("file_path")
            
            await process_resume_rag(resume_id, file_path)
    finally:
        await consumer.stop()

if __name__ == "__main__":
    asyncio.run(consume())