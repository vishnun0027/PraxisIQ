# PraxisIQ

An AI-powered journaling application that analyzes your emotions using CBT (Cognitive Behavioral Therapy) techniques. Write a journal entry, receive structured emotional analysis, and track your emotional trends over time.

---

## Tech Stack

- **Backend**: FastAPI + SQLAlchemy 2.0 + PostgreSQL
- **AI**: LangChain + Groq Cloud (`llama-3.3-70b-versatile`)
- **Vector Search**: Supabase pgvector + SentenceTransformers (`all-MiniLM-L6-v2`)

- **Ingestion**: Telegram Bot Polling
- **Package Manager**: [uv](https://docs.astral.sh/uv/)

---

## Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) installed
- Supabase account & project with `pgvector` enabled
- Groq Cloud API Key
- Telegram Bot Token (optional, for mobile ingestion)

---

## Setup

### 1. Clone and install dependencies

```bash
git clone https://github.com/vishnun0027/PraxisIQ.git
cd PraxisIQ
uv sync
```

### 2. Configure environment

Create a `.env` file in the project root:

```env
# --- Database Configuration (Supabase) ---
DATABASE_URL=postgresql+psycopg://postgres.[PROJECT_REF]:[PASSWORD]@aws-0-[REGION].pooler.supabase.com:6543/postgres?sslmode=require

# --- LLM Configuration (Groq Cloud) ---
GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# --- Telegram Bot Integration (Collector) ---
TELEGRAM_BOT_TOKEN=1234567890:ABCDEFGHIJKLMNOPQRSTUVWXYZ
TELEGRAM_ALLOWED_CHAT_ID=987654321
```

### 3. Configure the LLM model

Edit `config/llm_model.yaml` with the name of your Groq model:

```yaml
model_name: "llama-3.3-70b-versatile"
temperature: 0.0
timeout: 60
max_retries: 3
```

---

## Running Locally

### Start the FastAPI backend

```bash
uv run uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

API available at: `http://localhost:8000`
Interactive docs: `http://localhost:8000/docs`



### Run the Telegram Collector (Optional)

In a separate terminal, to start polling Telegram for new entries:

```bash
uv run python src/bot/collector.py
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
PraxisIQ/
├── src/
│   ├── main.py              # FastAPI app and routes
│   ├── analyzer.py          # LLM-based journal analyzer
│   └── core/
│       ├── models.py        # SQLAlchemy ORM models
│       ├── crud.py          # Database operations
│       ├── database.py      # DB engine, session, and Qdrant init
│       ├── embeddings.py    # Sentence embedding generation
│       └── logging.py       # Logging setup

├── config/
│   └── llm_model.yaml       # LLM configuration
├── tests/                   # Pytest test suite
├── src/bot/                 # Telegram integration
│   └── collector.py         # Polling script

```