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

  const [bannerDismissed, setBannerDismissed] = useState(false);
  const isNotionConnected = Boolean(integrations.find((i) => i.id === 'notion')?.connected);
  const isJiraConnected = Boolean(integrations.find((i) => i.id === 'jira')?.connected);
  const isGmailConnected = Boolean(integrations.find((i) => i.id === 'gmail')?.connected);

  const dismissBanner = () => {
    setBannerDismissed(true);
    if (typeof window !== 'undefined') {
      window.history.replaceState({}, '', window.location.pathname);
    }
  };

  return (
    <div className="max-w-4xl mx-auto px-4 py-8 flex-1 w-full">
      <div className="pb-6 border-b border-slate-200 mb-8">
        <h1 className="text-2xl font-bold text-slate-900">SaaS Integrations</h1>
        <p className="text-sm text-slate-600 mt-1">
          Connect your live personal or workspace accounts via OAuth 2.0. In development or CI mode, PulseAgent falls back to fixture mocks automatically.
        </p>
      </div>

      {/* OAuth Notification Banners */}
      {!bannerDismissed && (isNotionConnected || status === 'notion_connected') && (
        <div className="mb-6 p-4 rounded-xl bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs flex items-center justify-between shadow-xs">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
            <span>
              <strong>Notion Workspace Connected!</strong> PulseAgent has active access to search your Notion pages, notes, and task lists live in Chat.
            </span>
          </div>
          <button
            onClick={dismissBanner}
            className="text-emerald-700 hover:text-emerald-900 font-bold ml-4 text-sm"
            aria-label="Dismiss banner"
          >
            ✕
          </button>
        </div>
      )}

      {!bannerDismissed && !isNotionConnected && error === 'notion_auth_failed' && (
        <div className="mb-6 p-4 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 text-xs flex items-center justify-between shadow-xs">
          <div className="flex items-center gap-2">
            <XCircle className="w-4 h-4 text-rose-600 shrink-0" />
            <span>
              <strong>Authentication Failed:</strong> Notion OAuth authorization code exchange encountered an error. Please ensure the redirect URI matches <code>http://localhost:8000/auth/notion/callback</code> in your Notion Integration settings.
            </span>
          </div>
          <button
            onClick={dismissBanner}
            className="text-rose-700 hover:text-rose-900 font-bold ml-4 text-sm"
            aria-label="Dismiss banner"
          >
            ✕
          </button>
        </div>
      )}

      {!bannerDismissed && status === 'missing_notion_client_id' && (
        <div className="mb-6 p-4 rounded-xl bg-amber-50 border border-amber-200 text-amber-800 text-xs flex items-center justify-between shadow-xs">
          <div className="flex items-center gap-2">
            <AlertCircle className="w-4 h-4 text-amber-600 shrink-0" />
            <span>
              <strong>Configuration Notice:</strong> <code>NOTION_OAUTH_CLIENT_ID</code> is not set in your <code>.env</code> file.
            </span>
          </div>
          <button
            onClick={dismissBanner}
            className="text-amber-700 hover:text-amber-900 font-bold ml-4 text-sm"
            aria-label="Dismiss banner"
          >
            ✕
          </button>
        </div>
      )}

      {/* Jira Notification Banners */}
      {!bannerDismissed && (isJiraConnected || status === 'jira_connected') && (
        <div className="mb-6 p-4 rounded-xl bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs flex items-center justify-between shadow-xs">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
            <span>
              <strong>Jira Workspace Connected!</strong> PulseAgent has active access to search your Jira issues, sprint tasks, and blockers live in Chat.
            </span>
          </div>
          <button
            onClick={dismissBanner}
            className="text-emerald-700 hover:text-emerald-900 font-bold ml-4 text-sm"
            aria-label="Dismiss banner"
          >
            ✕
          </button>
        </div>
      )}

      {!bannerDismissed && !isJiraConnected && error === 'jira_auth_failed' && (
        <div className="mb-6 p-4 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 text-xs flex items-center justify-between shadow-xs">
          <div className="flex items-center gap-2">
            <XCircle className="w-4 h-4 text-rose-600 shrink-0" />
            <span>
              <strong>Jira Authentication Failed:</strong> Please verify that Callback URL in Atlassian Developer Console is set to <code>http://localhost:8000/auth/jira/callback</code> and Classic Jira scopes (<code>read:jira-work read:jira-user offline_access</code>) are enabled under Permissions.
            </span>
          </div>
          <button
            onClick={dismissBanner}
            className="text-rose-700 hover:text-rose-900 font-bold ml-4 text-sm"
            aria-label="Dismiss banner"
          >
            ✕
          </button>
        </div>
      )}

      {!bannerDismissed && status === 'missing_jira_client_id' && (
        <div className="mb-6 p-4 rounded-xl bg-amber-50 border border-amber-200 text-amber-800 text-xs flex items-center justify-between shadow-xs">
          <div className="flex items-center gap-2">
            <AlertCircle className="w-4 h-4 text-amber-600 shrink-0" />
            <span>
              <strong>Configuration Notice:</strong> <code>JIRA_OAUTH_CLIENT_ID</code> is not set in your <code>.env</code> file.
            </span>
          </div>
          <button
            onClick={dismissBanner}
            className="text-amber-700 hover:text-amber-900 font-bold ml-4 text-sm"
            aria-label="Dismiss banner"
          >
            ✕
          </button>
        </div>
      )}

      {/* Gmail Notification Banners */}
      {!bannerDismissed && (isGmailConnected || status === 'gmail_connected') && (
        <div className="mb-6 p-4 rounded-xl bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs flex items-center justify-between shadow-xs">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
            <span>
              <strong>Gmail Account Connected!</strong> PulseAgent has active access to search your Gmail threads and inbox updates live in Chat.
            </span>
          </div>
          <button
            onClick={dismissBanner}
            className="text-emerald-700 hover:text-emerald-900 font-bold ml-4 text-sm"
            aria-label="Dismiss banner"
          >
            ✕
          </button>
        </div>
      )}

      {!bannerDismissed && !isGmailConnected && error === 'gmail_auth_failed' && (
        <div className="mb-6 p-4 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 text-xs flex items-center justify-between shadow-xs">
          <div className="flex items-center gap-2">
            <XCircle className="w-4 h-4 text-rose-600 shrink-0" />
            <span>
              <strong>Gmail Authentication Failed:</strong> Please verify that Authorized redirect URIs in Google Cloud Console matches <code>http://localhost:8000/auth/gmail/callback</code> and your account is added under OAuth Consent Screen &gt; Test Users.
            </span>
          </div>
          <button
            onClick={dismissBanner}
            className="text-rose-700 hover:text-rose-900 font-bold ml-4 text-sm"
            aria-label="Dismiss banner"
          >
            ✕
          </button>
        </div>
      )}

      {!bannerDismissed && status === 'missing_google_client_id' && (
        <div className="mb-6 p-4 rounded-xl bg-amber-50 border border-amber-200 text-amber-800 text-xs flex items-center justify-between shadow-xs">
          <div className="flex items-center gap-2">
            <AlertCircle className="w-4 h-4 text-amber-600 shrink-0" />
            <span>
              <strong>Configuration Notice:</strong> <code>GOOGLE_OAUTH_CLIENT_ID</code> is not set in your <code>.env</code> file.
            </span>
          </div>
          <button
            onClick={dismissBanner}
            className="text-amber-700 hover:text-amber-900 font-bold ml-4 text-sm"
            aria-label="Dismiss banner"
          >
            ✕
          </button>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {integrations.map((item) => (
          <div
            key={item.id}
            className="bg-white border border-slate-200 rounded-xl p-6 flex flex-col justify-between shadow-sm hover:border-slate-300 transition-colors"
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

            <div className="flex flex-col gap-2">
              {item.connected && (
                <a
                  href="/chat"
                  className="w-full py-2 px-3 rounded-lg text-xs font-semibold text-center bg-emerald-600 hover:bg-emerald-700 text-white transition-colors inline-flex items-center justify-center gap-1.5"
                >
                  Query in Chat →
                </a>
              )}
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
