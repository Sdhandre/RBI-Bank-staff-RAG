# 🏦 Bank Staff Assistant — RBI RAG Chatbot

> An AI-powered chatbot that lets RBI bank staff ask natural-language questions about service rules, salary, leave, promotions, disciplinary procedures, and welfare schemes — all grounded in official RBI documents.

![Python](https://img.shields.io/badge/Python-3.13-blue?logo=python)
![Flask](https://img.shields.io/badge/Flask-3.x-black?logo=flask)
![LangChain](https://img.shields.io/badge/LangChain-1.x-green?logo=chainlink)
![ChromaDB](https://img.shields.io/badge/ChromaDB-Vector_Store-orange)
![MongoDB](https://img.shields.io/badge/MongoDB-Session_Store-brightgreen?logo=mongodb)
![NVIDIA](https://img.shields.io/badge/NVIDIA-NIM_Embeddings-76b900?logo=nvidia)
![Gemini](https://img.shields.io/badge/Gemini-3_Flash-blue?logo=google)

---

## 📌 What It Does

The Bank Staff Assistant uses **Retrieval-Augmented Generation (RAG)** to answer questions grounded **exclusively** in RBI staff-regulation PDFs. It will not hallucinate or use outside knowledge — if the answer isn't in the documents, it says so.

**Key capabilities:**
- 🔍 Semantic search over RBI staff-regulation PDFs using **NVIDIA NIM embeddings**
- 🤖 LLM answer generation with source citations (page number + document name)
- 📚 Multi-turn conversation with session memory (last 6 messages as context)
- 🗂️ Full chat history with session management (create, rename, delete, search)
- 🔄 **Three LLM providers** — switch between DeepSeek (NVIDIA NIM), Gemini, and OpenRouter at runtime
- ⏹️ Stop-generation button to cancel in-flight requests
- 📱 Fully responsive UI (mobile sidebar overlay + desktop collapsible sidebar)
- ☁️ MongoDB Atlas-backed persistent sessions (cloud or local)

---

## 🏗️ Architecture Overview

```
User Query
    │
    ▼
┌─────────────────────────────────────┐
│          Flask REST API             │
│  (session + chat management)        │
└────────────┬────────────────────────┘
             │
    ┌─────────┴─────────┐
    │                   │
    ▼                   ▼
┌──────────┐     ┌─────────────┐
│ Retriever│     │  Chat Hist. │
│ (Chroma) │     │  (MongoDB)  │
└────┬─────┘     └──────┬──────┘
     │                  │
     └────────┬──────────┘
              │  chunks + history
              ▼
     ┌─────────────────────┐
     │   LLM Provider      │
     │ DeepSeek / Gemini / │
     │    OpenRouter        │
     └────────┬────────────┘
              │
              ▼
       Structured Answer
       + Source Citations
```

---

## 🧠 RAG Pipeline (How It Works)

### 1. 📄 Document Ingestion (`ingestion/`)

| File | Role |
|---|---|
| `loader.py` | Recursively loads all PDF files from `data/pdf/` using **PyMuPDF** |
| `chunker.py` | Splits loaded documents into overlapping chunks (`600 chars`, `150 overlap`) using `RecursiveCharacterTextSplitter` |
| `embedder.py` | Generates dense vector embeddings via **NVIDIA NIM** (`llama-nemotron-embed-1b-v2`) |
| `build_index.py` | Orchestrates the full ingestion pipeline and persists the vector store to disk |

**Chunking strategy:**
- Chunk size: **600 characters**
- Overlap: **150 characters** (preserves cross-boundary context)
- Separators: paragraph → newline → sentence → word
- Metadata enriched per chunk: `source`, `file_path`, `page`, `chunk_id`, `chunk_length`

**Rate-limit handling:** Documents are inserted in batches of 90 with a 60-second pause between batches to respect API rate limits.

### 2. 🔎 Retrieval (`retrieval/retriever.py`)

At query time:
1. Query is normalised (lowercased, stripped)
2. `top_k × 3` candidates are fetched from ChromaDB via **cosine similarity search**
3. Duplicate chunks are de-duplicated (exact content match)
4. Weak matches (ChromaDB cosine distance > 1.4) are filtered out
5. Top `k=3` results are returned with their scores and metadata
6. **Automatic retry** on transient NVIDIA NIM network errors (exponential backoff, up to 3 attempts)

### 3. 🤖 Answer Generation (`llm.py`)

The retrieved chunks + last 6 messages of conversation history are assembled into a structured prompt and sent to the chosen LLM:

```
CONVERSATION HISTORY  →  context-aware follow-up handling
CONTEXT (from docs)   →  source-grounded answering
CURRENT QUESTION      →  the user's query
```

The LLM is instructed to:
- Answer **only** using the provided context
- Be structured (key points, conditions)
- Cite page references
- End every answer with a **proactive follow-up question**

---

## 🔌 LLM Providers

The app supports **three providers**, switchable at runtime in the UI:

| Provider | Model | Env Key | Notes |
|---|---|---|---|
| **DeepSeek** (default) | `deepseek-ai/deepseek-v4-flash` | `NVIDIA_API_KEY` | Served via NVIDIA NIM inference API |
| **Gemini** | `gemini-3-flash-preview` | `GEMINI_API_KEY` | Direct Google AI API |
| **OpenRouter** | `google/gemini-2.5-flash` | `OPENROUTER_API_KEY` | OpenRouter proxy, useful when Gemini rate limits hit |

> 💡 Switch between providers live in the UI. DeepSeek via NVIDIA NIM is the default for best performance. Use **Gemini** or **OpenRouter** as fallbacks.

---

## 🗃️ Vector Stores (Embedding Experiments)

Multiple vector stores were built during development — each uses a different embedding model:

| Directory | Embedding Model | Status |
|---|---|---|
| `vector_store_nvidia/` | `llama-nemotron-embed-1b-v2` (NVIDIA NIM) | ✅ **Active** |
| `vector_store_gemini/` | `models/embedding-001` (Gemini) | Experimental |
| `vector_store_gemini001/` | `gemini-embedding-001` (Gemini, latest) | Experimental |
| `vector_store_minilm/` | `all-MiniLM-L6-v2` (Sentence Transformers) | Experimental |
| `vector_store_ibm/` | IBM Granite Embedding | Experimental |
| `vector_store_ibm30b/` | IBM Granite Embedding 30B | Experimental |
| `vector_store/` | Initial prototype | Deprecated |

> **Currently active:** `vector_store_nvidia` — NVIDIA's `llama-nemotron-embed-1b-v2` model, offering the best retrieval quality for this domain.

---

## 🌐 Web Application (`app/`)

### Backend — Flask REST API (`app/app.py`)

| Endpoint | Method | Description |
|---|---|---|
| `GET /` | GET | Serves the chat UI |
| `GET /health` | GET | Health check |
| `GET /sessions` | GET | List all sessions (supports `?q=search`) |
| `POST /sessions` | POST | Create new session |
| `GET /sessions/<id>` | GET | Get session + full message history |
| `PATCH /sessions/<id>` | PATCH | Rename a session |
| `DELETE /sessions/<id>` | DELETE | Delete session and all its messages |
| `POST /chat` | POST | Main RAG query endpoint — accepts `provider` field |

**Chat request body:**
```json
{
  "query": "What is the leave policy for Grade B officers?",
  "session_id": "<uuid>",
  "provider": "deepseek"
}
```

**Session management** is backed by **MongoDB** (local dev: `mongodb://localhost:27017`, production: MongoDB Atlas via `MONGO_URI` env var).

Auto-title: First message of a session (truncated to 60 chars) becomes the session title automatically.

### Frontend — Vanilla HTML/CSS/JS (`app/static/`, `app/templates/`)

- **No framework** — pure HTML5, CSS custom properties, vanilla JavaScript
- ChatGPT-style sidebar with session list grouped by date (Today / Yesterday / Last 7 Days / Older)
- Sidebar search, rename, delete with context actions
- Welcome screen with 6 topic-category cards (General Policy, Salary, Leave, Promotions, Conduct, Welfare)
- Persistent **Suggested Topics** panel — always visible during conversation
- Markdown rendering for bot responses (`marked.js`)
- Source citation pills (document name + page)
- Typing indicator with bouncing dots
- ⚡ Model switcher (DeepSeek / Gemini / OpenRouter) with live fallback hint
- ⏹️ Stop Generation button (AbortController-based)
- 🍔 Hamburger sidebar toggle — overlay on mobile, push-collapse on desktop
- Toast notifications, status badge, char counter

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| **LLM (default)** | DeepSeek v4 Flash via NVIDIA NIM (`langchain-nvidia-ai-endpoints`) |
| **LLM (alt)** | Google Gemini (`gemini-3-flash-preview`) via `langchain-google-genai` |
| **LLM (alt)** | OpenRouter (`google/gemini-2.5-flash`) via `langchain-openai` |
| **Embeddings** | NVIDIA NIM `llama-nemotron-embed-1b-v2` |
| **Vector Store** | ChromaDB (`langchain-chroma`) — persisted to disk |
| **Orchestration** | LangChain (prompt templates, chains, output parsers) |
| **PDF Parsing** | PyMuPDF (`pymupdf`) |
| **Web Framework** | Flask 3.x + Flask-CORS |
| **Session Store** | MongoDB (`pymongo`) — local or MongoDB Atlas |
| **Frontend** | Vanilla HTML5 / CSS3 / JavaScript (no framework) |
| **Package Manager** | `uv` (fast Python package manager) |
| **Python** | 3.13+ |

---

## ⚙️ Setup & Running Locally

### Prerequisites
- Python 3.13+
- MongoDB running locally (`mongod`) — or a MongoDB Atlas connection string
- [`uv`](https://github.com/astral-sh/uv) package manager
- API keys: NVIDIA NIM, Google Gemini, OpenRouter (optional)

### 1. Clone & Install

```bash
git clone https://github.com/Sdhandre/RBI-Bank-staff-RAG.git
cd RBI-Bank-staff-RAG
uv sync
```

### 2. Configure Environment

Create a `.env` file in the root:

```env
NVIDIA_API_KEY=your_nvidia_nim_api_key          # Required — for embeddings + DeepSeek LLM
GEMINI_API_KEY=your_google_gemini_api_key        # Required — for Gemini LLM provider
OPENROUTER_API_KEY=your_openrouter_api_key       # Optional — for OpenRouter provider
MONGO_URI=mongodb://localhost:27017/             # Or your MongoDB Atlas URI
```

> ⚠️ **Never commit your `.env` file.** It is already in `.gitignore`.

### 3. Add Your PDFs

Place RBI staff-regulation PDFs in:
```
data/pdf/
```

### 4. Build the Vector Index

```bash
uv run python -m ingestion.build_index
```

> ⏳ This embeds all PDFs using NVIDIA NIM and saves the vector store to `vector_store_nvidia/`.  
> Large collections are batched with automatic rate-limit pausing.

### 5. Run the App

```bash
uv run python app/app.py
```

Open `http://127.0.0.1:5000` in your browser.

---

## 📁 Project Structure

```
Bank_staff_RAG/
│
├── app/
│   ├── app.py                  # Flask REST API (sessions + chat endpoints)
│   ├── static/
│   │   ├── style.css           # Full UI styles (dark theme, responsive)
│   │   └── script.js           # Chat logic, session management, sidebar
│   └── templates/
│       └── index.html          # Single-page chat UI
│
├── ingestion/
│   ├── loader.py               # PDF loading via PyMuPDF (recursive glob)
│   ├── chunker.py              # Document chunking (RecursiveCharacterTextSplitter)
│   ├── embedder.py             # NVIDIA NIM embedding model (llama-nemotron-embed-1b-v2)
│   └── build_index.py          # Full ingestion pipeline orchestrator
│
├── retrieval/
│   └── retriever.py            # Chroma semantic search + dedup/filtering + retry logic
│
├── llm.py                      # LLM factory: DeepSeek (NVIDIA) / Gemini / OpenRouter + prompt
├── main.py                     # Entrypoint helper
│
├── data/pdf/                   # 📂 Place your RBI PDFs here
│
├── vector_store_nvidia/        # ✅ Active — NVIDIA NIM embeddings
├── vector_store_gemini001/     # Experimental — latest Gemini embeddings
├── vector_store_minilm/        # Experimental — lightweight MiniLM embeddings
├── vector_store_ibm/           # Experimental — IBM Granite embeddings
├── vector_store_gemini/        # Experimental — older Gemini embeddings
├── vector_store_ibm30b/        # Experimental — IBM Granite 30B
├── vector_store/               # Deprecated — initial prototype
│
├── notebook/
│   ├── document.ipynb          # Document analysis / exploration
│   └── pdf_loader.ipynb        # PDF loader experiments
│
├── test_llm.py                 # Test LLM provider connection
├── test_retriever.py           # Test retrieval pipeline
├── test_chunking.py            # Test chunking strategy
├── test_integration.py         # End-to-end integration test
├── pyproject.toml              # Project metadata & dependencies (uv)
├── requirements.txt            # pip-compatible dependency list
└── .env                        # API keys (not committed)
```

---

## 🧪 Tests

```bash
uv run python test_llm.py          # Test LLM provider connectivity
uv run python test_retriever.py    # Test retrieval pipeline
uv run python test_chunking.py     # Test chunking strategy
uv run python test_integration.py  # End-to-end RAG integration test
```

---

## 🚀 Deployment

### Railway / Render

Set the following environment variables on your hosting platform:

| Variable | Description |
|---|---|
| `NVIDIA_API_KEY` | NVIDIA NIM API key (embeddings + DeepSeek LLM) |
| `GEMINI_API_KEY` | Google Gemini API key |
| `OPENROUTER_API_KEY` | OpenRouter API key (optional) |
| `MONGO_URI` | MongoDB Atlas connection string |
| `PORT` | Set automatically by the platform |

Start command:
```bash
gunicorn app.app:app
```

> ⚠️ The pre-built `vector_store_nvidia/` directory must be committed to the repository or uploaded separately, as most cloud platforms have no persistent disk on free tiers.

---

## 📜 License

MIT — free to use, modify, and distribute.

---

## 🙋 Questions?

Open an issue or start a discussion on [GitHub](https://github.com/Sdhandre/RBI-Bank-staff-RAG).
