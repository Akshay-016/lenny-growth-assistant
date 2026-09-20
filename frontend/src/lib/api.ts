const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

export interface Session {
  id: string;
  title: string | null;
  created_at: string;
  updated_at: string;
}

export interface Message {
  id: string;
  session_id: string;
  role: string;
  content: string;
  created_at: string;
}

export interface ChatCitation {
  citation_number: number;
  episode_title: string;
  episode_url: string | null;
  chunk_index: number;
  similarity: number;
}

export interface ChatResponse {
  session_id: string;
  answer: string;
  grounded: boolean;
  citations: ChatCitation[];
}

export interface ChatRequest {
  session_id: string;
  message: string;
  top_k?: number;
  similarity_threshold?: number;
}

export interface HealthResponse {
  status: string;
  database: string;
  ollama: string;
  vector_index: string;
  llm_provider: string;
  anthropic: string;
}

/*
 * ============================================================
 * ARTIFACTS
 * ============================================================
 */

export interface Artifact {
  id: string;
  session_id: string;
  artifact_type: string;
  title: string | null;
  content: string;
  created_at: string;
}


async function request<T>(
  endpoint: string,
  options?: RequestInit,
): Promise<T> {
  const response = await fetch(
    `${API_BASE_URL}${endpoint}`,
    {
      ...options,
      headers: {
        "Content-Type": "application/json",
        ...(options?.headers || {}),
      },
    },
  );

  if (!response.ok) {
    let detail =
      `Request failed with status ${response.status}.`;

    try {
      const errorBody = await response.json();

      if (
        typeof errorBody?.detail === "string"
      ) {
        detail = errorBody.detail;
      }
    } catch {
      // Keep the default error message.
    }

    throw new Error(detail);
  }

  return response.json() as Promise<T>;
}


/*
 * ============================================================
 * HEALTH
 * ============================================================
 */

export async function getHealth(): Promise<HealthResponse> {
  return request<HealthResponse>(
    "/api/health",
  );
}


/*
 * ============================================================
 * SESSIONS
 * ============================================================
 */

export async function createSession(
  title?: string,
): Promise<Session> {
  return request<Session>(
    "/api/sessions",
    {
      method: "POST",
      body: JSON.stringify({
        title: title || null,
      }),
    },
  );
}


export async function listSessions(): Promise<Session[]> {
  return request<Session[]>(
    "/api/sessions",
  );
}


export async function getSession(
  sessionId: string,
): Promise<Session> {
  return request<Session>(
    `/api/sessions/${sessionId}`,
  );
}


export async function getSessionMessages(
  sessionId: string,
): Promise<Message[]> {
  return request<Message[]>(
    `/api/sessions/${sessionId}/messages`,
  );
}


/*
 * ============================================================
 * CHAT
 * ============================================================
 */

export async function sendChat(
  requestData: ChatRequest,
): Promise<ChatResponse> {
  return request<ChatResponse>(
    "/api/chat",
    {
      method: "POST",
      body: JSON.stringify({
        session_id: requestData.session_id,
        message: requestData.message,
        top_k: requestData.top_k ?? 5,
        similarity_threshold:
          requestData.similarity_threshold ?? 0.65,
      }),
    },
  );
}


/*
 * ============================================================
 * ARTIFACTS
 * ============================================================
 */

/**
 * Get all artifacts belonging to a conversation.
 */
export async function getSessionArtifacts(
  sessionId: string,
): Promise<Artifact[]> {
  return request<Artifact[]>(
    `/api/sessions/${sessionId}/artifacts`,
  );
}


/**
 * Get one artifact by ID.
 */
export async function getArtifact(
  artifactId: string,
): Promise<Artifact> {
  return request<Artifact>(
    `/api/artifacts/${artifactId}`,
  );
}