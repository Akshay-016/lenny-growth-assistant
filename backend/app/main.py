from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Lenny Growth Assistant",
    description="RAG-powered assistant for Lenny's Podcast knowledge",
    version="0.1.0",
)

# Frontend development origin.
# We will make this configurable later.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {
        "name": "Lenny Growth Assistant",
        "status": "running",
        "version": "0.1.0",
    }


@app.get("/api/health")
async def health():
    return {
        "status": "healthy",
        "database": "not_configured",
        "ollama": "not_checked",
        "vector_index": "not_configured",
    }