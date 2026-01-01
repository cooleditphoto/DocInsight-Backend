FROM python:3.10-slim

WORKDIR /app

# 安装必要系统依赖
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    libgl1 \
    && rm -rf /var/lib/apt/lists/*

# 先安装依赖（利用缓存）
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制所有文件
COPY . .

# 【核心修复】: 设置 PYTHONPATH 确保 Python 能看到 /app 目录下的包
ENV PYTHONPATH=/app

# 使用 python -m 启动通常比直接启动 uvicorn 更能准确处理包路径
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]