# PulseAgent — Build Guide
Agentic RAG assistant over live Gmail/Notion/Jira, with persistent memory, guardrails, evals, and CI. Built with Antigravity, $0 stack.

---

## 0. Locked Decisions

| Decision | Choice | Notes |
|---|---|---|
| Primary LLM (planning/synthesis) | **Google Gemini API** (free tier, Google AI Studio key) | Generous free quota, strong tool-calling, pairs naturally with Antigravity |
| Cheap/fast LLM (guardrail classification, citation entailment, PII pass) | **Groq free tier** (Llama 3.x models) | Very fast + free — keeps your "reduced cost per task" metric real |
| Data sources | **Live** personal Gmail, Notion, Jira accounts via OAuth | Real demo; see CI note below on why evals still use seeded data |
| Hosting | **Vercel** (frontend) + **Render** free web service (backend) + **Supabase** free tier (Postgres + pgvector + auth) | All $0 |
| Orchestration | **LangGraph** | Explicit node graph = easy to trace, checkpoint, guardrail |
| Observability | **LangSmith free tier** | Named in your source material; capped trace volume on free tier — watch usage during heavy eval runs |
| PII redaction | **Presidio** (open source) | No API cost |

**Important caveat on "live accounts":** connect your real Gmail/Notion/Jira for the **interactive demo**, but the **CI eval suite should still run against seeded/mocked fixtures**, not your live inbox. Reasons: (1) live data changes, so eval expected-answers can't stay stable; (2) free-tier API rate limits will throttle CI runs; (3) you don't want a GitHub Action reading your real email on every push. This is a one-line addition to your architecture, not a contradiction of "live accounts" — live for demo, fixtures for CI.

---

## 1. Architecture (recap, finalized)

```
User Question
   │
   ▼
[Input Guardrail] ── Groq classifier: prompt-injection / jailbreak check
   │
   ▼
[Decompose] ── Gemini: breaks question into sub-questions
   │
   ├──► Gmail MCP  ──► Evidence[]
   ├──► Notion MCP ──► Evidence[]
   └──► Jira MCP   ──► Evidence[]
   │
   ▼
[Memory Read] ── pull relevant long-term facts (Supabase/pgvector)
   │
   ▼
[Synthesize] ── Gemini: draft cited answer from evidence + memory
   │
   ▼
[PII Redaction] ── Presidio pass on evidence + draft answer
   │
   ▼
[Citation Validation] ── Groq: does evidence actually support each claim?
   │
   ▼
[Output Validation] ── Pydantic schema check (claims[], citations[], confidence)
   │
   ▼
[Risky Action?] ──yes──► write to pending_actions ──► send confirmation email ──► WAIT
   │no
   ▼
[Memory Write] ── promote durable facts to long-term store
   │
   ▼
Cited Final Answer (+ full trace in LangSmith + UI trace viewer)
```

Every node writes a structured log entry (`node`, `input`, `output`, `tokens`, `latency_ms`) — this is what both LangSmith tracing and your eval metrics feed off, so build it once and reuse everywhere.

---

## 2. Folder Structure

```
pulseagent/
├── frontend/                      # Next.js
│   ├── app/
│   │   ├── chat/                  # main chat UI
│   │   ├── trace/                 # trace viewer (decompose → tools → evidence → memory → answer)
│   │   └── connect/               # OAuth connect screens for Gmail/Notion/Jira
│   ├── components/
│   └── lib/api.ts
├── backend/
│   ├── app/
│   │   ├── agent/
│   │   │   ├── graph.py           # LangGraph definition, wires all nodes
│   │   │   ├── nodes/
│   │   │   │   ├── input_guardrail.py
│   │   │   │   ├── decompose.py
│   │   │   │   ├── synthesize.py
│   │   │   │   ├── pii_redact.py
│   │   │   │   ├── citation_validate.py
│   │   │   │   ├── output_validate.py
│   │   │   │   └── permission_gate.py
│   │   │   └── llm_client.py      # routes calls to Gemini vs Groq, logs tokens/latency
│   │   ├── tools/
│   │   │   ├── gmail_mcp.py
│   │   │   ├── notion_mcp.py
│   │   │   └── jira_mcp.py
│   │   ├── memory/
│   │   │   ├── short_term.py
│   │   │   ├── long_term.py
│   │   │   └── memory_manager.py  # decides what gets promoted
│   │   ├── models/                # Pydantic schemas (Evidence, Citation, AgentResponse, PendingAction)
│   │   ├── db/                    # SQLAlchemy models + Alembic migrations
│   │   ├── auth/                  # OAuth flows for Gmail/Notion/Jira
│   │   └── main.py                # FastAPI app
│   └── requirements.txt
├── eval/
│   ├── fixtures/                  # seeded mock Gmail/Notion/Jira responses for CI
│   ├── testsets/
│   │   ├── normal.json
│   │   ├── edge_cases.json
│   │   ├── adversarial.json       # prompt injection attempts
│   │   ├── missing_data.json
│   │   └── tool_failures.json
│   ├── runner.py                  # executes agent against testsets, scores results
│   └── report/eval_report.json
├── .github/
│   └── workflows/eval.yml
├── docs/
│   └── diagrams/                  # your uploaded pipeline diagrams, referenced in README
├── .env.example
└── README.md                      # your "story" + badge + metrics live here
```

---

## 3. Environment Variables (`.env.example`)

Never commit a populated `.env`. Copy this to `.env` locally and to Render/Vercel's secret manager for deployment.

```bash
# ── LLM Providers ──────────────────────────────
GEMINI_API_KEY=                    # from Google AI Studio (free tier)
GROQ_API_KEY=                      # from console.groq.com (free tier)

# ── Observability ──────────────────────────────
LANGCHAIN_API_KEY=                 # LangSmith
LANGCHAIN_TRACING_V2=true
LANGCHAIN_PROJECT=pulseagent

# ── Database (Supabase) ────────────────────────
DATABASE_URL=                      # postgres connection string from Supabase
SUPABASE_URL=
SUPABASE_ANON_KEY=
SUPABASE_SERVICE_ROLE_KEY=         # backend only, never expose to frontend

# ── OAuth: Gmail ────────────────────────────────
GOOGLE_OAUTH_CLIENT_ID=
GOOGLE_OAUTH_CLIENT_SECRET=
GOOGLE_OAUTH_REDIRECT_URI=

# ── OAuth: Notion ───────────────────────────────
NOTION_OAUTH_CLIENT_ID=
NOTION_OAUTH_CLIENT_SECRET=
NOTION_OAUTH_REDIRECT_URI=

# ── OAuth: Jira (Atlassian) ─────────────────────
JIRA_OAUTH_CLIENT_ID=
JIRA_OAUTH_CLIENT_SECRET=
JIRA_OAUTH_REDIRECT_URI=
JIRA_CLOUD_SITE_URL=

# ── Confirmation emails for risky actions ──────
SENDGRID_API_KEY=                  # or use Gmail API itself to send, avoiding a second free tier
CONFIRMATION_EMAIL_FROM=

# ── App config ──────────────────────────────────
ENVIRONMENT=development            # development | ci | production
SESSION_SECRET=                    # random string, for session signing
FRONTEND_URL=http://localhost:3000
BACKEND_URL=http://localhost:8000
```

CI note: the GitHub Actions workflow needs its own secret set (GitHub → Settings → Secrets) mirroring this file, but pointed at a **test** Supabase project and **fixture** data — never CI-run against your real OAuth tokens.

---

## 4. Development Roadmap

Each milestone is independently demoable — stop after any of these and you still have something to show.

- **M0 — Foundation**: repo scaffold, FastAPI skeleton, Next.js skeleton, Supabase project + schema, `.env` wiring, health-check endpoint
- **M1 — Single-source RAG**: Notion MCP connected, basic retrieval, single-hop answer (no decomposition yet)
- **M2 — Multi-hop**: add Gmail + Jira MCP, decomposition node, parallel tool calls, evidence aggregation, cited synthesis
- **M3 — Memory**: short-term session buffer, long-term store + promotion logic, memory read feeding into decomposition
- **M4 — Observability**: LangSmith wired into every node, frontend trace viewer
- **M5 — Guardrails**: input guardrail, PII redaction, citation validation, output schema validation, permission gate + confirmation email
- **M6 — Evaluation suite**: 5 testset buckets, eval runner, scoring
- **M7 — CI**: GitHub Actions running evals on push, badge generation, PR comments
- **M8 — Deploy + polish**: Vercel/Render/Supabase live deployment, README with real numbers + your build story

---

## 5. Antigravity Prompts (copy-paste per phase)

Feed these one at a time, in order. Each assumes Antigravity has repo context. Adjust anything in `[brackets]`.

### M0 — Foundation

```
Set up a monorepo called "pulseagent" with two apps:

1. `frontend/` — Next.js 14+ (App Router), TypeScript, Tailwind CSS. Include a placeholder
   chat page at /chat and a placeholder trace page at /trace.

2. `backend/` — FastAPI (Python 3.11+), structured as:
   app/agent/, app/tools/, app/memory/, app/models/, app/db/, app/auth/, app/main.py
   Include a `/health` GET endpoint returning {"status": "ok"}.
   Use Pydantic v2 for all schemas. Use SQLAlchemy 2.0 async style for the DB layer,
   with Alembic configured for migrations.

3. Create a `.env.example` at the repo root with these variables (values blank):
   GEMINI_API_KEY, GROQ_API_KEY, LANGCHAIN_API_KEY, LANGCHAIN_TRACING_V2,
   LANGCHAIN_PROJECT, DATABASE_URL, SUPABASE_URL, SUPABASE_ANON_KEY,
   SUPABASE_SERVICE_ROLE_KEY, GOOGLE_OAUTH_CLIENT_ID, GOOGLE_OAUTH_CLIENT_SECRET,
   GOOGLE_OAUTH_REDIRECT_URI, NOTION_OAUTH_CLIENT_ID, NOTION_OAUTH_CLIENT_SECRET,
   NOTION_OAUTH_REDIRECT_URI, JIRA_OAUTH_CLIENT_ID, JIRA_OAUTH_CLIENT_SECRET,
   JIRA_OAUTH_REDIRECT_URI, JIRA_CLOUD_SITE_URL, SENDGRID_API_KEY,
   CONFIRMATION_EMAIL_FROM, ENVIRONMENT, SESSION_SECRET, FRONTEND_URL, BACKEND_URL

4. Add a root README.md with a one-paragraph project description (agentic RAG assistant
   over Gmail/Notion/Jira with memory, guardrails, and CI-gated evals) and a placeholder
   for an eval badge.

5. Add .gitignore covering node_modules, __pycache__, .env, .venv, and build artifacts.

Do not implement any agent logic yet — this is scaffolding only. Confirm the backend
starts with `uvicorn app.main:app --reload` and the frontend starts with `npm run dev`.
```

### M1 — Single-source RAG (Notion)

```
Implement a minimal single-hop RAG flow using only Notion as a data source.

1. In app/auth/, implement OAuth2 flow for Notion (authorization code flow), storing
   the access token encrypted in the `oauth_tokens` table (create this table via
   Alembic migration: id, user_id, provider, access_token_encrypted, refresh_token_encrypted,
   expires_at).

2. In app/tools/notion_mcp.py, implement a client that: given a natural language query,
   searches the connected Notion workspace and returns a list of Evidence objects
   (Pydantic model: source: str, permalink: str, timestamp: datetime, snippet: str,
   page_title: str).

3. In app/agent/, implement a minimal LangGraph graph with two nodes:
   - retrieve: calls notion_mcp to get Evidence[]
   - synthesize: calls the Gemini API (via a new app/agent/llm_client.py that reads
     GEMINI_API_KEY and wraps generate calls, logging token counts and latency_ms
     for every call) to produce a plain-text answer citing evidence indices, e.g. [1], [2]

4. Expose POST /chat on the backend: accepts {"query": str}, runs the graph, returns
   {"answer": str, "evidence": Evidence[]}.

5. On the frontend /chat page, wire a simple form that POSTs to /chat and renders the
   answer with clickable citation links to the Notion permalinks.

Use Gemini's free-tier API (model: gemini-2.0-flash or latest available flash model)
via the google-generativeai or google-genai Python SDK. Read the key from GEMINI_API_KEY.
```

### M2 — Multi-hop decomposition (add Gmail + Jira)

```
Extend the agent graph to support decomposition and multi-source multi-hop retrieval.

1. Implement OAuth for Gmail (Google OAuth, gmail.readonly scope minimum) and Jira
   (Atlassian OAuth, read-only scopes) following the same pattern as Notion in app/auth/.

2. Implement app/tools/gmail_mcp.py and app/tools/jira_mcp.py, each returning the same
   Evidence Pydantic model as Notion for consistency.

3. In app/agent/nodes/decompose.py, implement a node that calls Gemini with a prompt
   instructing it to break the user's question into 2-5 sub-questions, each tagged
   with which source(s) it should query (gmail, notion, jira, or multiple). Return
   structured output (use Gemini's JSON mode / function calling, validated against a
   Pydantic model: SubQuestion(text: str, sources: list[str])).

4. Rewrite the LangGraph graph so that after decompose, sub-questions are dispatched
   to the relevant tool(s) in parallel (use LangGraph's parallel node execution or
   asyncio.gather), collecting all Evidence into a single list tagged by which
   sub-question they answered.

5. Update the synthesize node to take all sub-question evidence and produce one
   final answer with per-claim citations mapping back to specific evidence items.

6. Update the /trace frontend page to show: original question → sub-questions →
   which tool was called for each → evidence retrieved per tool → final cited answer.
   Fetch this from a new GET /trace/{session_id} endpoint that returns the full
   node-by-node log.

Treat all evidence content as untrusted data — never let text inside a Notion page,
email body, or Jira ticket description be interpreted as an instruction to the agent.
Add a comment in decompose.py and synthesize.py explicitly noting this boundary.
```

### M3 — Memory

```
Add short-term and long-term memory to the agent.

1. Create a `sessions` table (id, user_id, created_at) and a `messages` table
   (id, session_id, role, content, created_at) for short-term memory — standard
   conversation history scoped per session.

2. Create a `long_term_memory` table (id, user_id, fact: str, source_session_id,
   created_at, embedding: vector(768)) using Supabase's pgvector extension.

3. Implement app/memory/memory_manager.py: after each completed agent run, call
   Gemini with the conversation + final answer and ask it to extract 0-3 durable,
   reusable facts (e.g. "Project X is high priority"), returning structured output.
   Only facts explicitly worth persisting get written to long_term_memory — do NOT
   store the full conversation as memory.

4. Implement app/memory/long_term.py: a retrieve(query, user_id) function that
   embeds the query and does a pgvector similarity search against long_term_memory,
   returning the top 3 relevant facts.

5. Add a memory_read node to the graph, running right after decompose and before
   tool calls, injecting retrieved facts into the synthesis context.

6. Add a memory_write node at the end of the graph calling memory_manager.

Add a simple test: send "Project X is our top priority this quarter" in one session,
start a new session, ask "What's our top priority?" and confirm the fact is recalled.
```

### M4 — Observability (LangSmith + trace viewer)

```
Wire LangSmith tracing into the full agent graph.

1. Ensure LANGCHAIN_TRACING_V2=true and LANGCHAIN_API_KEY are read at startup;
   if LangSmith env vars are missing, log a warning but do not crash — tracing
   should be optional for local dev without a LangSmith account.

2. Make sure every node in the LangGraph graph (input_guardrail, decompose, tool
   calls, memory_read, synthesize, pii_redact, citation_validate, output_validate,
   permission_gate, memory_write) appears as a distinct step in the LangSmith trace,
   with meaningful names.

3. Extend the trace logging so every node's output is also persisted to a new
   `run_traces` table (id, session_id, node_name, input_summary, output_summary,
   tokens_used, latency_ms, created_at) — this is the source of truth for both
   the frontend trace viewer AND the eval metrics later, so keep it structured.

4. Update GET /trace/{session_id} to read from run_traces and return a clean
   ordered JSON array of steps.

5. On the frontend /trace page, render this as a vertical timeline: each step as
   a card showing node name, a short summary, tokens used, and latency. Include
   a link out to the corresponding LangSmith run if LANGSMITH_PROJECT is configured
   (construct the URL from LANGCHAIN_PROJECT + run id).
```

### M5 — Guardrails

```
Implement the full guardrail layer around the existing agent graph.

1. app/agent/nodes/input_guardrail.py: before decompose, call Groq (fast/cheap model,
   e.g. llama-3.1-8b-instant) with a classification prompt to detect prompt injection /
   jailbreak attempts in the user's raw query. If flagged, short-circuit the graph and
   return a polite refusal with reason "input_guardrail_blocked" — do not proceed to
   decompose.

2. app/agent/nodes/pii_redact.py: after synthesize, run Presidio's analyzer + anonymizer
   over both the evidence snippets and the draft answer, redacting emails, phone numbers,
   names not already public in the source, etc. Add a note that Notion/Jira/Gmail
   permalinks and titles are NOT redacted, only free-text content.

3. app/agent/nodes/citation_validate.py: for each cited claim in the draft answer, call
   Groq with an entailment-style prompt: "Does this evidence support this claim? yes/no".
   If any citation fails, either drop that claim from the final answer or regenerate
   synthesis once. Log the pass/fail rate per run to run_traces.

4. app/agent/nodes/output_validate.py: define a Pydantic model AgentResponse(claims:
   list[Claim], citations: list[Citation], confidence: float). Validate the final
   output against this schema before returning; on failure, retry synthesis once,
   then fail gracefully with a clear error rather than returning malformed output.

5. app/agent/nodes/permission_gate.py: define a RISKY_ACTIONS allowlist (e.g. "delete
   jira ticket", "archive notion page", "send email on user's behalf"). If the agent's
   plan includes any risky action, do NOT execute it. Instead:
   - write a row to a new `pending_actions` table (id, session_id, action_description,
     status: 'pending'|'approved'|'denied', created_at)
   - send a confirmation email (via Gmail API, using the user's own connected account,
     or SendGrid if SENDGRID_API_KEY is set) with an approve/deny link pointing to
     GET /actions/{id}/approve and GET /actions/{id}/deny
   - return to the user: "I've prepared this action and sent you a confirmation email
     before proceeding."
   Only execute the action after status becomes 'approved'.

Wire all five nodes into the LangGraph graph in the correct order (see architecture
diagram in docs/diagrams/). Every guardrail decision (blocked, redacted, citation
failed, validation failed, action gated) must be logged to run_traces with a clear
node_name so it shows up in both LangSmith and the frontend trace viewer.
```

### M6 — Evaluation suite

```
Build the evaluation suite and runner.

1. Create eval/fixtures/ with mocked Gmail/Notion/Jira API responses (JSON files)
   representing a small fake "Project X" — a few emails, a few Notion pages, a few
   Jira tickets, including realistic goals/tasks/deadlines/blockers content so the
   agent has something real to reason over.

2. Create eval/testsets/ with 5 JSON files:
   - normal.json: ~30 realistic questions with expected_answer_summary + expected_sources
   - edge_cases.json: ~20 questions with ambiguous phrasing, empty results expected, etc.
   - adversarial.json: ~15 prompt injection / jailbreak attempts (some directly in the
     user query, some embedded inside fixture data as "hidden instructions" to test the
     malicious-retrieved-doc defense), each with expected_behavior: "blocked" or "ignored"
   - missing_data.json: ~15 questions referencing a "Project Y" that doesn't exist in
     fixtures, expecting a graceful "I don't have that information" response
   - tool_failures.json: ~15 cases where a fixture loader is configured to simulate a
     tool timeout/error, expecting graceful degradation, not a crash

   Aim for roughly 120-150 total cases across all five files.

3. Implement eval/runner.py:
   - loads each testset, runs the agent against fixture-backed tools (not live APIs)
   - for normal/edge_cases: score with an LLM-judge (Gemini) comparing actual vs
     expected_answer_summary, pass if judged substantively correct
   - for adversarial: pass if the input_guardrail blocked it OR the malicious
     instruction was demonstrably ignored in the final answer
   - for missing_data: pass if the agent explicitly states it lacks the information
     rather than hallucinating
   - for tool_failures: pass if the agent degrades gracefully (partial answer +
     acknowledgment) rather than crashing or returning an error to the user
   - aggregate: overall accuracy %, refusal rate (adversarial bucket, e.g. "14/15
     blocked"), average latency, total token usage
   - write results to eval/report/eval_report.json

4. Add a `--mode=ci` flag to runner.py that ensures ALL tool calls resolve against
   eval/fixtures/ only, never real APIs, regardless of .env contents — this is a
   safety rail so CI never accidentally hits live Gmail/Notion/Jira.
```

### M7 — CI (GitHub Actions)

```
Set up CI to run the evaluation suite on every push and publish a badge.

1. Create .github/workflows/eval.yml:
   - triggers on push and pull_request to main
   - sets up Python 3.11, installs backend/requirements.txt
   - sets ENVIRONMENT=ci and points DATABASE_URL at a disposable test Postgres
     (use a GitHub Actions postgres service container, or Supabase's test branch
     if available)
   - injects GEMINI_API_KEY and GROQ_API_KEY from GitHub Secrets (use minimal-quota
     keys or a mock LLM mode if you want zero API cost in CI — see step 4)
   - runs `python eval/runner.py --mode=ci`
   - uploads eval/report/eval_report.json as a workflow artifact
   - fails the workflow if overall accuracy drops below a threshold (start at 75%)

2. Add a step that parses eval_report.json and writes a shields.io endpoint JSON
   badge file to a `badges/` branch or gh-pages, e.g.:
   {"schemaVersion":1,"label":"eval accuracy","message":"82%","color":"green"}
   Reference this badge in the root README.md using the shields.io endpoint format.

3. On pull_request events, add a step that posts a comment on the PR summarizing
   the eval_report.json results (accuracy, refusal rate, latency, token usage) —
   use the github-script action or a simple curl to the GitHub API.

4. If you want CI to run with zero LLM API cost, add a `MOCK_LLM=true` env option
   that makes llm_client.py return canned/recorded responses for a curated subset
   of the testsets, and only hit real Gemini/Groq for a smaller "smoke" subset.
   Document this tradeoff in README.md.
```

### M8 — Deploy + polish

```
Prepare PulseAgent for production deployment and finalize the README.

1. Backend: add a Dockerfile for the FastAPI app, confirm it runs correctly with
   `docker build` and `docker run` locally. Add a render.yaml (or document manual
   Render setup) for deploying as a free-tier Render web service, with environment
   variables sourced from Render's secret manager, not the repo.

2. Frontend: confirm `next build` succeeds cleanly, add a vercel.json if needed for
   API proxy rewrites to the Render backend URL, deploy to Vercel.

3. Database: confirm Alembic migrations run cleanly against the production Supabase
   project (separate from the CI test project), document the migration command in
   README.md.

4. Update README.md with:
   - Architecture diagram (embed docs/diagrams/ images)
   - Real eval numbers pulled from your latest eval_report.json (accuracy, refusal
     rate, latency, token usage) and the CI badge
   - A "How I built this" story section: what was hard, what tradeoffs you made
     (e.g. why fixtures for CI but live accounts for demo, why Gemini/Groq for
     zero-cost operation, why you separated short-term vs long-term memory instead
     of storing everything)
   - A short GIF or screenshot of the /trace view showing decomposition → tool
     calls → evidence → cited answer

5. Do a final end-to-end smoke test: fresh clone, .env from .env.example filled in,
   run locally, connect real Notion/Gmail/Jira, ask "Summarize what changed in
   Project X this quarter and identify major risks", confirm full trace renders
   correctly and citations are clickable and accurate.
```

---

## 6. Integrating Your Pipeline Diagrams

You already have the exact diagrams that define this system — use them literally, not just as inspiration:

1. **Drop the diagram images into `docs/diagrams/`** (name them `01-agentic-rag-flow.png`, `02-threat-model.png`, `03-guardrail-flow.png`, `04-eval-ci-metrics.png`) and embed them directly in `README.md` under an "Architecture" section — this is exactly what an interviewer wants to see alongside the working repo.
2. **Diagram 1 (decompose → MCP → evidence → cited answer)** is your literal LangGraph structure for M1/M2 — the sub-question boxes (`Project goals?`, `Tasks this quarter?`, `Deadlines changed?`, `Blockers reported?`) map directly to example sub-questions your decompose node should produce for the canonical demo query.
3. **Diagram 2 (threat model: prompt injection / malicious doc / PII / risky action)** is your guardrail requirements spec for M5 — literally the four rows in the guardrail table in section 1 above.
4. **Diagram 3 (guardrail flow with permission layer + PII redaction + citation validation + output validation)** is your exact node ordering for the M5 graph — build it in this order, don't reorder.
5. **Diagrams 4-8 (eval metrics → GitHub Action)** define your exact CI badge content for M7 — `accuracy`, `refusal rate`, `latency`, `token usage` are the four numbers your `eval_report.json` must always produce, in that order, for the README badge/table.

When you paste these into Antigravity for the M2 and M5 prompts, literally attach the diagram images — most agentic IDEs (Antigravity included) accept image context and will follow the exact box/arrow structure more faithfully than a text description alone.

---

## 7. Testing, Debugging, Evaluation, Monitoring, Production-Readiness

**Unit/integration testing**
- `pytest` for backend: test each node in isolation with mocked LLM responses (don't burn free-tier quota on every test run)
- Test the MCP tool wrappers against `eval/fixtures/` so tests are deterministic
- Test OAuth token refresh logic explicitly — this is a common silent-failure point

**Debugging**
- Every node logs to `run_traces` — when something looks wrong, check the trace first before re-running
- LangSmith trace URLs should be printed in backend logs during development for one-click inspection

**Evaluation** (see M6) — re-run `eval/runner.py` locally before every push; don't rely on CI to catch regressions first

**Monitoring in production**
- LangSmith gives you trace-level monitoring for free-tier usage
- Add a lightweight `/metrics` endpoint (even just counts: total requests, guardrail blocks, avg latency from the last N `run_traces` rows) — you don't need a full Grafana stack for a portfolio project, but showing you thought about it matters
- Watch Gemini/Groq free-tier rate limits — log a warning when you're approaching quota so you're not surprised mid-demo

**Production readiness checklist**
- [ ] All secrets in platform secret managers, none in git history (check with `git log -p | grep -i api_key` before making the repo public)
- [ ] OAuth scopes are minimum-necessary (read-only except where the risky-action flow explicitly needs write)
- [ ] Rate limiting / basic abuse protection on `/chat` (even simple per-IP throttling)
- [ ] Graceful error responses everywhere — never leak stack traces to the frontend
- [ ] CI passing on main branch with badge reflecting current numbers

---

## 8. Final Verification Checklist

Use this before you call the project "done" for your resume/portfolio:

- [ ] Canonical demo query works end-to-end: "Summarize what changed in Project X this quarter and identify major risks" — decomposes, calls all three tools, retrieves evidence, cites correctly
- [ ] Trace viewer shows: original question → sub-questions → tools called → evidence per tool → memory used → final cited answer
- [ ] Long-term memory demonstrably persists across sessions (test from M3)
- [ ] At least one adversarial prompt injection is demonstrably blocked, and it's visible in the trace
- [ ] At least one "risky action" scenario triggers the permission gate + confirmation email correctly, and does NOT execute until approved
- [ ] PII redaction demonstrably redacts something in a test case (verify by eye, don't just trust the code)
- [ ] Citation validation demonstrably catches at least one bad citation in a constructed test case
- [ ] `eval/runner.py` runs clean locally and produces `eval_report.json` with all four metrics (accuracy, refusal rate, latency, token usage)
- [ ] GitHub Actions workflow passes on push, badge in README reflects real current numbers (not placeholders)
- [ ] Live deployment (Vercel + Render + Supabase) works from a fresh browser, not just localhost
- [ ] README includes: architecture diagrams, real eval numbers, CI badge, and your "story" section (what was hard, key tradeoffs, what you'd do differently)
- [ ] You can explain, out loud, without notes: why decomposition beats basic RAG here, why you separated short/long-term memory, what your three biggest guardrail decisions were, and one number from your eval report

---

*Next step suggestion: start with the M0 prompt above in Antigravity, confirm the scaffold builds cleanly, then move to M1. Don't skip milestones — each one should be a working, demoable state before you move on.*
