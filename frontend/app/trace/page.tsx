'use client';

import { useState, useEffect, Suspense } from 'react';
import { useSearchParams } from 'next/navigation';
import { Search, Clock, Cpu, ArrowLeft, CheckCircle2, Zap } from 'lucide-react';
import Link from 'next/link';
import { getTrace, getRecentTraceSessions, TraceStep } from '@/lib/api';

function TraceContent() {
  const searchParams = useSearchParams();
  const initialSession = searchParams.get('session_id') || '';
  const [sessionId, setSessionId] = useState(initialSession);
  const [steps, setSteps] = useState<TraceStep[]>([]);
  const [loading, setLoading] = useState(false);
  const [searched, setSearched] = useState(false);
  const [recentSessions, setRecentSessions] = useState<string[]>([]);

  async function loadTraceForSession(id: string) {
    if (!id.trim()) return;
    setLoading(true);
    setSearched(true);
    try {
      const data = await getTrace(id.trim());
      setSteps(data);
    } catch (err: any) {
      console.error(err);
      setSteps([]);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    getRecentTraceSessions().then((sessions) => {
      setRecentSessions(sessions);
    });
  }, []);

  useEffect(() => {
    if (initialSession) {
      setSessionId(initialSession);
      loadTraceForSession(initialSession);
    }
  }, [initialSession]);

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    loadTraceForSession(sessionId);
  }

  function handleSelectRecent(id: string) {
    setSessionId(id);
    loadTraceForSession(id);
    if (typeof window !== 'undefined') {
      window.history.replaceState({}, '', `/trace?session_id=${id}`);
    }
  }

  const totalLatency = steps.reduce((sum, s) => sum + (s.latency_ms || 0), 0);
  const totalTokens = steps.reduce((sum, s) => sum + (s.tokens_used || 0), 0);

  return (
    <div className="max-w-4xl mx-auto px-4 py-8 flex-1 w-full">
      <div className="flex items-center justify-between pb-6 border-b border-slate-200 mb-8">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Execution Trace Timeline</h1>
          <p className="text-sm text-slate-600 mt-1">
            Inspect node-by-node execution, latency, token usage, and guardrail decisions.
          </p>
        </div>
        <Link
          href="/chat"
          className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-slate-200 text-xs font-semibold text-slate-700 hover:bg-slate-50 transition-colors"
        >
          <ArrowLeft className="w-3.5 h-3.5" /> Back to Chat
        </Link>
      </div>

      <form onSubmit={handleSubmit} className="flex gap-3 mb-4">
        <div className="relative flex-1">
          <Search className="w-4 h-4 absolute left-3.5 top-3.5 text-slate-400" />
          <input
            type="text"
            value={sessionId}
            onChange={(e) => setSessionId(e.target.value)}
            placeholder="Enter Session ID (e.g. test_triple_connect, sess_xyz)..."
            className="w-full pl-10 pr-4 py-2.5 rounded-lg border border-slate-200 bg-white text-sm outline-none focus:border-sky-500 font-mono"
          />
        </div>
        <button
          type="submit"
          disabled={loading || !sessionId.trim()}
          className="px-5 py-2.5 rounded-lg bg-sky-600 hover:bg-sky-700 disabled:opacity-50 text-white text-sm font-medium transition-colors"
        >
          {loading ? 'Fetching...' : 'Load Trace'}
        </button>
      </form>

      {/* Quick Pick Recent Sessions */}
      {recentSessions.length > 0 && (
        <div className="flex flex-wrap items-center gap-2 mb-8 text-xs text-slate-500">
          <span className="font-semibold text-slate-600">Recent Sessions:</span>
          {recentSessions.map((s) => (
            <button
              key={s}
              type="button"
              onClick={() => handleSelectRecent(s)}
              className={`font-mono px-2.5 py-1 rounded-md border transition-colors ${
                sessionId === s
                  ? 'bg-sky-50 border-sky-300 text-sky-700 font-semibold'
                  : 'bg-white border-slate-200 hover:border-slate-300 text-slate-700'
              }`}
            >
              {s}
            </button>
          ))}
        </div>
      )}

      {/* Summary Metrics Cards */}
      {steps.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
          <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-sm">
            <span className="text-slate-500 text-xs font-semibold uppercase tracking-wider">Total Pipeline Latency</span>
            <div className="text-2xl font-bold text-slate-900 mt-1 flex items-center gap-2">
              <Clock className="w-5 h-5 text-sky-600" /> {totalLatency} ms
            </div>
          </div>
          <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-sm">
            <span className="text-slate-500 text-xs font-semibold uppercase tracking-wider">Total LLM Tokens</span>
            <div className="text-2xl font-bold text-slate-900 mt-1 flex items-center gap-2">
              <Cpu className="w-5 h-5 text-indigo-600" /> {totalTokens.toLocaleString()} tokens
            </div>
          </div>
          <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-sm">
            <span className="text-slate-500 text-xs font-semibold uppercase tracking-wider">Executed DAG Nodes</span>
            <div className="text-2xl font-bold text-slate-900 mt-1 flex items-center gap-2">
              <Zap className="w-5 h-5 text-amber-500" /> {steps.length} nodes
            </div>
          </div>
        </div>
      )}

      {/* Visual LangGraph DAG Strip */}
      {steps.length > 0 && (
        <div className="bg-white border border-slate-200 rounded-xl p-5 mb-8 shadow-sm">
          <div className="flex items-center justify-between mb-3">
            <span className="text-slate-700 text-xs font-bold uppercase tracking-wider">
              LangGraph Execution Flow (DAG)
            </span>
            <span className="text-xs text-emerald-600 font-semibold inline-flex items-center gap-1">
              <CheckCircle2 className="w-3.5 h-3.5" /> All Nodes Completed
            </span>
          </div>
          <div className="flex flex-wrap items-center gap-2 overflow-x-auto pb-1">
            {steps.map((step, idx) => (
              <div key={idx} className="flex items-center gap-2">
                <span className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-mono font-semibold bg-slate-50 border border-slate-200 text-slate-800 shadow-2xs hover:border-sky-500 transition-colors">
                  <span className="w-2 h-2 rounded-full bg-emerald-500"></span>
                  {step.node_name}
                </span>
                {idx < steps.length - 1 && <span className="text-slate-300 font-bold">→</span>}
              </div>
            ))}
          </div>
        </div>
      )}

      {searched && steps.length === 0 && !loading && (
        <div className="p-8 text-center bg-white rounded-xl border border-slate-200 text-slate-500 text-sm">
          No trace steps found for session <code className="font-mono text-slate-700">{sessionId}</code>.
        </div>
      )}

      <div className="relative border-l-2 border-slate-200 ml-4 pl-6 space-y-6">
        {steps.map((step, idx) => (
          <div key={idx} className="relative group">
            {/* Step marker */}
            <div className="absolute -left-[31px] top-1.5 w-4 h-4 rounded-full bg-white border-2 border-sky-600 group-hover:bg-sky-600 transition-colors" />

            <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm">
              <div className="flex flex-wrap items-center justify-between gap-2 mb-2">
                <span className="font-mono font-bold text-sm text-slate-900 px-2 py-0.5 rounded bg-slate-100 border border-slate-200">
                  {step.node_name}
                </span>
                <div className="flex items-center gap-4 text-xs text-slate-500 font-mono">
                  <span className="inline-flex items-center gap-1">
                    <Clock className="w-3.5 h-3.5" />
                    {step.latency_ms} ms
                  </span>
                  <span className="inline-flex items-center gap-1">
                    <Cpu className="w-3.5 h-3.5" />
                    {step.tokens_used} tokens
                  </span>
                </div>
              </div>

              <div className="space-y-2 mt-3 text-xs">
                <div>
                  <span className="font-semibold text-slate-500 uppercase tracking-wide text-[10px]">
                    Input Summary
                  </span>
                  <div className="mt-1 p-2 rounded bg-slate-50 text-slate-700 font-mono">
                    {step.input_summary}
                  </div>
                </div>
                <div>
                  <span className="font-semibold text-slate-500 uppercase tracking-wide text-[10px]">
                    Output Summary
                  </span>
                  <div className="mt-1 p-2 rounded bg-slate-50 text-slate-700 font-mono whitespace-pre-wrap">
                    {step.output_summary}
                  </div>
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

export default function TracePage() {
  return (
    <Suspense fallback={<div className="p-8 text-center text-slate-500">Loading trace timeline...</div>}>
      <TraceContent />
    </Suspense>
  );
}
