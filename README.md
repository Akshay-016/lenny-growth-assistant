# Lenny Growth Assistant

A full-stack AI-powered conversational assistant that answers product and growth questions using grounded knowledge from Lenny's Podcast transcripts.

Public repository: https://github.com/Akshay-016/lenny-growth-assistant

The application combines:

- Next.js frontend
- FastAPI backend
- PostgreSQL
- pgvector semantic search
- Ollama local inference
- Anthropic Claude cloud inference
- Retrieval-Augmented Generation (RAG)
- Claude Agent SDK integration
- Persistent conversation sessions
- Transcript source citations
- Ship 30 for 30 content generation
- Artifact generation and in-app Markdown viewing
- Structured application logging and request tracing

---

## 1. Product Overview

The Lenny Growth Assistant helps Product Managers and Growth Leaders quickly extract actionable knowledge from Lenny's Podcast transcripts.

Instead of manually searching through hundreds of podcast transcripts, a user can ask questions such as:

> What makes a good product strategy?

The system:

1. Creates or selects a conversation session.
2. Receives the user's question.
3. Generates a query embedding.
4. Searches the transcript knowledge base using pgvector.
5. Selects relevant evidence.
6. Generates a grounded response using the configured LLM provider.
7. Returns transcript source metadata.
8. Persists the conversation in PostgreSQL.

The application also supports Ship 30 for 30-style article generation from retrieved transcript evidence.

---

## 2. Architecture

```text
                         User
                           |
                           v
                  +------------------+
                  |    Next.js UI    |
                  |                  |
                  | Chat             |
                  | Sessions         |
                  | Sources          |
                  | Artifacts        |
                  | Provider Status  |
                  +--------+---------+
                           |
                           | HTTP
                           v
                  +------------------+
                  |     FastAPI      |
                  |                  |
                  | Chat API         |
                  | Session API      |
                  | Artifact API     |
                  | Health API       |
                  +--------+---------+
                           |
             +-------------+-------------+
             |             |             |
             v             v             v
       +-----------+ +-----------+ +-----------+
       | PostgreSQL| | RAG Engine| | LLM Layer |
       | + pgvector| |           | |           |
       |           | | Embedding | | Ollama    |
       | Sessions  | | Retrieval | | Anthropic |
       | Messages  | | Grounding | | Claude SDK|
       | Artifacts | +-----------+ +-----------+
       | Chunks    |
       +-----------+
             |
             v
     Lenny Podcast Transcripts

Project Structure:

    lenny-growth-assistant/
    │
    ├── backend/
    │   ├── app/
    │   │   ├── agent/
    │   │   │   └── lenny_agent.py
    │   │   │
    │   │   ├── api/
    │   │   │   ├── artifacts.py
    │   │   │   ├── chat.py
    │   │   │   └── sessions.py
    │   │   │
    │   │   ├── models/
    │   │   │   ├── db_models.py
    │   │   │   └── schemas.py
    │   │   │
    │   │   ├── providers/
    │   │   │   ├── embedding.py
    │   │   │   └── llm.py
    │   │   │
    │   │   ├── rag/
    │   │   │   ├── chunker.py
    │   │   │   ├── generator.py
    │   │   │   ├── ingestion.py
    │   │   │   ├── loader.py
    │   │   │   └── retriever.py
    │   │   │
    │   │   ├── skills/
    │   │   │   ├── ship30.py
    │   │   │   └── ship30_generator.py
    │   │   │
    │   │   ├── config.py
    │   │   ├── database.py
    │   │   └── main.py
    │   │
    │   ├── scripts/
    │   │   ├── create_tables.py
    │   │   ├── ingest_transcripts.py
    │   │   ├── migrate_add_source_path.py
    │   │   ├── retry_failed_transcripts.py
    │   │   └── test_ship30_real.py
    │   │
    │   ├── tests/
    │   │   ├── test_chunker.py
    │   │   ├── test_database_connection.py
    │   │   ├── test_embeddings.py
    │   │   ├── test_ingestion_database.py
    │   │   ├── test_ingestion_embeddings.py
    │   │   ├── test_ingestion_pipeline.py
    │   │   ├── test_llm_provider.py
    │   │   ├── test_loader.py
    │   │   ├── test_rag_generator.py
    │   │   ├── test_rag_integration.py
    │   │   ├── test_retriever.py
    │   │   ├── test_ship30_generator.py
    │   │   └── test_ship30_skill.py
    │   │
    │   └── requirements.txt
    │
    ├── data/
    │   └── raw/
    │       └── lennys-podcast-transcripts/
    │
    ├── docs/
    │   ├── architecture.md
    │   ├── design.md
    │   └── PRD.md
    │
    ├── frontend/
    │   ├── src/
    │   │   ├── app/
    │   │   │   ├── globals.css
    │   │   │   ├── layout.tsx
    │   │   │   └── page.tsx
    │   │   └── lib/
    │   │       └── api.ts
    │   └── package.json
    │
    ├── .env.example
    ├── docker-compose.yml
    ├── pytest.ini
    └── README.md


Prerequisites

Install the following:

Python 3.13+
Node.js
npm
Docker Desktop
Ollama
Git

Verify the installations:

python --version
node --version
npm --version
docker --version
docker compose version
ollama --version



git clone https://github.com/Akshay-016/lenny-growth-assistant.git
cd lenny-growth-assistant

Python Virtual Environment

Create the virtual environment:

python -m venv .venv

Activate it on Windows:

.venv\Scripts\activate

Install backend dependencies:

pip install -r backend\requirements.txt


Environment Configuration

Create the local environment file:

copy .env.example .env

For local development, configure the environment as follows:

APP_NAME=Lenny Growth Assistant
APP_ENV=development
LOG_LEVEL=INFO

BACKEND_HOST=0.0.0.0
BACKEND_PORT=8000

DATABASE_URL=postgresql+asyncpg://postgres:password123@localhost:5433/lenny_assistant

DEFAULT_LLM_PROVIDER=ollama

OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2:3b

ANTHROPIC_API_KEY=
ANTHROPIC_MODEL=claude-sonnet-4-6

RETRIEVAL_TOP_K=5
RETRIEVAL_SIMILARITY_THRESHOLD=0.65

NEXT_PUBLIC_API_URL=http://localhost:8000

Do not commit .env to Git.

8. PostgreSQL + pgvector

The application uses PostgreSQL with the pgvector extension.

Start the database:

docker compose up -d db

Check the database:

docker compose ps

The expected database container is:

lenny_postgres

The database is exposed locally on:

localhost:5433

The PostgreSQL container listens internally on:

5432
9. Create Database Tables

After PostgreSQL is healthy, run:

python backend\scripts\create_tables.py

Expected output:

Database tables created successfully.

The application uses these main tables:

sessions
messages
artifacts
transcript_chunks

The transcript_chunks table stores transcript embeddings and uses pgvector for semantic similarity search.

10. Ollama Setup

Install and start Ollama.

Verify that Ollama is available:

curl http://127.0.0.1:11434/api/tags

Pull the local chat model:

ollama pull llama3.2:3b

Pull the embedding model:

ollama pull nomic-embed-text

Verify installed models:

ollama list

The application uses:

Chat model:
llama3.2:3b

Embedding model:
nomic-embed-text

The embedding model produces 768-dimensional vectors, matching the pgvector column used by the application.

11. Transcript Knowledge Base

The application uses Lenny's Podcast transcript content as its knowledge base.

Transcript files are stored locally under:

data/raw/lennys-podcast-transcripts/

The raw transcript corpus is intentionally excluded from Git because it is local
input data rather than application source code. A fresh clone therefore needs the
transcript corpus to be placed in this directory before running the ingestion
pipeline.

The ingestion pipeline:

Loads transcript files.
Parses transcript metadata.
Cleans transcript text.
Splits transcripts into chunks.
Generates embeddings using Ollama.
Stores chunks and embeddings in PostgreSQL.
Uses pgvector for semantic retrieval.

To run ingestion:

python backend\scripts\ingest_transcripts.py

The ingestion pipeline is designed to avoid duplicate transcript chunks using the source path and chunk index.

12. Start the Backend

From the project root with the virtual environment activated:

uvicorn backend.app.main:app --host 0.0.0.0 --port 8000

Backend:

http://127.0.0.1:8000

Interactive API documentation:

http://127.0.0.1:8000/docs

Root endpoint:

GET /

Health endpoint:

GET /api/health
13. Health Check

Run:

curl http://127.0.0.1:8000/api/health

Example response:

{
  "status": "healthy",
  "database": "healthy",
  "ollama": "healthy",
  "vector_index": "configured",
  "llm_provider": "ollama",
  "anthropic": "not_configured"
}

The health endpoint checks:

PostgreSQL connectivity
Ollama availability
configured LLM provider
vector index configuration
Anthropic configuration status

Secrets such as API keys are not returned.

14. Start the Frontend

Open another terminal.

Navigate to the frontend:

cd frontend

Install dependencies:

npm install

Start the development server:

npm run dev

Frontend:

http://localhost:3000

The frontend communicates with the backend through:

http://localhost:8000

The API URL is configured through:

NEXT_PUBLIC_API_URL
15. Production Frontend Build

Create a production build:

cd frontend
npm run build

Start the production server:

npm run start
16. LLM Providers

The application uses a provider abstraction so the rest of the application does not depend directly on a single LLM provider.

Local Ollama

Default configuration:

DEFAULT_LLM_PROVIDER=ollama

Ollama is used for:

local chat generation
local embedding generation

This mode does not require a cloud API key.

Anthropic

To use Anthropic:

DEFAULT_LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=<your-api-key>
ANTHROPIC_MODEL=claude-sonnet-4-6

Never commit the API key to Git.

The backend uses the Anthropic Python SDK and Claude Agent SDK for the cloud agent path.

17. Chat API
Create a Session
POST /api/sessions

Example:

{
  "title": "Product Strategy"
}
Send a Chat Message
POST /api/chat

Example:

{
  "session_id": "SESSION_UUID",
  "message": "What makes a good product strategy?",
  "top_k": 5,
  "similarity_threshold": 0.65
}

The response contains:

session ID
grounded answer
grounding status
transcript citations

Example response structure:

{
  "session_id": "SESSION_UUID",
  "answer": "...",
  "grounded": true,
  "citations": [
    {
      "citation_number": 1,
      "episode_title": "...",
      "episode_url": "...",
      "chunk_index": 3,
      "similarity": 0.82
    }
  ]
}
18. Grounding and Retrieval

The RAG pipeline follows:

User question
      |
      v
Query embedding
      |
      v
pgvector similarity search
      |
      v
Relevant transcript chunks
      |
      v
Evidence selection
      |
      v
Grounded prompt
      |
      v
LLM provider
      |
      v
Answer + verified source metadata

The assistant is designed to avoid presenting unsupported information as transcript-derived knowledge.

When the available evidence is insufficient, the system should acknowledge the limitation rather than fabricate transcript evidence.

19. Sessions and Conversation Context

Each conversation has its own session ID.

Messages are persisted in PostgreSQL.

The chat API loads recent conversation history for the active session before generating the next response.

This allows follow-up questions within the same conversation.

Example:

User:
What makes a good product strategy?

User:
How would that apply to an early-stage startup?

The second question can use the context of the same session.

20. Ship 30 for 30 Skill

The project includes a dedicated Ship 30 for 30 skill:

backend/app/skills/ship30.py
backend/app/skills/ship30_generator.py

The generator:

Retrieves relevant transcript evidence.
Selects diverse evidence.
Provides the evidence to the writing model.
Generates a structured article.
Preserves grounding requirements.
Attaches verified source metadata separately.

The target article length is approximately:

1,250 words

The skill emphasizes:

strong hooks
specific headlines
clear sections
skimmable structure
practical takeaways
transcript grounding
no fabricated quotations
no fabricated statistics
no invented citations

A manual real-generation script is available at:

backend/scripts/test_ship30_real.py
21. Artifacts

The application supports artifact records associated with sessions.

Current artifact types include:

essay
framework
checklist
growth_plan

Artifacts can be retrieved through:

GET /api/sessions/{session_id}/artifacts

and:

GET /api/artifacts/{artifact_id}

The frontend displays artifact content using Markdown rendering.

The current implementation does not execute generated JavaScript in the artifact viewer.

22. Operational Logging

The FastAPI application includes structured application logging.

Each request receives a unique request ID.

Example:

request_started request_id=... method=GET path=/api/health

request_completed request_id=... method=GET path=/api/health status=200

The request ID is also returned through:

X-Request-ID

Unexpected application errors are logged server-side while the client receives a generic error response rather than internal exception details.

23. API Error Handling

Expected errors use normal HTTP status codes.

For example, a missing session returns:

404 Not Found

with:

{
  "detail": "Session not found."
}

Unexpected application errors return a structured response:

{
  "error": "internal_server_error",
  "message": "An unexpected error occurred.",
  "request_id": "..."
}

The request ID can be used to correlate the client error with backend logs.

24. Testing

Run the backend test suite from the project root:

pytest -q

The backend test suite covers:

chunking
transcript loading
embeddings
ingestion
retrieval
RAG generation
RAG integration
LLM providers
Ship 30 skill
Ship 30 generation
database connectivity

Current verified result:

46 passed
25. Frontend Checks

From the frontend directory:

cd frontend

Run the production build:

npm run build

Run lint:

npm run lint

Start development mode:

npm run dev
26. Development Startup

For the current local development setup, start the components in this order.

Terminal 1 — PostgreSQL

From the project root:

docker compose up -d db
Terminal 2 — Ollama

Make sure Ollama is running and the required models are installed:

ollama list

Required models:

llama3.2:3b
nomic-embed-text
Terminal 3 — Backend

From the project root:

.venv\Scripts\activate

Then:

uvicorn backend.app.main:app --host 0.0.0.0 --port 8000
Terminal 4 — Frontend
cd frontend
npm run dev

Open:

http://localhost:3000
27. Docker Compose

The current docker-compose.yml provides the PostgreSQL + pgvector dependency.

Start it with:

docker compose up -d db

Check its status:

docker compose ps

The current Compose configuration runs PostgreSQL as a container.

The FastAPI backend, Next.js frontend, and Ollama runtime are currently run as local development processes.

28. Troubleshooting
PostgreSQL is unavailable

Check:

docker compose ps

If the container is stopped:

docker compose up -d db

Check port availability:

netstat -ano | findstr :5433
Ollama is unavailable

Check:

curl http://127.0.0.1:11434/api/tags

Verify installed models:

ollama list

Required models:

llama3.2:3b
nomic-embed-text
Backend cannot connect to PostgreSQL

Verify .env contains:

DATABASE_URL=postgresql+asyncpg://postgres:password123@localhost:5433/lenny_assistant

Then check:

docker compose ps
Frontend cannot reach backend

Verify the backend is running:

http://127.0.0.1:8000/api/health

Verify the frontend environment variable:

NEXT_PUBLIC_API_URL=http://localhost:8000

Restart the Next.js development server after changing environment variables.

Anthropic provider fails

Verify:

DEFAULT_LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=<your-api-key>
ANTHROPIC_MODEL=claude-sonnet-4-6

Do not commit the API key.

For a fully local setup, use:

DEFAULT_LLM_PROVIDER=ollama
29. Security Notes
.env is excluded from Git.
API keys should never be committed.
Generated artifacts are rendered as Markdown in the current viewer.
Generated JavaScript is not executed by the current artifact viewer.
Arbitrary code execution on the host machine is outside the project scope.
Internal exception details are not returned to API clients.
Request IDs are used for operational debugging.
Transcript content is used as the grounding knowledge base for the assistant.
30. Documentation

Additional project documentation is available in:

docs/PRD.md
docs/design.md
docs/architecture.md
PRD

Describes:

product problem
target users
product goals
non-goals
primary user flow
functional requirements
Design

Describes:

application layout
chat experience
session interaction
source display
artifact viewer
provider/status presentation
Architecture

Describes:

frontend/backend architecture
PostgreSQL and pgvector
RAG pipeline
LLM provider abstraction
Ollama
cloud LLM
Ship 30 skill
artifact layer
31. Technology Stack
Frontend
---------
Next.js 16
React 19
TypeScript
Tailwind CSS
React Markdown
DOMPurify (available for sanitization)

Backend
-------
FastAPI
Python
SQLAlchemy
Pydantic
Pydantic Settings

Database
--------
PostgreSQL
pgvector
asyncpg

Local AI
--------
Ollama
llama3.2:3b
nomic-embed-text

Cloud AI
--------
Anthropic
Claude Agent SDK

Retrieval
---------
Embeddings
Vector similarity search
RAG
Grounded generation

Testing
-------
pytest
pytest-asyncio