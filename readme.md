DocInsight: Event-Driven RAG Resume Interviewer
DocInsight is a high-performance, distributed AI interview platform. It utilizes RAG (Retrieval-Augmented Generation) to analyze candidate resumes and conduct context-aware mock interviews with real-time feedback and probing questions.

🌟 Architectural Evolution: From Batch to Stream
A core highlight of this project is the transition between two industry-standard architectures:

V1 (Airflow Mode): Initially implemented using Apache Airflow for DAG-based orchestration. While reliable for batch jobs, the inherent scheduling latency was unsuitable for real-time user interaction.

V2 (Current - Event-Driven): Re-engineered using Redpanda (Kafka) + Fast-Worker. This allows sub-second latency for PDF parsing and vector indexing. The moment a user uploads a resume, the RAG index is built asynchronously, enabling an immediate start to the interview session.

🛠️ Tech Stack
FastAPI: Asynchronous Python web framework for high-concurrency API handling.

LangChain: Orchestration of the RAG pipeline and LLM (GPT-4o-mini) integration.

PGVector: Vector similarity search extension for PostgreSQL to store document embeddings.

Redpanda: A Kafka-compatible, high-performance message bus for task distribution.

MinIO: S3-compatible object storage for secure PDF resume management.

SQLAlchemy: Robust ORM for structured data management.

🏗️ System Architecture
API Layer: FastAPI handles file uploads, persists them to MinIO, and produces a "process-resume" event to Redpanda.

Worker Layer: Asynchronous consumers listen for events, extract text from PDFs, and perform recursive character chunking.

Vectorization: Chunks are transformed into 1536-dimensional embeddings (OpenAI) and stored in PGVector.

RAG Chat: Relevant resume context is retrieved via semantic search and injected into the LLM prompt for precise, grounded interviewing.

🚀 Getting Started
1. Prerequisites
Clone the repository and set up your environment variables:

Bash

cp .env.example .env
# Edit .env and add your OPENAI_API_KEY
2. Launch with Docker
The entire ecosystem (Database, Message Queue, Storage, API, and Worker) is containerized for one-click deployment:

Bash

docker-compose up -d --build
3. API Exploration
Interactive API Docs: http://localhost:8000/docs (Swagger UI)

MinIO Console: http://localhost:9001 (Default: admin/password123)

📂 Project Structure
Plaintext

├── app/
│   ├── api/          # Route handlers (Upload, Chat, Status)
│   ├── logic/        # Core business logic (Kafka Workers, PDF Processing)
│   ├── services/     # Integration services (LLM, Embeddings, Storage)
│   ├── models/       # Database schemas & PGVector definitions
│   └── main.py       # Application entry point
├── dags/             # Legacy Airflow DAGs (Provided for architectural comparison)
├── docker-compose.yml
└── requirements.txt
💡 Key Design Decisions
Decoupling: Heavy PDF processing and Embedding generation are offloaded to background workers to keep the API responsive.

Scalability: Both the API and Worker containers can be scaled independently to handle varying loads.

Cold Start Optimization: By using Redpanda instead of full Kafka, the development environment starts significantly faster with lower memory overhead.