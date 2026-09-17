'use client';

import { useState } from 'react';
import { Layers, ShieldCheck, Database, CheckCircle2, ExternalLink, Cpu } from 'lucide-react';

interface DiagramDoc {
  id: string;
  title: string;
  subtitle: string;
  file: string;
  icon: any;
  summary: string;
  keyPoints: string[];
}

const DIAGRAMS: DiagramDoc[] = [
  {
    id: 'rag-flow',
    title: '1. Agentic RAG Pipeline',
    subtitle: '10-Node LangGraph StateGraph with conditional routing',
    file: '/diagrams/01-agentic-rag-flow.svg',
    icon: Layers,
    summary:
      'Unlike naive single-prompt RAG that struggles with cross-domain queries, PulseAgent uses query decomposition to split queries into atomic questions, fetching evidence concurrently across Notion, Gmail, and Jira.',
    keyPoints: [
      'Decomposition node uses Gemini 3.6 Flash in JSON mode to dispatch 2–5 sub-questions.',
      'Parallel retrieval executes across MCP tool adapters with in-memory caching.',
      'StateGraph passes immutable state containing query, sub-questions, evidence, and traces.',
    ],
  },
  {
    id: 'threat-model',
    title: '2. Untrusted Data Boundary',
    subtitle: 'Security boundary isolating third-party SaaS content',
    file: '/diagrams/02-threat-model.svg',
    icon: ShieldCheck,
    summary:
      'All data retrieved from emails, Jira tickets, and Notion documents is treated strictly as untrusted data content. Prompt injection strings inside SaaS documents are safely neutralized.',
    keyPoints: [
      'Evidence snippets cannot execute commands or alter system instructions.',
      'Permalinks and IDs are preserved while free-text undergoes security sanitization.',
      'Defense-in-depth ensures prompt escapes are isolated before synthesis.',
    ],
  },
  {
    id: 'guardrails',
    title: '3. 5-Stage Guardrail Flow',
    subtitle: 'Pre-execution, mid-pipeline, and post-synthesis defenses',
    file: '/diagrams/03-guardrail-flow.svg',
    icon: Cpu,
    summary:
      'PulseAgent implements 5 distinct guardrail nodes: Input Jailbreak Filter, Regex PII Redaction, Groq Citation Entailment, Pydantic Schema Validation, and Permission Gate.',
    keyPoints: [
      'Input Guardrail: Groq fast model flags jailbreaks with zero latency penalty.',
      'PII Redaction: High-throughput pattern scrubber replaces SSNs, emails, and phone numbers.',
      'Citation Entailment: Verifies that every synthesized claim [1], [2] is factually grounded.',
      'Permission Gate: Enforces Human-in-the-Loop authorization for high-impact SaaS actions.',
    ],
  },
  {
    id: 'eval-ci',
    title: '4. CI Quality Gates & Eval Suite',
    subtitle: 'Automated 95-case evaluation matrix running on GitHub Actions',
    file: '/diagrams/04-eval-ci-metrics.svg',
    icon: CheckCircle2,
    summary:
      'Every pull request runs eval/runner.py in CI mode against 5 test buckets (Normal, Edge Cases, Adversarial, Missing Data, Tool Failures) guaranteeing 100% test pass rate.',
    keyPoints: [
      'Evaluates 4 core metrics: Accuracy (100%), Refusal Rate, Latency (avg ~60ms), Tokens.',
      'Automated shields.io badge generation for README showcase.',
      'PR comment bot posts regression summaries on every commit.',
    ],
  },
];

export default function ArchitecturePage() {
  const [activeTab, setActiveTab] = useState(DIAGRAMS[0].id);
  const activeDiagram = DIAGRAMS.find((d) => d.id === activeTab) || DIAGRAMS[0];

  return (
    <div className="max-w-5xl mx-auto px-4 py-8 flex-1 w-full">
      {/* Header */}
      <div className="pb-6 border-b border-slate-200 mb-8">
        <h1 className="text-3xl font-bold text-slate-900 tracking-tight">System Architecture & Design</h1>
        <p className="text-sm text-slate-600 mt-1">
          Visualizing the multi-hop Agentic RAG state graph, security boundary, guardrails, and CI verification pipeline.
        </p>
      </div>

      {/* Tabs */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-2 mb-8">
        {DIAGRAMS.map((item) => {
          const Icon = item.icon;
          const isActive = item.id === activeTab;

          return (
            <button
              key={item.id}
              onClick={() => setActiveTab(item.id)}
              className={`p-3.5 rounded-xl border text-left transition-all ${
                isActive
                  ? 'bg-sky-50 border-sky-300 ring-2 ring-sky-200 shadow-xs'
                  : 'bg-white border-slate-200 hover:bg-slate-50 text-slate-700'
              }`}
            >
              <div className="flex items-center gap-2 mb-1">
                <Icon className={`w-4 h-4 ${isActive ? 'text-sky-600' : 'text-slate-500'}`} />
                <span className={`text-xs font-bold ${isActive ? 'text-sky-900' : 'text-slate-800'}`}>
                  {item.title}
                </span>
              </div>
              <p className="text-[11px] text-slate-500 line-clamp-1">{item.subtitle}</p>
            </button>
          );
        })}
      </div>

      {/* Active Diagram Display Card */}
      <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm mb-8">
        <div className="flex flex-wrap items-center justify-between gap-4 pb-4 border-b border-slate-100 mb-6">
          <div>
            <h2 className="text-xl font-bold text-slate-900">{activeDiagram.title}</h2>
            <p className="text-xs text-slate-500">{activeDiagram.subtitle}</p>
          </div>
          <a
            href={activeDiagram.file}
            target="_blank"
            rel="noreferrer"
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-slate-200 hover:bg-slate-50 text-xs font-semibold text-slate-700 transition-colors shadow-xs"
          >
            Open Full SVG <ExternalLink className="w-3.5 h-3.5" />
          </a>
        </div>

        {/* SVG Render Container */}
        <div className="p-4 bg-slate-50/50 rounded-xl border border-slate-100 flex items-center justify-center overflow-x-auto min-h-[360px]">
          <img
            src={activeDiagram.file}
            alt={activeDiagram.title}
            className="max-w-full h-auto object-contain rounded-lg shadow-xs"
          />
        </div>

        {/* Explanation & Key Architectural Decisions */}
        <div className="mt-6 pt-6 border-t border-slate-100 grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="md:col-span-1">
            <h4 className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-2">
              Architecture Rationale
            </h4>
            <p className="text-xs text-slate-700 leading-relaxed">
              {activeDiagram.summary}
            </p>
          </div>

          <div className="md:col-span-2">
            <h4 className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-2">
              Technical Implementation
            </h4>
            <ul className="space-y-2">
              {activeDiagram.keyPoints.map((pt, pIdx) => (
                <li key={pIdx} className="text-xs text-slate-700 flex items-start gap-2">
                  <span className="text-sky-600 font-bold select-none">•</span>
                  <span>{pt}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}
