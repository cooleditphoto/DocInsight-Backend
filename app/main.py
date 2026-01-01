# app/main.py
from fastapi import FastAPI
from app.core.database import engine, Base
from app.models import all_models # 确保导入了模型
from app.api.resumes import router as resume_router

# 这行代码会根据上面的模型创建表
Base.metadata.create_all(bind=engine)
app = FastAPI()

app.include_router(resume_router)

@app.get("/")
async def root():
    return {"message": "API is working"}

if __name__ == "__main__":
    import uvicorn
    # 这里建议写 127.0.0.1 确保本地访问
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)