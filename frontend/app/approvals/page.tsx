'use client';

import { useState, useEffect } from 'react';
import { ShieldCheck, ShieldAlert, CheckCircle2, XCircle, Clock, AlertTriangle, PlusCircle, RefreshCw } from 'lucide-react';
import { ActionItem, getAllActions, approveAction, denyAction, simulateRiskyAction } from '@/lib/api';

export default function ActionsPage() {
  const [actions, setActions] = useState<ActionItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [filter, setFilter] = useState<'all' | 'pending'>('pending');
  const [statusMessage, setStatusMessage] = useState<string | null>(null);

  async function loadActions() {
    setLoading(true);
    try {
      const data = await getAllActions();
      setActions(data);
    } catch (err: any) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadActions();
  }, []);

  async function handleApprove(id: number) {
    try {
      const res = await approveAction(id);
      setStatusMessage(`✅ ${res.message}`);
      loadActions();
      setTimeout(() => setStatusMessage(null), 4000);
    } catch (err: any) {
      setStatusMessage(`❌ Error approving action: ${err.message}`);
    }
  }

  async function handleDeny(id: number) {
    try {
      const res = await denyAction(id);
      setStatusMessage(`🛑 ${res.message}`);
      loadActions();
      setTimeout(() => setStatusMessage(null), 4000);
    } catch (err: any) {
      setStatusMessage(`❌ Error denying action: ${err.message}`);
    }
  }

  async function handleSimulate() {
    try {
      const samples = [
        "Delete Jira issue PROJ-101 (High-Priority Milestone)",
        "Archive Notion database: 'Q3 Product Roadmap'",
        "Send email on user's behalf: 'Weekly Executive Status Update'",
        "Drop table public.credentials in database",
      ];
      const randomSample = samples[Math.floor(Math.random() * samples.length)];
      await simulateRiskyAction(randomSample);
      setStatusMessage(`⚡ Simulated risky action queued for human review!`);
      loadActions();
      setTimeout(() => setStatusMessage(null), 4000);
    } catch (err: any) {
      setStatusMessage(`❌ Simulation failed: ${err.message}`);
    }
  }

  const displayedActions = actions.filter((a) => (filter === 'pending' ? a.status === 'pending' : true));
  const pendingCount = actions.filter((a) => a.status === 'pending').length;

  return (
    <div className="max-w-4xl mx-auto px-4 py-8 flex-1 w-full">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-4 pb-6 border-b border-slate-200 mb-8">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-bold text-slate-900">Permission Gate & Action Approvals</h1>
            <span className="text-[10px] px-2 py-0.5 font-bold uppercase rounded-full bg-amber-50 text-amber-800 border border-amber-200">
              HITL Guardrail
            </span>
          </div>
          <p className="text-sm text-slate-600 mt-1">
            Milestone 5 Guardrail — High-impact or destructive actions require explicit Human-in-the-Loop authorization.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={handleSimulate}
            className="inline-flex items-center gap-1.5 px-3 py-2 rounded-lg bg-sky-600 hover:bg-sky-700 text-xs font-semibold text-white transition-colors shadow-xs"
          >
            <PlusCircle className="w-3.5 h-3.5" />
            Simulate Risky Action
          </button>
          <button
            onClick={loadActions}
            disabled={loading}
            className="inline-flex items-center gap-1.5 px-3 py-2 rounded-lg border border-slate-200 bg-white hover:bg-slate-50 text-xs font-semibold text-slate-700 transition-colors shadow-xs"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </button>
        </div>
      </div>

      {/* Status banner */}
      {statusMessage && (
        <div className="mb-6 p-3.5 rounded-xl bg-slate-900 text-white text-xs font-medium shadow-md transition-all flex items-center justify-between">
          <span>{statusMessage}</span>
          <button onClick={() => setStatusMessage(null)} className="text-slate-400 hover:text-white text-sm ml-2">
            ✕
          </button>
        </div>
      )}

      {/* Filter Tabs */}
      <div className="flex items-center gap-2 mb-6 border-b border-slate-200 pb-2">
        <button
          onClick={() => setFilter('pending')}
          className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all flex items-center gap-2 ${
            filter === 'pending'
              ? 'bg-sky-50 text-sky-700 border border-sky-200'
              : 'text-slate-600 hover:text-slate-900'
          }`}
        >
          Pending Approvals
          {pendingCount > 0 && (
            <span className="px-1.5 py-0.2 rounded-full bg-amber-500 text-white text-[10px] font-bold">
              {pendingCount}
            </span>
          )}
        </button>

        <button
          onClick={() => setFilter('all')}
          className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
            filter === 'all'
              ? 'bg-sky-50 text-sky-700 border border-sky-200'
              : 'text-slate-600 hover:text-slate-900'
          }`}
        >
          All Actions History ({actions.length})
        </button>
      </div>

      {/* Actions List */}
      {displayedActions.length === 0 ? (
        <div className="text-center p-12 bg-white rounded-xl border border-slate-200 shadow-sm">
          <ShieldCheck className="w-10 h-10 text-emerald-500 mx-auto mb-3" />
          <h3 className="text-base font-bold text-slate-800 mb-1">
            {filter === 'pending' ? 'No Actions Pending Approval' : 'No Actions Recorded'}
          </h3>
          <p className="text-xs text-slate-500 max-w-sm mx-auto mb-4">
            All agent execution plans have passed safety gates without requiring human intervention.
          </p>
          <button
            onClick={handleSimulate}
            className="text-xs px-3.5 py-2 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-700 font-semibold transition-colors"
          >
            Trigger a Test Gated Action
          </button>
        </div>
      ) : (
        <div className="space-y-4">
          {displayedActions.map((item) => (
            <div
              key={item.id}
              className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4 transition-all hover:border-slate-300"
            >
              <div className="space-y-1.5 flex-1">
                <div className="flex items-center gap-2">
                  <span className="px-2 py-0.5 rounded text-[11px] font-mono font-bold bg-slate-100 border border-slate-200 text-slate-700">
                    Action #{item.id}
                  </span>
                  <span className="text-[11px] font-mono text-slate-400">
                    Session: {item.session_id}
                  </span>

                  {item.status === 'pending' && (
                    <span className="inline-flex items-center gap-1 text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full bg-amber-50 text-amber-700 border border-amber-200">
                      <Clock className="w-3 h-3" /> Pending Authorization
                    </span>
                  )}
                  {item.status === 'approved' && (
                    <span className="inline-flex items-center gap-1 text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200">
                      <CheckCircle2 className="w-3 h-3" /> Approved
                    </span>
                  )}
                  {item.status === 'denied' && (
                    <span className="inline-flex items-center gap-1 text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full bg-rose-50 text-rose-700 border border-rose-200">
                      <XCircle className="w-3 h-3" /> Denied
                    </span>
                  )}
                </div>

                <div className="flex items-start gap-2 pt-1">
                  <AlertTriangle className="w-4 h-4 text-amber-500 shrink-0 mt-0.5" />
                  <p className="font-semibold text-slate-900 text-sm leading-relaxed">
                    {item.action_description}
                  </p>
                </div>
              </div>

              {/* Action buttons */}
              {item.status === 'pending' ? (
                <div className="flex items-center gap-2 shrink-0">
                  <button
                    onClick={() => handleApprove(item.id)}
                    className="px-4 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white font-semibold text-xs transition-colors shadow-xs flex items-center gap-1.5"
                  >
                    <CheckCircle2 className="w-3.5 h-3.5" /> Approve
                  </button>
                  <button
                    onClick={() => handleDeny(item.id)}
                    className="px-4 py-2 rounded-lg bg-rose-50 hover:bg-rose-100 text-rose-700 border border-rose-200 font-semibold text-xs transition-colors shadow-xs flex items-center gap-1.5"
                  >
                    <XCircle className="w-3.5 h-3.5" /> Deny
                  </button>
                </div>
              ) : (
                <div className="text-xs text-slate-400 font-medium shrink-0">
                  Resolved
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
