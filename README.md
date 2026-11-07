# AI Job Agent

A chat assistant that searches the German job market for you. Tell it what you're looking for, optionally upload your CV, and it searches several job sources and suggests the best matches.

Built with a FastAPI backend, a Next.js chat UI, and an LLM agent that uses its search tools through [MCP](https://modelcontextprotocol.io).

## What it does

- Understands requests like *"data jobs in Berlin that fit my resume"*, and follow-ups like *"only remote ones"*
- Searches the Bundesagentur für Arbeit, plus Adzuna if you add keys, and removes duplicates
- Reads your CV (PDF or DOCX) to match jobs to your skills and experience
- Can fetch full job descriptions, and search the web for company career pages if you add a Tavily key

## Quick start

You need Python 3.10+, Node.js, and an API key for an OpenAI-compatible LLM provider (OpenRouter, OpenAI, Groq, Gemini, or a local Ollama).

**1. Backend**

```bash
cd backend
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
cp .env.example .env             # Windows: Copy-Item .env.example .env
```

Open `backend/.env` and set at least `LLM_API_KEY` (see [Configuration](#configuration)). Then start the server:

```bash
uvicorn app.main:app --reload
```

The API runs on `http://localhost:8000` (docs at `/docs`).

**2. Frontend** (in a second terminal)

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:3000` and start searching.

## Configuration

Set these in `backend/.env`:

| Variable | Required | What it does |
|---|---|---|
| `LLM_API_KEY` | Yes | API key for your LLM provider |
| `LLM_BASE_URL` | No | Provider endpoint. Default: OpenRouter. Examples are in `.env.example` |
| `LLM_MODEL` | No | Model to use. Default: a free OpenRouter model |
| `ADZUNA_APP_ID`, `ADZUNA_APP_KEY` | No | Add both to include Adzuna results |
| `TAVILY_API_KEY` | No | Enables web search and page reading |
| `AGENT_VERBOSE` | No | Set to `1` for detailed tool logs |

The Bundesagentur für Arbeit source works without any key.

> **Tip:** The model must support tool (function) calling. Small or free models often work poorly: they may ignore your location or forget earlier messages. If results look off, try a stronger model first.

## How it works

```text
Browser (Next.js)  ──POST /search──▶  FastAPI  ──▶  Agent (LLM)  ──▶  MCP tools
                                                                       ├─ search_jobs → Bundesagentur, Adzuna*
                                                                       └─ search_web, read_webpage → Tavily*
                                                                       (* only if configured)
```

1. You send a message, plus your CV if attached.
2. The backend extracts the CV text and starts the agent.
3. The agent decides which tools to call, up to 15 steps, then writes the answer.

**Conversation memory:** the backend doesn't store anything. The browser sends the last 10 messages and your CV with every request, so follow-ups work. Reloading the page starts a new conversation.

## API

`POST /search` takes `multipart/form-data`:

| Field | Description |
|---|---|
| `message` | Your request (max 2,000 characters) |
| `cv` | Optional file: `.pdf`, `.docx`, `.txt` or `.md`, max 5 MB |
| `history` | Optional JSON list of earlier `{role, content}` messages |

It returns `{"response": "..."}`.

## Agent tools

| Tool | Purpose |
|---|---|
| `search_jobs` | Search all enabled sources, merged and de-duplicated |
| `get_job_details`, `get_jobs_details` | Full descriptions, for Bundesagentur jobs only (ids starting with `ba:`) |
| `search_web`, `read_webpage` | Web search and page reading, only with a Tavily key |

## Project layout

```text
backend/app/
  agent/       agent loop, LLM client, prompts
  mcp/         MCP server with the tools above
  services/    CV parsing and job sources (one file per source)
  main.py      FastAPI app
frontend/      Next.js chat UI
```

To add a job source, write a search function like `adzuna_search.py` and register it in `services/sources/registry.py`.

## Development

```bash
cd backend && pip install -r requirements-dev.txt && pytest   # backend tests
cd frontend && npm run lint                                    # frontend lint
```

## Known limitations

- Built for local use: the frontend calls `localhost:8000` and the backend only allows `localhost:3000`. There is no login or rate limiting, so don't expose it publicly as is.
- Not every filter works for every source. Each one applies what its API supports.
- Web results are unverified snippets and may be incomplete.
- The agent follows your location and filters only as well as the LLM does.

## License

No license yet. Until one is added, all rights are reserved.
