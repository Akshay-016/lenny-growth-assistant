# Lenny Growth Assistant — Architecture Specification

## 1. Architecture Overview

The Lenny Growth Assistant is a full-stack retrieval-augmented generation (RAG) application.

The system consists of:

- Next.js frontend.
- FastAPI backend.
- PostgreSQL relational database.
- PostgreSQL pgvector extension for semantic retrieval.
- Transcript ingestion pipeline.
- Embedding generation layer.
- RAG retrieval layer.
- Unified LLM provider interface.
- Local Ollama provider.
- Cloud LLM provider.
- Ship 30 for 30 content skill.
- Artifact generation and rendering layer.
- Docker Compose deployment.

The architecture separates product logic, retrieval, persistence, model providers, and presentation so that individual components can be changed without modifying unrelated application layers.

---

# 2. High-Level System Architecture

```text
                         ┌─────────────────────┐
                         │        User         │
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │      Next.js        │
                         │      Frontend       │
                         │                     │
                         │ Chat Interface      │
                         │ Session Selector    │
                         │ Model Selector      │
                         │ Artifact Viewer     │
                         └──────────┬──────────┘
                                    │
                              HTTP / SSE
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │       FastAPI       │
                         │       Backend       │
                         ├─────────────────────┤
                         │ Session API         │
                         │ Chat API            │
                         │ Health API          │
                         │                     │
                         │ Chat Orchestrator   │
                         └──────────┬──────────┘
                                    │
                 ┌──────────────────┼──────────────────┐
                 │                  │                  │
                 ▼                  ▼                  ▼
          ┌────────────┐     ┌────────────┐     ┌──────────────┐
          │ PostgreSQL │     │ RAG Engine │     │ Skill Engine │
          │            │     │            │     │              │
          │ Sessions   │     │ Embeddings │     │ Ship30       │
          │ Messages   │     │ Retrieval  │     │ Artifacts    │
          │ Artifacts  │     │ Grounding  │     │              │
          └────────────┘     └──────┬─────┘     └──────┬───────┘
                                    │                    │
                                    ▼                    │
                             ┌─────────────┐             │
                             │  pgvector   │             │
                             │ Transcript  │             │
                             │   Chunks    │             │
                             └──────┬──────┘             │
                                    │                    │
                                    └─────────┬──────────┘
                                              ▼
                                      ┌─────────────┐
                                      │  LLM Router │
                                      └──────┬──────┘
                                             │
                              ┌──────────────┴──────────────┐
                              ▼                             ▼
                       ┌────────────┐                ┌────────────┐
                       │   Ollama   │                │   Claude   │
                       │   Local    │                │   Cloud    │
                       └────────────┘                └────────────┘