'use client';

import { useState, useEffect, Suspense } from 'react';
import { useSearchParams } from 'next/navigation';
import { Mail, FileText, CheckCircle2, AlertCircle, ExternalLink, ShieldCheck, XCircle } from 'lucide-react';
import { API_BASE } from '@/lib/api';

interface Integration {
  id: string;
  name: string;
  description: string;
  icon: string;
  authUrl: string;
  connected: boolean;
}

function ConnectContent() {
  const searchParams = useSearchParams();
  const status = searchParams.get('status');
  const error = searchParams.get('error');

  const [integrations, setIntegrations] = useState<Integration[]>([
    {
      id: 'notion',
      name: 'Notion',
      description: 'Search workspaces, documents, notes, and task databases.',
      icon: 'file-text',
      authUrl: `${API_BASE}/auth/notion/login`,
      connected: false,
    },
    {
      id: 'gmail',
      name: 'Gmail',
      description: 'Search threads, emails, project communications, and updates.',
      icon: 'mail',
      authUrl: `${API_BASE}/auth/gmail/login`,
      connected: false,
    },
    {
      id: 'jira',
      name: 'Atlassian Jira',
      description: 'Track issues, tickets, sprint goals, bugs, and project blockers.',
      icon: 'check-square',
      authUrl: `${API_BASE}/auth/jira/login`,
      connected: false,
    },
  ]);

  useEffect(() => {
    // Check connection status from backend
    fetch(`${API_BASE}/auth/status`)
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
  }, [status]);

  return (
    <div className="max-w-4xl mx-auto px-4 py-8 flex-1 w-full">
      <div className="pb-6 border-b border-slate-200 mb-8">
        <h1 className="text-2xl font-bold text-slate-900">SaaS Integrations</h1>
        <p className="text-sm text-slate-600 mt-1">
          Connect your live personal or workspace accounts via OAuth 2.0. In development or CI mode, PulseAgent falls back to fixture mocks automatically.
        </p>
      </div>

      {/* OAuth Notification Banners */}
      {status === 'notion_connected' && (
        <div className="mb-6 p-4 rounded-xl bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs flex items-center gap-2 shadow-xs">
          <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
          <span>
            <strong>Success!</strong> Your Notion workspace has been authorized and connected to PulseAgent.
          </span>
        </div>
      )}

      {error === 'notion_auth_failed' && (
        <div className="mb-6 p-4 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 text-xs flex items-center gap-2 shadow-xs">
          <XCircle className="w-4 h-4 text-rose-600 shrink-0" />
          <span>
            <strong>Authentication Failed:</strong> Notion OAuth authorization code exchange encountered an error. Please ensure the redirect URI matches <code>http://localhost:8000/auth/notion/callback</code> in your Notion Integration settings.
          </span>
        </div>
      )}

      {status === 'missing_notion_client_id' && (
        <div className="mb-6 p-4 rounded-xl bg-amber-50 border border-amber-200 text-amber-800 text-xs flex items-center gap-2 shadow-xs">
          <AlertCircle className="w-4 h-4 text-amber-600 shrink-0" />
          <span>
            <strong>Configuration Notice:</strong> <code>NOTION_OAUTH_CLIENT_ID</code> is not set in your <code>.env</code> file.
          </span>
        </div>
      )}

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
                  <span className="inline-flex items-center gap-1 text-xs font-semibold text-emerald-600 bg-emerald-50 px-2 py-0.5 rounded-full border border-emerald-200">
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

export default function ConnectPage() {
  return (
    <Suspense fallback={<div className="p-8 text-center text-slate-500">Loading integrations...</div>}>
      <ConnectContent />
    </Suspense>
  );
}
