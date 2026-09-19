# Lenny Growth Assistant — Design Specification

## 1. Design Overview

The Lenny Growth Assistant uses a desktop-first conversational interface designed for Product Managers and Growth Leaders.

The primary interaction consists of:

1. Selecting or creating a conversation.
2. Asking a question.
3. Retrieving relevant Lenny's Podcast transcript content.
4. Streaming a grounded answer.
5. Viewing source citations.
6. Generating a Ship 30 for 30 article when required.
7. Viewing generated artifacts in a dedicated artifact pane.

The interface follows a two-pane workspace model.

---

# 2. Primary Layout

The desktop layout contains two major areas:

```text
┌──────────────────────────────────────────────────────────────┐
│                        TOP HEADER                            │
│  Lenny Growth Assistant     Session     Provider     Status  │
├───────────────────────────────┬──────────────────────────────┤
│                               │                              │
│                               │                              │
│       CHAT PANE               │       ARTIFACT PANE          │
│                               │                              │
│  Conversation history         │  Artifact Preview            │
│                               │                              │
│  User message                 │  Markdown / HTML             │
│                               │                              │
│  Assistant response           │                              │
│  + citations                  │                              │
│                               │                              │
│                               │                              │
├───────────────────────────────┤                              │
│  Message input                │                              │
│  Provider   Send              │                              │
└───────────────────────────────┴──────────────────────────────┘