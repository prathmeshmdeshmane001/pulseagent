import type { Metadata } from 'next';
import Link from 'next/link';
import './globals.css';

export const metadata: Metadata = {
  title: 'PulseAgent — Agentic RAG Assistant',
  description: 'Agentic RAG assistant over Notion, Gmail, and Jira with guardrails, memory, and observability',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="font-sans antialiased text-slate-900 min-h-screen flex flex-col">
        <header className="border-b border-slate-200 bg-white/80 backdrop-blur sticky top-0 z-50">
          <div className="max-w-6xl mx-auto px-4 h-16 flex items-center justify-between">
            <Link href="/" className="flex items-center gap-2 font-bold text-xl text-slate-900 tracking-tight">
              <span className="w-8 h-8 rounded-lg bg-sky-600 text-white flex items-center justify-center font-black text-lg">P</span>
              <span>Pulse<span className="text-sky-600">Agent</span></span>
            </Link>
            <nav className="flex items-center gap-5 text-sm font-medium text-slate-600">
              <Link href="/chat" className="hover:text-sky-600 transition-colors">Chat</Link>
              <Link href="/trace" className="hover:text-sky-600 transition-colors">Trace</Link>
              <Link href="/approvals" className="hover:text-sky-600 transition-colors flex items-center gap-1">
                Approvals
                <span className="w-1.5 h-1.5 rounded-full bg-amber-500" />
              </Link>
              <Link href="/architecture" className="hover:text-sky-600 transition-colors">Architecture</Link>
              <Link href="/connect" className="hover:text-sky-600 transition-colors">Integrations</Link>
              <a
                href={process.env.NEXT_PUBLIC_BACKEND_URL ? `${process.env.NEXT_PUBLIC_BACKEND_URL}/docs` : 'http://localhost:8000/docs'}
                target="_blank"
                rel="noreferrer"
                className="text-xs px-2.5 py-1 rounded-md bg-slate-100 hover:bg-slate-200 text-slate-700 font-mono transition-colors"
              >
                API Docs ↗
              </a>
            </nav>
          </div>
        </header>
        <main className="flex-1 flex flex-col">{children}</main>
        <footer className="border-t border-slate-200 py-6 text-center text-xs text-slate-500 bg-slate-50">
          <p>PulseAgent — Built with LangGraph, Gemini, Groq, and FastAPI on a $0 Stack.</p>
        </footer>
      </body>
    </html>
  );
}
