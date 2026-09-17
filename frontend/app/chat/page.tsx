'use client';

import { useState } from 'react';
import { Send, Bot, User, Sparkles, ExternalLink, ShieldAlert } from 'lucide-react';
import { sendChatMessage, Evidence } from '@/lib/api';

interface Message {
  role: 'user' | 'assistant';
  content: string;
  evidence?: Evidence[];
}

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([
    {
      role: 'assistant',
      content: 'Hello! I am PulseAgent. Ask me anything about your Notion pages, Gmail threads, or Jira issues.',
    },
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [sessionId] = useState(() => 'sess_' + Math.random().toString(36).substring(2, 9));

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!input.trim() || loading) return;

    const userQuery = input.trim();
    setInput('');
    setMessages((prev) => [...prev, { role: 'user', content: userQuery }]);
    setLoading(true);

    try {
      const res = await sendChatMessage(userQuery, sessionId);
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: res.answer,
          evidence: res.evidence,
        },
      ]);
    } catch (err: any) {
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: `⚠️ Error processing request: ${err.message || 'Check backend connection.'}`,
        },
      ]);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="max-w-4xl mx-auto px-4 py-8 flex flex-col flex-1 w-full">
      <div className="flex items-center justify-between pb-4 border-b border-slate-200 mb-6">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">PulseAgent Chat</h1>
          <p className="text-xs text-slate-500 font-mono">Session ID: {sessionId}</p>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto space-y-6 pb-20">
        {messages.map((m, idx) => (
          <div
            key={idx}
            className={`flex gap-4 ${
              m.role === 'user' ? 'justify-end' : 'justify-start'
            }`}
          >
            {m.role === 'assistant' && (
              <div className="w-8 h-8 rounded-full bg-sky-600 text-white flex items-center justify-center shrink-0">
                <Bot className="w-4 h-4" />
              </div>
            )}
            <div
              className={`max-w-[80%] rounded-2xl px-5 py-3.5 shadow-sm text-sm ${
                m.role === 'user'
                  ? 'bg-sky-600 text-white'
                  : 'bg-white border border-slate-200 text-slate-800'
              }`}
            >
              <div className="whitespace-pre-wrap leading-relaxed">{m.content}</div>

              {m.evidence && m.evidence.length > 0 && (
                <div className="mt-4 pt-3 border-t border-slate-100">
                  <p className="text-xs font-semibold text-slate-500 mb-2 uppercase tracking-wider">
                    Retrieved Evidence ({m.evidence.length})
                  </p>
                  <div className="space-y-2">
                    {m.evidence.map((ev, evIdx) => (
                      <div
                        key={evIdx}
                        className="text-xs bg-slate-50 p-2.5 rounded-lg border border-slate-100 text-slate-700"
                      >
                        <div className="flex items-center justify-between mb-1">
                          <span className="font-semibold text-sky-700 uppercase text-[10px] tracking-wide">
                            [{evIdx + 1}] {ev.source}
                          </span>
                          {ev.permalink && (
                            <a
                              href={ev.permalink}
                              target="_blank"
                              rel="noreferrer"
                              className="inline-flex items-center gap-1 text-slate-400 hover:text-sky-600 font-medium"
                            >
                              Open <ExternalLink className="w-3 h-3" />
                            </a>
                          )}
                        </div>
                        <p className="line-clamp-2 text-slate-600 italic font-mono text-[11px]">
                          "{ev.snippet}"
                        </p>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
            {m.role === 'user' && (
              <div className="w-8 h-8 rounded-full bg-slate-800 text-white flex items-center justify-center shrink-0">
                <User className="w-4 h-4" />
              </div>
            )}
          </div>
        ))}
        {loading && (
          <div className="flex gap-4 items-center text-slate-500 text-sm italic">
            <div className="w-8 h-8 rounded-full bg-sky-100 text-sky-600 flex items-center justify-center animate-pulse">
              <Sparkles className="w-4 h-4" />
            </div>
            <span>PulseAgent is reasoning, querying tools, and validating guardrails...</span>
          </div>
        )}
      </div>

      <form onSubmit={handleSubmit} className="sticky bottom-6 mt-auto">
        <div className="flex gap-2 bg-white rounded-xl shadow-lg border border-slate-200 p-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask about goals, deadlines, Notion docs, or emails..."
            className="flex-1 px-4 py-2 text-sm bg-transparent outline-none text-slate-900 placeholder:text-slate-400"
          />
          <button
            type="submit"
            disabled={loading || !input.trim()}
            className="px-4 py-2 rounded-lg bg-sky-600 hover:bg-sky-700 disabled:opacity-50 text-white font-medium text-sm transition-all inline-flex items-center gap-2"
          >
            <Send className="w-4 h-4" />
          </button>
        </div>
      </form>
    </div>
  );
}
