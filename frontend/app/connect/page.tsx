'use client';

import { useState, useEffect } from 'react';
import { Mail, FileText, CheckCircle2, AlertCircle, ExternalLink } from 'lucide-react';

interface Integration {
  id: string;
  name: string;
  description: string;
  icon: string;
  authUrl: string;
  connected: boolean;
}

export default function ConnectPage() {
  const [integrations, setIntegrations] = useState<Integration[]>([
    {
      id: 'notion',
      name: 'Notion',
      description: 'Search workspaces, documents, notes, and task databases.',
      icon: 'file-text',
      authUrl: 'http://localhost:8000/auth/notion/login',
      connected: false,
    },
    {
      id: 'gmail',
      name: 'Gmail',
      description: 'Search threads, emails, project communications, and updates.',
      icon: 'mail',
      authUrl: 'http://localhost:8000/auth/gmail/login',
      connected: false,
    },
    {
      id: 'jira',
      name: 'Atlassian Jira',
      description: 'Track issues, tickets, sprint goals, bugs, and project blockers.',
      icon: 'check-square',
      authUrl: 'http://localhost:8000/auth/jira/login',
      connected: false,
    },
  ]);

  useEffect(() => {
    // Check connection status from backend
    fetch('http://localhost:8000/auth/status')
      .then((res) => (res.ok ? res.json() : null))
      .then((data) => {
        if (data && data.providers) {
          setIntegrations((prev) =>
            prev.map((item) => ({
              ...item,
              connected: Boolean(data.providers[item.id]),
            }))
          );
        }
      })
      .catch(() => {
        // Dev fallback
      });
  }, []);

  return (
    <div className="max-w-4xl mx-auto px-4 py-8 flex-1 w-full">
      <div className="pb-6 border-b border-slate-200 mb-8">
        <h1 className="text-2xl font-bold text-slate-900">SaaS Integrations</h1>
        <p className="text-sm text-slate-600 mt-1">
          Connect your live personal or workspace accounts via OAuth 2.0. In development or CI mode, PulseAgent falls back to fixture mocks automatically.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {integrations.map((item) => (
          <div
            key={item.id}
            className="bg-white border border-slate-200 rounded-xl p-6 flex flex-col justify-between shadow-sm"
          >
            <div>
              <div className="flex items-center justify-between mb-4">
                <div className="w-10 h-10 rounded-lg bg-slate-100 flex items-center justify-center font-bold text-slate-700">
                  {item.name[0]}
                </div>
                {item.connected ? (
                  <span className="inline-flex items-center gap-1 text-xs font-semibold text-emerald-600 bg-emerald-50 px-2 py-0.5 rounded-full">
                    <CheckCircle2 className="w-3.5 h-3.5" /> Connected
                  </span>
                ) : (
                  <span className="inline-flex items-center gap-1 text-xs font-medium text-slate-500 bg-slate-100 px-2 py-0.5 rounded-full">
                    Not connected
                  </span>
                )}
              </div>

              <h3 className="font-bold text-slate-900 mb-1">{item.name}</h3>
              <p className="text-xs text-slate-600 leading-relaxed mb-6">
                {item.description}
              </p>
            </div>

            <a
              href={item.authUrl}
              className={`w-full py-2 px-3 rounded-lg text-xs font-semibold text-center transition-colors inline-flex items-center justify-center gap-1.5 ${
                item.connected
                  ? 'bg-slate-100 hover:bg-slate-200 text-slate-700'
                  : 'bg-sky-600 hover:bg-sky-700 text-white'
              }`}
            >
              {item.connected ? 'Reconnect' : 'Connect Account'} <ExternalLink className="w-3 h-3" />
            </a>
          </div>
        ))}
      </div>
    </div>
  );
}
