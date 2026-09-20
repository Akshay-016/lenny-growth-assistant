# Manual Test Plan — Lenny Growth Assistant

## 1. Purpose

This document defines the manual verification plan for the Lenny Growth Assistant.

The plan covers:

- Application startup
- Backend health
- PostgreSQL persistence
- Ollama local LLM
- Transcript knowledge-base retrieval
- Grounded conversational responses
- Source citations
- Conversation context
- Session isolation
- API validation and error handling
- Frontend UI
- Artifact API and viewer
- Ship 30 skill
- Provider configuration
- Request tracing and operational behavior

The expected results below describe the current implementation and are intended to be executed before final submission.

---

# 2. Test Environment

## Hardware / Software

- Operating System: Windows
- Editor: VS Code
- Python: 3.13+
- Node.js: Installed
- Docker Desktop: Installed
- PostgreSQL: Docker container
- Ollama: Local installation
- Browser: Chrome / Edge

## Project

Repository:

`https://github.com/Akshay-016/lenny-growth-assistant`

Backend:

`http://localhost:8000`

Frontend:

`http://localhost:3000`

Ollama:

`http://localhost:11434`

PostgreSQL:

`localhost:5433`

---

# 3. Prerequisites

Before beginning the tests:

1. Docker Desktop is running.
2. PostgreSQL container is running.
3. Ollama is running.
4. Required Ollama models are available:
   - `llama3.2:3b`
   - `nomic-embed-text`
5. Python virtual environment is available.
6. Backend dependencies are installed.
7. Frontend dependencies are installed.
8. Database tables have been created.
9. Transcript knowledge base has already been ingested.

---

# 4. Application Startup

## TEST-001 — Start PostgreSQL

### Steps

Run:

```cmd
docker compose up -d db
# 15. Artifact Generation and Viewer

## TEST-ART-001 - Generate a Grounded Artifact

### Steps

1. Open `http://localhost:3000`.
2. Select or create a conversation.
3. In the right-side Artifact panel, click **+ Create Artifact**.
4. Select an artifact type such as `Framework`.
5. Enter a title, for example `Product Growth Framework`.
6. Enter a request based on Lenny's Podcast knowledge.
7. Click **Generate Artifact**.
8. Wait for Ollama to complete generation.

### Expected Result

- The artifact is generated successfully.
- The artifact appears in the Artifact panel.
- The generated content is grounded in transcript evidence.
- The artifact viewer displays the generated Markdown content.
- Source information is returned by the backend.
- No artifact is created when the retrieval step has insufficient evidence.

## TEST-ART-002 - Artifact API

### Steps

Send a POST request to:

`http://localhost:8000/api/artifacts/generate`

using a valid session ID, artifact type, and grounded request.

### Expected Result

- HTTP `201 Created` is returned for successful generation.
- The response contains `artifact`, `grounded`, and `sources`.
- The saved artifact can be retrieved using its artifact ID.

## TEST-ART-003 - Artifact Session Isolation

### Steps

1. Generate an artifact in Session A.
2. Switch to Session B.
3. Inspect the Artifact panel.

### Expected Result

- Session B does not display artifacts belonging to Session A.
- Returning to Session A displays its previously generated artifacts.
