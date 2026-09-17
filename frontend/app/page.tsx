import Link from 'next/link';
import { ArrowRight, Bot, ShieldCheck, Database, Activity, Sparkles } from 'lucide-react';

export default function HomePage() {
  return (
    <div className="max-w-5xl mx-auto px-4 py-12 flex flex-col items-center text-center">
      <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-sky-50 text-sky-700 text-xs font-semibold mb-6 border border-sky-100">
        <Sparkles className="w-3.5 h-3.5" />
        Agentic RAG Assistant on a $0 Stack
      </div>
      
      <h1 className="text-4xl md:text-5xl font-extrabold text-slate-900 tracking-tight max-w-3xl mb-4">
        Unified Cross-SaaS Intelligence for Gmail, Notion & Jira
      </h1>
      
      <p className="text-lg text-slate-600 max-w-2xl mb-8">
        PulseAgent decomposes complex queries, queries live SaaS data sources, verifies citations with Groq entailment, safeguards PII, and maintains persistent cross-session memory.
      </p>

      <div className="flex flex-wrap items-center justify-center gap-3 mb-16">
        <Link
          href="/chat"
          className="inline-flex items-center gap-2 px-6 py-3 rounded-lg bg-sky-600 hover:bg-sky-700 text-white font-medium shadow-sm transition-all"
        >
          Open Chat <ArrowRight className="w-4 h-4" />
        </Link>
        <Link
          href="/architecture"
          className="inline-flex items-center gap-2 px-5 py-3 rounded-lg bg-white hover:bg-slate-50 text-slate-700 font-medium border border-slate-200 transition-all shadow-xs"
        >
          Explore Architecture
        </Link>
        <Link
          href="/trace"
          className="inline-flex items-center gap-2 px-5 py-3 rounded-lg bg-white hover:bg-slate-50 text-slate-700 font-medium border border-slate-200 transition-all shadow-xs"
        >
          Inspect Trace Timeline
        </Link>
        <Link
          href="/approvals"
          className="inline-flex items-center gap-2 px-5 py-3 rounded-lg bg-white hover:bg-slate-50 text-slate-700 font-medium border border-slate-200 transition-all shadow-xs"
        >
          Human Approvals
        </Link>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 w-full text-left">
        <div className="p-6 rounded-xl bg-white border border-slate-200 shadow-sm">
          <div className="w-10 h-10 rounded-lg bg-indigo-50 text-indigo-600 flex items-center justify-center mb-4">
            <Bot className="w-5 h-5" />
          </div>
          <h3 className="font-bold text-slate-900 mb-2">LangGraph Multi-Hop</h3>
          <p className="text-sm text-slate-600">
            Decomposes user queries into sub-questions dispatched concurrently across Gmail, Notion, and Jira.
          </p>
        </div>

        <div className="p-6 rounded-xl bg-white border border-slate-200 shadow-sm">
          <div className="w-10 h-10 rounded-lg bg-emerald-50 text-emerald-600 flex items-center justify-center mb-4">
            <ShieldCheck className="w-5 h-5" />
          </div>
          <h3 className="font-bold text-slate-900 mb-2">5-Stage Guardrails</h3>
          <p className="text-sm text-slate-600">
            Input jailbreak classification, Presidio PII anonymization, citation entailment, and risky action approval gates.
          </p>
        </div>

        <div className="p-6 rounded-xl bg-white border border-slate-200 shadow-sm">
          <div className="w-10 h-10 rounded-lg bg-purple-50 text-purple-600 flex items-center justify-center mb-4">
            <Database className="w-5 h-5" />
          </div>
          <h3 className="font-bold text-slate-900 mb-2">Dual-Tier Memory</h3>
          <p className="text-sm text-slate-600">
            Short-term session context coupled with long-term vector semantic recall for durable facts across sessions.
          </p>
        </div>
      </div>
    </div>
  );
}
