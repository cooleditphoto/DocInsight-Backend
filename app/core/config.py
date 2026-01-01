from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # 基础配置
    DATABASE_URL: str = "postgresql://myuser:mypassword@localhost:5432/resume_rag"
    OPENAI_API_KEY: str

    # 之前报错缺少的变量（根据你的错误提示补全）
    llm_model: str = "gpt-4o-mini"
    minio_endpoint: str = "localhost:9000"
    minio_access_key: str = "admin"
    minio_secret_key: str = "password123"
    minio_bucket_name: str = "resumes"
    
    class Config:
        env_file = ".env"
        # 额外保险：如果你不想一个个写，可以允许额外输入（但不推荐）
        # extra = "allow" 

settings = Settings()