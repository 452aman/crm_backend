# AI-First CRM – HCP Interaction Logger

A pharmaceutical CRM system for field representatives to log and manage interactions with Healthcare Professionals (HCPs). Built with FastAPI, LangGraph, Groq LLM, React, and PostgreSQL.

## Features

- **Dual logging modes** — log interactions via structured form or conversational AI chat
- **JWT Authentication** — secure signup and login
- **LangGraph AI Agent** — 5 tools powered by Groq LLM (llama-3.3-70b-versatile)
- **HCP Management** — manage doctor profiles
- **Interaction History** — full CRUD on interaction logs

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React + Redux Toolkit + Vite |
| Backend | Python + FastAPI |
| AI Agent | LangGraph + LangChain |
| LLM | Groq (llama-3.3-70b-versatile) |
| Database | PostgreSQL + SQLAlchemy |
| Auth | JWT (python-jose) |

## Project Structure

```
crm/
├── main.py                  # FastAPI entry point
├── requirements.txt
├── app/
│   ├── database.py          # DB connection
│   ├── models.py            # SQLAlchemy models
│   ├── schemas.py           # Pydantic schemas
│   ├── auth.py              # Password hashing + JWT
│   ├── agent/
│   │   ├── llm.py           # Groq LLM setup
│   │   ├── tools.py         # 5 LangGraph tools
│   │   └── graph.py         # LangGraph agent
│   └── routes/
│       ├── auth.py          # /signup /login
│       ├── hcps.py          # /hcps CRUD
│       ├── interactions.py  # /interactions CRUD
│       └── chat.py          # /chat AI endpoint
└── frontend/
    └── src/
        ├── store/           # Redux store + authSlice
        ├── api/             # Axios instance
        ├── pages/           # Login, Signup, Dashboard
        └── components/      # LogInteractionForm, ChatInterface
```

## LangGraph Tools

| Tool | Description |
|---|---|
| `log_interaction` | Extracts and saves a new HCP interaction from natural language |
| `edit_interaction` | Modifies an existing interaction by ID |
| `get_hcp_history` | Returns all past interactions with a specific doctor |
| `summarize_interaction` | Generates and saves a summary of an interaction |
| `get_all_interactions` | Lists all interactions logged by the current rep |

## Setup & Run

### Prerequisites
- Python 3.9+
- Node.js 18+
- PostgreSQL

### Backend

```bash
# Create database
createdb crm_db

# Create virtual environment
python3 -m venv crm_env
crm_env/bin/python3 -m pip install -r requirements.txt

# Create .env file
echo "SECRET_KEY=your-secret-key" > .env
echo "DATABASE_URL=postgresql://username@localhost/crm_db" >> .env
echo "GROQ_API_KEY=your-groq-api-key" >> .env

# Run backend
crm_env/bin/uvicorn main:app --reload --port 8001
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open **http://localhost:5173**

### API Docs

Open **http://localhost:8001/docs**

## Environment Variables

| Variable | Description |
|---|---|
| `DATABASE_URL` | PostgreSQL connection string |
| `SECRET_KEY` | JWT signing secret |
| `GROQ_API_KEY` | Groq API key from console.groq.com |
