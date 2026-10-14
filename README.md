# AI-First CRM: HCP Interaction Platform

A CRM for pharmaceutical field reps to log and manage interactions with healthcare professionals (HCPs). Reps can log by form, by typing a plain-English note, or by talking to an AI assistant. Managers get a team view. Every AI write is a *proposal* the rep confirms first.

**Stack:** FastAPI · SQLAlchemy 2 · Alembic · PostgreSQL / SQLite · LangGraph · Groq · JWT · SSE · React 19 · TypeScript · Redux Toolkit (RTK Query) · Tailwind · Recharts · Docker

## What changed from the first version

The first version (a hiring-assignment submission) had a form, a chat box and five tools. This rebuild fixes its design problems and adds a real product around it:

| Before | Now |
|---|---|
| The agent got `rep_id` from the user's prompt text, so anyone could claim to be another rep | Identity comes from the JWT; tools are built per request around the authenticated user |
| The agent wrote to the database directly | Write tools only create a `PendingAction`. Nothing is saved until the rep clicks Confirm (single use, owner-only) |
| One-shot `create_react_agent` | A LangGraph `StateGraph` (agent ↔ tools loop) with a step limit, streaming tokens and a visible tool trace |
| Single role | Rep and manager roles; reps only ever see their own interactions |
| Form + chat only | AI quick-log with editable preview, doctor timelines, follow-ups, analytics, at-risk detection, team dashboard, CSV export |

## Features

- **Quick log:** paste a note ("Met Dr. Verma, positive about CardioMax, follow up in 2 weeks"). An LLM extracts a structured draft (fuzzy-matching the doctor and products); a rule-based fallback works without an API key. The rep reviews and edits before saving.
- **Assistant:** 9 tools. Reads: doctor history, my interactions, doctors needing a visit, follow-ups, product mentions, summarise. Proposals: log, edit, create follow-up. The UI shows the tool trace and an approve/discard card for each proposal.
- **Analytics:** activity trend, sentiment mix, top products, Tier A coverage, overdue follow-ups, and an **at-risk list** (Tier A/B doctors with no recent contact) with a suggested next action.
- **Team view (managers):** per-rep activity, reach, positive rate, overdue follow-ups and neglected accounts.
- **Doctor pages:** full timeline, sentiment and product breakdown, open follow-ups.

## Run it

```bash
# Docker (SQLite, seeded with synthetic demo data)
cp backend/.env.example backend/.env        # add GROQ_API_KEY for the AI features
docker compose up --build                   # http://localhost:8083

# or locally
cd backend && python3 -m venv crm_env && crm_env/bin/python3 -m pip install -r requirements.txt
crm_env/bin/alembic upgrade head && crm_env/bin/python3 -m app.seed
crm_env/bin/uvicorn app.main:app --port 8003
cd ../frontend && npm install && npm run dev   # http://localhost:5210
```

Demo logins: `rep1@crm.dev` / `rep12345`, `manager@crm.dev` / `manager123`. All doctors, hospitals and products are fictional.

PostgreSQL: set `DATABASE_URL=postgresql+psycopg://user:pass@host/crm` (migration, seed and API verified against Postgres 16). Without `GROQ_API_KEY` everything works except the assistant and AI parsing, which fall back to rules.

Tests: `cd backend && crm_env/bin/python3 -m pytest` (10 tests: auth, role scoping, quick-log, analytics, and the full propose → confirm flow using a scripted fake chat model, no network).

## Layout

```
backend/app/
  api/        auth, records (HCPs, interactions, follow-ups), insights (analytics + assistant SSE)
  agent/      tools.py (ToolKit per user), graph.py (LangGraph)
  services/   crm.py (shared domain rules), extraction.py, analytics.py, actions.py
frontend/src/ store/ (RTK Query + token refresh), pages/, components/
```

*Fictional data. Not a medical product.*
