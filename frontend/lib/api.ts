export interface Evidence {
  source: string;
  permalink: string;
  timestamp: string;
  snippet: string;
  page_title: string;
}

export interface SubQuestion {
  id: string;
  text: string;
  sources: string[];
}

export interface ChatResponse {
  answer: string;
  evidence: Evidence[];
  session_id: string;
  guardrail_blocked?: boolean;
  refusal_reason?: string | null;
  sub_questions?: SubQuestion[];
  memories_used?: string[];
  total_tokens?: number;
  total_latency_ms?: number;
}

export interface TraceStep {
  id?: number;
  session_id: string;
  node_name: string;
  input_summary: string;
  output_summary: string;
  tokens_used: number;
  latency_ms: number;
  created_at?: string;
}

export const API_BASE = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000';

export async function checkHealth(): Promise<{ status: string }> {
  const res = await fetch(`${API_BASE}/health`, { cache: 'no-store' });
  if (!res.ok) throw new Error('Health check failed');
  return res.json();
}

export async function sendChatMessage(query: string, sessionId?: string): Promise<ChatResponse> {
  const res = await fetch(`${API_BASE}/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query, session_id: sessionId }),
  });
  if (!res.ok) {
    const err = await res.text();
    throw new Error(`Chat request failed: ${err}`);
  }
  return res.json();
}

export async function getTrace(sessionId: string): Promise<TraceStep[]> {
  const res = await fetch(`${API_BASE}/trace/${sessionId}`, { cache: 'no-store' });
  if (!res.ok) {
    const err = await res.text();
    throw new Error(`Trace fetch failed: ${err}`);
  }
  return res.json();
}
