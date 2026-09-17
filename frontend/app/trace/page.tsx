'use client';

import { useState } from 'react';
import { Search, Clock, Cpu, ArrowDown, ExternalLink } from 'lucide-react';
import { getTrace, TraceStep } from '@/lib/api';

export default function TracePage() {
  const [sessionId, setSessionId] = useState('');
  const [steps, setSteps] = useState<TraceStep[]>([]);
  const [loading, setLoading] = useState(false);
  const [searched, setSearched] = useState(false);

  async function fetchTrace(e?: React.FormEvent) {
    if (e) e.preventDefault();
    if (!sessionId.trim()) return;
    setLoading(true);
    setSearched(true);
    try {
      const data = await getTrace(sessionId.trim());
      setSteps(data);
    } catch (err: any) {
      console.error(err);
      setSteps([]);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="max-w-4xl mx-auto px-4 py-8 flex-1 w-full">
      <div className="pb-6 border-b border-slate-200 mb-8">
        <h1 className="text-2xl font-bold text-slate-900">Execution Trace Timeline</h1>
        <p className="text-sm text-slate-600 mt-1">
          Inspect node-by-node execution, latency, token usage, and guardrail decisions.
        </p>
      </div>

      <form onSubmit={fetchTrace} className="flex gap-3 mb-8">
        <div className="relative flex-1">
          <Search className="w-4 h-4 absolute left-3.5 top-3.5 text-slate-400" />
          <input
            type="text"
            value={sessionId}
            onChange={(e) => setSessionId(e.target.value)}
            placeholder="Enter Session ID (e.g. sess_xyz)..."
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
