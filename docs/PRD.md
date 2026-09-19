# Lenny Growth Assistant — Product Requirements Document

## 1. Product Overview

The Lenny Growth Assistant is a full-stack AI-powered conversational application that transforms Lenny's Podcast transcripts into a reliable knowledge assistant for product managers and growth leaders.

The system uses retrieval-augmented generation (RAG) to retrieve relevant transcript passages before generating an answer.

The assistant must ground responses in the available transcript knowledge base and clearly acknowledge when the available material does not support an answer.

---

# 2. Forward Deployment Brief

## 2.1 User

The primary user is a Product Manager or Growth Leader who wants to quickly extract actionable product and growth knowledge from Lenny's Podcast without manually listening to hundreds of hours of podcast content.

## 2.2 Problem

Lenny's Podcast contains a large amount of product management, growth, startup, leadership, and strategy knowledge.

However, users face several problems:

- Finding the relevant episode is time-consuming.
- Listening through long episodes to find one insight is inefficient.
- Manually comparing advice across episodes is difficult.
- Extracting reusable written content requires additional work.
- Generated AI answers may hallucinate unless grounded in source material.

## 2.3 Product Solution

The Lenny Growth Assistant provides:

1. Grounded conversational question answering.
2. Transcript citations for generated answers.
3. Persistent chat sessions.
4. Follow-up conversation context.
5. Ship 30 for 30-style content generation.
6. Markdown and HTML/CSS artifact generation.
7. An in-app artifact viewer.
8. Local Ollama inference.
9. Cloud LLM inference.
10. A configurable model provider layer.

---

# 3. Goals

## Primary Goals

- Provide source-grounded answers from Lenny's Podcast transcripts.
- Preserve conversation context within independent sessions.
- Allow users to switch between local and cloud LLM providers.
- Generate approximately 1,250-word structured essays.
- Render generated artifacts inside the application.
- Provide a reproducible local deployment.
- Make the system understandable and operable by another engineer.

## Secondary Goals

- Provide meaningful automated tests.
- Provide structured application logging.
- Gracefully handle failures.
- Document architecture and implementation decisions.

---

# 4. Non-Goals

The following are intentionally outside the initial scope:

- General-purpose internet search.
- Training or fine-tuning a new LLM.
- Building a public social network.
- User billing or subscription management.
- Mobile-native applications.
- Arbitrary execution of generated code on the host machine.

The assistant should primarily operate over the provided Lenny's Podcast knowledge base.

---

# 5. Primary User Flow

```text
User opens application
        |
        v
Create/select chat session
        |
        v
Ask product/growth question
        |
        v
Generate query embedding
        |
        v
Retrieve relevant transcript chunks
        |
        v
Check retrieval relevance
        |
        +---- Low relevance ----> Explain insufficient evidence
        |
        v
Build grounded context
        |
        v
Route request to selected LLM
        |
        v
Generate answer
        |
        v
Display answer + transcript citations