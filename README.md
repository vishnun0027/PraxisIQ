# Mental Clarity Journal

An AI-powered journaling application that analyzes your emotions using CBT (Cognitive Behavioral Therapy) techniques. Write a journal entry, receive structured emotional analysis, and track your emotional trends over time.

---

## Tech Stack

- **Backend**: FastAPI + SQLAlchemy 2.0 + PostgreSQL
- **AI**: LangChain + Ollama (local LLM)
- **Vector Search**: Qdrant + SentenceTransformers (`all-MiniLM-L6-v2`)
- **Frontend**: Streamlit (multi-page)
- **Package Manager**: [uv](https://docs.astral.sh/uv/)

---

## Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) installed
- [Ollama](https://ollama.com/) running locally
- PostgreSQL 16+ (Docker recommended)
- Qdrant (Docker recommended)

---

## Setup

### 1. Clone and install dependencies

```bash
git clone https://github.com/vishnun0027/projectx.git
cd projectx
uv sync
```

### 2. Configure environment

Create a `.env` file in the project root:

```env
DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/journal
```

### 3. Configure the LLM model

Edit `config/llm_model.yaml` with the name of your Ollama model and any parameters you want to tune:

```yaml
model_name: "gpt-oss:120b-cloud"
temperature: 0.0
format: "json"
timeout: 120
num_predict: 2048
num_ctx: 8192
top_p: 0.9
repeat_penalty: 1.1
```

Make sure the model is available in your local Ollama instance before starting the backend.

---

## Running Locally

### Start PostgreSQL (Docker)

```bash
docker run --name journal-db \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=journal \
  -p 5432:5432 \
  -d postgres:16
```

### Start Qdrant (Docker)

```bash
docker run --name journal-qdrant \
  -p 6333:6333 \
  -d qdrant/qdrant
```

### Start the FastAPI backend

```bash
uv run uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

API available at: `http://localhost:8000`
Interactive docs: `http://localhost:8000/docs`

### Start the Streamlit frontend

In a separate terminal:

```bash
uv run streamlit run streamlit_app.py
```

Frontend available at: `http://localhost:8501`

---

## Running with Docker Compose

Starts the API, PostgreSQL, and Qdrant together:

```bash
docker compose up --build
```

Then start the Streamlit frontend separately:

```bash
uv run streamlit run streamlit_app.py
```

---

## Running Tests

```bash
uv run pytest tests/ -v
```

With coverage:

```bash
uv run pytest tests/ -v --cov=src --cov-report=term-missing
```

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Health check |
| `POST` | `/journal` | Submit a journal entry for analysis |
| `GET` | `/journal/history` | Get past entries (supports `skip` and `limit`) |
| `GET` | `/journal/search` | Semantic search for similar entries (`?q=...`) |
| `GET` | `/journal/{id}` | Get a single entry by ID |
| `DELETE` | `/journal/all` | Delete all journal entries |

---

## Project Structure

```
projectx/
├── src/
│   ├── main.py              # FastAPI app and routes
│   ├── analyzer.py          # LLM-based journal analyzer
│   └── core/
│       ├── models.py        # SQLAlchemy ORM models
│       ├── crud.py          # Database operations
│       ├── database.py      # DB engine, session, and Qdrant init
│       ├── embeddings.py    # Sentence embedding generation
│       └── logging.py       # Logging setup
├── pages/
│   ├── 1_Journal_Entry.py   # Streamlit journal input page
│   ├── 2_Dashboard.py       # Streamlit dashboard and trends
│   └── 3_Semantic_Search.py # Streamlit semantic search page
├── ui/
│   └── helpers.py           # Shared CSS, charts, and HTML builders
├── config/
│   └── llm_model.yaml       # LLM configuration
├── tests/                   # Pytest test suite
├── docker/                  # Dockerfile
├── docker-compose.yml
└── streamlit_app.py         # Streamlit entry point
```