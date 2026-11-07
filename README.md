# AI Job Agent

An AI-powered job search assistant for the German job market. Users can describe the roles they are looking for, optionally upload a CV, and let an LLM-powered agent search multiple job sources and retrieve additional information about promising vacancies.

The project combines a **FastAPI backend**, a **Next.js chat interface**, and an **MCP-based tool layer** that gives the agent access to job-search and web-search capabilities.

## Features

- **Natural-language job search** – describe a target role, location, and preferences in a chat interface.
- **Multi-source job search** – search the Bundesagentur für Arbeit and, when configured, Adzuna.
- **Result aggregation** – merge results from enabled sources and remove likely duplicates based on job title, company, and location.
- **Web search** – optionally use Tavily to discover job postings on company career pages and other websites.
- **Additional job information** – retrieve full job descriptions for supported Bundesagentur für Arbeit listings, or read public web pages through the web-search integration.
- **CV upload** – extract text from PDF, DOCX, TXT, and Markdown files and provide it as context to the agent.
- **Tool-using AI agent** – discover tools through MCP and decide which tools to call based on the user's request.
- **Configurable LLM endpoint** – configure an OpenAI-compatible API endpoint, model, and API key through environment variables.

## How It Works

1. The user enters a job-search request and can optionally attach a CV.
2. The FastAPI backend validates the request and extracts text from the uploaded CV, if present.
3. The agent connects to the MCP server and discovers the tools currently available.
4. The LLM interprets the request and chooses which tools to call.
5. The MCP tools search the enabled job sources and, when useful, retrieve more information from job listings or web pages.
6. The agent uses the tool results to prepare a natural-language response for the frontend.

## Architecture

```text
                         User
                          |
                          v
                  Next.js / React UI
                          |
                    POST /search
                          |
                          v
                    FastAPI Backend
                          |
                          v
                       AI Agent
                          |
                 Configurable LLM Client
                          |
                 Tool calling via MCP
                          |
                          v
                  MCP Job Search Server
                    /             \
                   /               \
          Job search tools       Web tools*
                 |                   |
          Source registry          Tavily
                 |
          Search aggregator
             /       \
            /         \
 Bundesagentur       Adzuna*
 für Arbeit
```

`*` Optional integrations that are enabled when their API credentials are configured. Tavily web-search tools are only registered with the MCP server when `TAVILY_API_KEY` is present. Adzuna is only included as a job source when both Adzuna credentials are configured.

## Tech Stack

| Area | Technologies |
|---|---|
| Frontend | Next.js, React, TypeScript, Tailwind CSS |
| Backend | Python, FastAPI, Uvicorn |
| AI integration | OpenAI-compatible Python client, configurable LLM endpoint |
| Agent/tool integration | Model Context Protocol (MCP) |
| Job sources | Bundesagentur für Arbeit API, Adzuna API |
| Web search and page extraction | Tavily |
| Data validation | Pydantic |
| CV extraction | pypdf, python-docx |
| Configuration | python-dotenv |

## Project Structure

```text
ai-job-agent/
├── backend/
│   ├── app/
│   │   ├── agent/              # Agent loop, LLM client, prompts and logging
│   │   ├── mcp/                # MCP server and tools
│   │   ├── models/             # Pydantic data models
│   │   ├── services/
│   │   │   ├── sources/        # Job-source adapters, registry and aggregator
│   │   │   └── cv_parser.py    # CV text extraction
│   │   └── main.py             # FastAPI application
│   ├── .env.example
│   ├── requirements.txt
│   └── requirements-dev.txt
├── frontend/
│   ├── app/                    # Next.js app
│   ├── components/             # Chat and message components
│   ├── lib/                    # Backend API client
│   └── package.json
├── .gitignore
└── README.md
```

## Getting Started

### Prerequisites

- Python 3.10 or newer
- Node.js and npm
- An API key for an OpenAI-compatible LLM provider
- Optional: Tavily API key for web search
- Optional: Adzuna application ID and API key for Adzuna job results

### 1. Clone the repository

```bash
git clone https://github.com/Ouzoproject/ai-job-agent.git
cd ai-job-agent
```

### 2. Configure the backend

Open a terminal in the project root and create a virtual environment:

```bash
cd backend
python -m venv .venv
```

Activate it:

**Windows PowerShell**
```powershell
.venv\Scripts\Activate.ps1
```

**macOS / Linux**
```bash
source .venv/bin/activate
```

Install the Python dependencies:

```bash
python -m pip install -r requirements.txt
```

Create your local environment file from the example:

**Windows PowerShell**
```powershell
Copy-Item .env.example .env
```

**macOS / Linux**
```bash
cp .env.example .env
```

Edit `backend/.env` and provide your credentials and model configuration.

### 3. Configure environment variables

| Variable | Required | Description |
|---|---|---|
| `LLM_API_KEY` | Yes | API key for the selected LLM provider |
| `LLM_BASE_URL` | Yes | OpenAI-compatible API base URL |
| `LLM_MODEL` | Yes | Model identifier used by the provider |
| `AGENT_VERBOSE` | No | Set to `1` to enable verbose agent logging |
| `TAVILY_API_KEY` | No | Enables the Tavily web-search and page-reading tools |
| `ADZUNA_APP_ID` | No | Adzuna application ID |
| `ADZUNA_APP_KEY` | No | Adzuna application key |

Example configuration:

```env
LLM_API_KEY=your-api-key
LLM_BASE_URL=https://openrouter.ai/api/v1
LLM_MODEL=your-model-id
AGENT_VERBOSE=0

TAVILY_API_KEY=your-tavily-api-key

ADZUNA_APP_ID=your-adzuna-app-id
ADZUNA_APP_KEY=your-adzuna-app-key
```

The LLM client uses an OpenAI-compatible API interface. The repository's example file includes base-URL examples for OpenRouter, OpenAI, Groq, Gemini's OpenAI-compatible endpoint, and a local Ollama endpoint. The selected provider and model must support the chat-completion tool/function-calling features used by the agent; compatibility can vary between providers and models.

The Bundesagentur für Arbeit source is available without additional credentials. Adzuna and Tavily are optional integrations.

### 4. Start the backend

From the `backend/` directory, run:

```bash
uvicorn app.main:app --reload
```

The API is available at `http://localhost:8000`.

FastAPI's interactive API documentation is available at:

- `http://localhost:8000/docs`

### 5. Start the frontend

Open a second terminal in the project root:

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:3000` in your browser.

The frontend currently sends requests to `http://localhost:8000`. The backend CORS configuration also currently allows the local frontend origin `http://localhost:3000`.

## API

### `POST /search`

Accepts `multipart/form-data` with:

| Field | Type | Description |
|---|---|---|
| `message` | string | Job-search instructions or preferences |
| `cv` | file, optional | CV attachment |

The backend accepts `.pdf`, `.docx`, `.txt`, and `.md` CV files, with a maximum upload size of 5 MB. The current frontend file picker exposes PDF, DOC, and DOCX extensions; TXT and Markdown are currently supported by the backend parser but are not exposed in that picker.

Example response:

```json
{
  "response": "The agent's response with matching job opportunities..."
}
```

## MCP Tools

The MCP server exposes the following tools:

| Tool | Purpose |
|---|---|
| `search_jobs` | Search enabled job databases and return aggregated, de-duplicated job summaries |
| `get_job_details` | Retrieve full details for a single Bundesagentur für Arbeit job |
| `get_jobs_details` | Retrieve details for multiple Bundesagentur für Arbeit jobs |
| `search_web` | Search the open web for job postings (available when Tavily is configured) |
| `read_webpage` | Extract text from a public web page (available when Tavily is configured) |

Full job-detail retrieval through the job API is currently implemented for Bundesagentur für Arbeit job IDs. For listings from other sources, the agent can use the web-page reading tool when available.

## Development

Install development dependencies from the `backend/` directory:

```bash
python -m pip install -r requirements-dev.txt
```

Run the backend tests with:

```bash
pytest
```

Run the frontend linter from `frontend/`:

```bash
npm run lint
```

## Current Scope and Limitations

- Search coverage depends on the sources that are available and configured.
- Each source supports only the filters provided by its underlying API; not every filter is necessarily applied by every source.
- Full structured job details are currently supported for Bundesagentur für Arbeit listings.
- Web search results and extracted web-page content may be incomplete or change over time.
- LLM tool-calling support and behavior depend on the selected provider and model.
- The current frontend and CORS settings are configured for local development.

## Roadmap

Potential next steps include:

- Add further job-search providers through the existing source interface and registry.
- Expand structured job-detail retrieval for additional sources.
- Improve job relevance ranking and matching against CV skills and experience.
- Add saved searches, bookmarks, and persistent search history.
- Add configuration for deployment beyond the local development environment.

## License

No license has been specified yet. Unless a license is added to the repository, standard copyright restrictions apply.
