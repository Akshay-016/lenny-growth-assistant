"use client";

import { FormEvent, useEffect, useState } from "react";
import ReactMarkdown from "react-markdown";

import {
  Artifact,
  ChatCitation,
  HealthResponse,
  Message,
  Session,
  createSession,
  getHealth,
  getSessionArtifacts,
  getSessionMessages,
  listSessions,
  sendChat,
} from "@/lib/api";

export default function HomePage() {
  const [sessions, setSessions] = useState<Session[]>([]);
  const [activeSessionId, setActiveSessionId] =
    useState<string | null>(null);

  const [messages, setMessages] = useState<Message[]>([]);

  const [citations, setCitations] = useState<
    ChatCitation[]
  >([]);

  const [artifacts, setArtifacts] = useState<
    Artifact[]
  >([]);

  const [selectedArtifact, setSelectedArtifact] =
    useState<Artifact | null>(null);

  const [loadingArtifacts, setLoadingArtifacts] =
    useState(false);

  const [input, setInput] = useState("");
  const [loadingSessions, setLoadingSessions] =
    useState(true);

  const [loadingMessages, setLoadingMessages] =
    useState(false);

  const [sending, setSending] = useState(false);

  const [error, setError] = useState<string | null>(
    null,
  );

  const [health, setHealth] =
    useState<HealthResponse | null>(null);

  // ---------------------------------------------------------
  // Load application health and existing sessions.
  // ---------------------------------------------------------

  useEffect(() => {
    async function loadHealth() {
      try {
        const healthResponse = await getHealth();
        setHealth(healthResponse);
      } catch {
        // Health information is informational only.
        // Do not prevent the chat application from loading.
        setHealth(null);
      }
    }

    async function loadSessions() {
      try {
        setLoadingSessions(true);
        setError(null);

        const existingSessions = await listSessions();

        setSessions(existingSessions);

        if (existingSessions.length > 0) {
          setActiveSessionId(existingSessions[0].id);
        } else {
          const newSession =
            await createSession("New Conversation");

          setSessions([newSession]);
          setActiveSessionId(newSession.id);
        }
      } catch (err) {
        setError(
          err instanceof Error
            ? err.message
            : "Failed to load sessions.",
        );
      } finally {
        setLoadingSessions(false);
      }
    }

    loadHealth();
    loadSessions();
  }, []);

  // ---------------------------------------------------------
  // Load messages and artifacts whenever the selected
  // session changes.
  // ---------------------------------------------------------

  useEffect(() => {
    if (!activeSessionId) {
      setMessages([]);
      setCitations([]);
      setArtifacts([]);
      setSelectedArtifact(null);
      return;
    }

    async function loadSessionData() {
      try {
        setLoadingMessages(true);
        setLoadingArtifacts(true);
        setError(null);

        // Load conversation messages.
        const sessionMessages =
          await getSessionMessages(
            activeSessionId!,
          );

        // Load artifacts belonging to this conversation.
        const sessionArtifacts =
          await getSessionArtifacts(
            activeSessionId!,
          );

        setMessages(sessionMessages);
        setCitations([]);
        setArtifacts(sessionArtifacts);

        // Automatically select the first artifact.
        if (sessionArtifacts.length > 0) {
          setSelectedArtifact(sessionArtifacts[0]);
        } else {
          setSelectedArtifact(null);
        }
      } catch (err) {
        setError(
          err instanceof Error
            ? err.message
            : "Failed to load conversation data.",
        );
      } finally {
        setLoadingMessages(false);
        setLoadingArtifacts(false);
      }
    }

    loadSessionData();
  }, [activeSessionId]);

  // ---------------------------------------------------------
  // Create a new conversation.
  // ---------------------------------------------------------

  async function handleNewChat() {
    try {
      setError(null);

      const newSession = await createSession(
        "New Conversation",
      );

      setSessions((currentSessions) => [
        newSession,
        ...currentSessions,
      ]);

      setActiveSessionId(newSession.id);

      setMessages([]);
      setCitations([]);

      // Clear artifacts for the new conversation.
      setArtifacts([]);
      setSelectedArtifact(null);

      setInput("");
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Failed to create a new conversation.",
      );
    }
  }

  // ---------------------------------------------------------
  // Send a message to the RAG backend.
  // ---------------------------------------------------------

  async function handleSubmit(
    event: FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault();

    const trimmedInput = input.trim();

    if (!trimmedInput || !activeSessionId || sending) {
      return;
    }

    const temporaryUserMessage: Message = {
      id: `temporary-${Date.now()}`,
      session_id: activeSessionId,
      role: "user",
      content: trimmedInput,
      created_at: new Date().toISOString(),
    };

    setMessages((currentMessages) => [
      ...currentMessages,
      temporaryUserMessage,
    ]);

    setInput("");
    setSending(true);
    setError(null);
    setCitations([]);

    try {
      const response = await sendChat({
        session_id: activeSessionId,
        message: trimmedInput,
        top_k: 5,
        similarity_threshold: 0.65,
      });

      const assistantMessage: Message = {
        id: `assistant-${Date.now()}`,
        session_id: activeSessionId,
        role: "assistant",
        content: response.answer,
        created_at: new Date().toISOString(),
      };

      setMessages((currentMessages) => [
        ...currentMessages,
        assistantMessage,
      ]);

      setCitations(response.citations);

      // Refresh the session list so its updated_at value
      // reflects the latest conversation activity.
      const updatedSessions = await listSessions();

      setSessions(updatedSessions);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Failed to send the message.",
      );

      // Remove the temporary user message if sending failed.
      setMessages((currentMessages) =>
        currentMessages.filter(
          (message) =>
            message.id !== temporaryUserMessage.id,
        ),
      );
    } finally {
      setSending(false);
    }
  }

  // ---------------------------------------------------------
  // Render
  // ---------------------------------------------------------

  const providerLabel =
    health?.llm_provider === "anthropic"
      ? "Cloud Anthropic"
      : health?.llm_provider === "ollama"
        ? "Local Ollama"
        : "Provider unavailable";

  const healthLabel =
    health?.status === "healthy"
      ? "System healthy"
      : health
        ? "System degraded"
        : "Health check unavailable";

  const healthIndicatorClass =
    health?.status === "healthy"
      ? "bg-green-500"
      : health
        ? "bg-yellow-500"
        : "bg-gray-400";

  return (
    <main className="flex h-screen bg-[#f7f7f5] text-[#171717]">

      {/* =====================================================
          LEFT SIDEBAR
          ===================================================== */}

      <aside className="flex w-72 flex-col border-r border-[#deded9] bg-[#f1f1ed]">

        {/* Logo / application name */}

        <div className="border-b border-[#deded9] px-5 py-5">
          <h1 className="text-lg font-semibold">
            Lenny Growth Assistant
          </h1>

          <p className="mt-1 text-xs text-[#6b6b66]">
            Lenny&apos;s Podcast knowledge
          </p>
        </div>

        {/* New conversation button */}

        <div className="p-4">
          <button
            type="button"
            onClick={handleNewChat}
            className="w-full rounded-lg border border-[#cfcfca] bg-white px-4 py-2.5 text-sm font-medium shadow-sm transition hover:bg-[#fafafa]"
          >
            + New Chat
          </button>
        </div>

        {/* Conversation list */}

        <div className="flex-1 overflow-y-auto px-3 pb-4">

          <p className="px-2 pb-2 text-xs font-semibold uppercase tracking-wide text-[#777771]">
            Conversations
          </p>

          {loadingSessions ? (
            <div className="px-2 py-3 text-sm text-[#777771]">
              Loading conversations...
            </div>
          ) : sessions.length === 0 ? (
            <div className="px-2 py-3 text-sm text-[#777771]">
              No conversations yet.
            </div>
          ) : (
            <div className="space-y-1">
              {sessions.map((session) => (
                <button
                  key={session.id}
                  type="button"
                  onClick={() =>
                    setActiveSessionId(session.id)
                  }
                  className={`w-full rounded-lg px-3 py-3 text-left text-sm transition ${
                    activeSessionId === session.id
                      ? "bg-white font-medium shadow-sm"
                      : "hover:bg-white/70"
                  }`}
                >
                  <div className="truncate">
                    {session.title ||
                      "Untitled conversation"}
                  </div>

                  <div className="mt-1 text-xs text-[#858580]">
                    {new Date(
                      session.updated_at,
                    ).toLocaleDateString()}
                  </div>
                </button>
              ))}
            </div>
          )}

        </div>

        {/* Footer / provider status */}

        <div className="border-t border-[#deded9] px-5 py-4">

          <div className="flex items-center gap-2">
            <span
              className={`h-2 w-2 rounded-full ${healthIndicatorClass}`}
            />

            <span className="text-xs font-medium text-[#555550]">
              {providerLabel}
            </span>
          </div>

          <p className="mt-1 text-xs text-[#777771]">
            {healthLabel}
          </p>

          {health?.ollama === "healthy" && (
            <p className="mt-1 text-xs text-[#999994]">
              Local RAG + Ollama
            </p>
          )}

        </div>

      </aside>

      {/* =====================================================
          MAIN CHAT AREA
          ===================================================== */}

      <section className="flex min-w-0 flex-1 flex-col">

        {/* Header */}

        <header className="flex h-16 items-center border-b border-[#deded9] bg-white px-6">

          <div>
            <h2 className="font-semibold">
              Growth Assistant
            </h2>

            <p className="text-xs text-[#777771]">
              Ask questions about product, growth,
              startups, and Lenny&apos;s Podcast.
            </p>
          </div>

        </header>

        {/* Error */}

        {error && (
          <div className="mx-auto mt-4 w-full max-w-4xl px-6">
            <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
              {error}
            </div>
          </div>
        )}

        {/* Messages */}

        <div className="flex-1 overflow-y-auto">

          <div className="mx-auto flex w-full max-w-4xl flex-col gap-6 px-6 py-8">

            {!activeSessionId ? (
              <div className="flex flex-1 items-center justify-center py-32">
                <p className="text-sm text-[#777771]">
                  Create a conversation to get started.
                </p>
              </div>
            ) : loadingMessages ? (
              <div className="py-20 text-center text-sm text-[#777771]">
                Loading conversation...
              </div>
            ) : messages.length === 0 ? (
              <div className="py-20 text-center">

                <h3 className="text-2xl font-semibold">
                  What would you like to explore?
                </h3>

                <p className="mx-auto mt-3 max-w-lg text-sm leading-6 text-[#777771]">
                  Ask about product strategy, growth,
                  hiring, startups, leadership, or other
                  topics discussed on Lenny&apos;s Podcast.
                </p>

              </div>
            ) : (
              messages.map((message) => (
                <div
                  key={message.id}
                  className={`flex ${
                    message.role === "user"
                      ? "justify-end"
                      : "justify-start"
                  }`}
                >

                  <div
                    className={`max-w-3xl rounded-2xl px-5 py-4 ${
                      message.role === "user"
                        ? "bg-[#171717] text-white"
                        : "border border-[#deded9] bg-white"
                    }`}
                  >

                    <div className="mb-2 text-xs font-semibold uppercase tracking-wide opacity-60">
                      {message.role === "user"
                        ? "You"
                        : "Lenny Growth Assistant"}
                    </div>

                    <div
                      className={`text-sm leading-7 ${
                        message.role === "user"
                          ? "text-white"
                          : "text-[#292925]"
                      }`}
                    >
                      {message.role === "assistant" ? (
                        <ReactMarkdown>
                          {message.content}
                        </ReactMarkdown>
                      ) : (
                        <p className="whitespace-pre-wrap">
                          {message.content}
                        </p>
                      )}
                    </div>

                  </div>

                </div>
              ))
            )}

            {/* Loading indicator */}

            {sending && (
              <div className="flex justify-start">
                <div className="rounded-2xl border border-[#deded9] bg-white px-5 py-4">
                  <div className="text-xs font-semibold uppercase tracking-wide text-[#858580]">
                    Lenny Growth Assistant
                  </div>

                  <div className="mt-2 text-sm text-[#777771]">
                    Thinking...
                  </div>
                </div>
              </div>
            )}

            {/* Sources */}

            {citations.length > 0 && !sending && (
              <div className="mt-2 rounded-xl border border-[#deded9] bg-white p-5">

                <h3 className="text-sm font-semibold">
                  Sources
                </h3>

                <div className="mt-3 space-y-3">

                  {citations.map((citation) => (
                    <div
                      key={citation.citation_number}
                      className="rounded-lg bg-[#f7f7f5] p-3"
                    >

                      <div className="flex gap-3">

                        <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-[#171717] text-xs font-semibold text-white">
                          {citation.citation_number}
                        </span>

                        <div className="min-w-0">

                          <p className="text-sm font-medium">
                            {citation.episode_title}
                          </p>

                          <p className="mt-1 text-xs text-[#777771]">
                            Transcript chunk{" "}
                            {citation.chunk_index}
                            {" · "}
                            Similarity{" "}
                            {citation.similarity.toFixed(3)}
                          </p>

                          {citation.episode_url && (
                            <a
                              href={
                                citation.episode_url
                              }
                              target="_blank"
                              rel="noopener noreferrer"
                              className="mt-2 inline-block text-xs font-medium underline"
                            >
                              Open episode
                            </a>
                          )}

                        </div>

                      </div>

                    </div>
                  ))}

                </div>

              </div>
            )}

          </div>

        </div>

        {/* ===================================================
            MESSAGE INPUT
            =================================================== */}

        <div className="border-t border-[#deded9] bg-white px-6 py-5">

          <form
            onSubmit={handleSubmit}
            className="mx-auto flex w-full max-w-4xl gap-3"
          >

            <textarea
              value={input}
              onChange={(event) =>
                setInput(event.target.value)
              }
              onKeyDown={(event) => {
                if (
                  event.key === "Enter" &&
                  !event.shiftKey
                ) {
                  event.preventDefault();
                  event.currentTarget.form?.requestSubmit();
                }
              }}
              placeholder={
                activeSessionId
                  ? "Ask Lenny Growth Assistant..."
                  : "Create a conversation first..."
              }
              disabled={
                !activeSessionId || sending
              }
              rows={2}
              className="min-h-[56px] flex-1 resize-none rounded-xl border border-[#cfcfca] bg-[#fafafa] px-4 py-3 text-sm outline-none transition focus:border-[#999994] focus:ring-2 focus:ring-[#e8e8e3] disabled:cursor-not-allowed disabled:opacity-60"
            />

            <button
              type="submit"
              disabled={
                !activeSessionId ||
                !input.trim() ||
                sending
              }
              className="self-end rounded-xl bg-[#171717] px-6 py-3 text-sm font-medium text-white transition hover:bg-[#303030] disabled:cursor-not-allowed disabled:opacity-40"
            >
              {sending ? "Sending..." : "Send"}
            </button>

          </form>

          <p className="mx-auto mt-2 max-w-4xl text-xs text-[#999994]">
            Enter to send · Shift + Enter for a new line
          </p>

        </div>

      </section>

      {/* =====================================================
          ARTIFACT PANEL
          ===================================================== */}

      <aside className="hidden w-[420px] flex-col border-l border-[#deded9] bg-white lg:flex">

        {/* Artifact header */}

        <div className="border-b border-[#deded9] px-5 py-4">

          <div className="flex items-center justify-between">

            <div>
              <h2 className="font-semibold">
                Artifacts
              </h2>

              <p className="mt-1 text-xs text-[#777771]">
                Generated work for this conversation
              </p>
            </div>

            {loadingArtifacts && (
              <span className="text-xs text-[#777771]">
                Loading...
              </span>
            )}

          </div>

        </div>

        {/* Artifact list */}

        {artifacts.length > 0 && (
          <div className="border-b border-[#deded9] p-3">

            <div className="space-y-1">

              {artifacts.map((artifact) => (
                <button
                  key={artifact.id}
                  type="button"
                  onClick={() =>
                    setSelectedArtifact(artifact)
                  }
                  className={`w-full rounded-lg px-3 py-3 text-left transition ${
                    selectedArtifact?.id === artifact.id
                      ? "bg-[#f1f1ed] font-medium"
                      : "hover:bg-[#f7f7f5]"
                  }`}
                >

                  <div className="truncate text-sm">
                    {artifact.title ||
                      "Untitled artifact"}
                  </div>

                  <div className="mt-1 text-xs text-[#777771]">
                    {artifact.artifact_type}
                  </div>

                </button>
              ))}

            </div>

          </div>
        )}

        {/* Artifact viewer */}

        <div className="flex-1 overflow-y-auto">

          {loadingArtifacts ? (
            <div className="p-6 text-center text-sm text-[#777771]">
              Loading artifacts...
            </div>
          ) : selectedArtifact ? (
            <div className="p-6">

              <div className="mb-5">

                <div className="text-xs font-semibold uppercase tracking-wide text-[#858580]">
                  {selectedArtifact.artifact_type}
                </div>

                <h3 className="mt-2 text-xl font-semibold">
                  {selectedArtifact.title ||
                    "Untitled artifact"}
                </h3>

              </div>

              <article className="prose prose-sm max-w-none text-[#292925]">
                <ReactMarkdown>
                  {selectedArtifact.content}
                </ReactMarkdown>
              </article>

            </div>
          ) : (
            <div className="flex h-full items-center justify-center p-8 text-center">

              <div>

                <div className="text-3xl">
                  📄
                </div>

                <h3 className="mt-3 text-sm font-semibold">
                  No artifact selected
                </h3>

                <p className="mt-2 text-xs leading-5 text-[#777771]">
                  Create or add an artifact to this
                  conversation and it will appear here.
                </p>

              </div>

            </div>
          )}

        </div>

      </aside>

    </main>
  );
}