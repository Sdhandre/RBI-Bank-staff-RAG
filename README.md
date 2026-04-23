# 🏦 Bank Staff Assistant — RBI RAG Chatbot

> An AI-powered chatbot that lets RBI bank staff ask natural-language questions about service rules, salary, leave, promotions, disciplinary procedures, and welfare schemes — all grounded in official RBI documents.

![Python](https://img.shields.io/badge/Python-3.13-blue?logo=python)
![Flask](https://img.shields.io/badge/Flask-3.x-black?logo=flask)
![LangChain](https://img.shields.io/badge/LangChain-0.4+-green?logo=chainlink)
![ChromaDB](https://img.shields.io/badge/ChromaDB-Vector_Store-orange)
![MongoDB](https://img.shields.io/badge/MongoDB-Session_Store-brightgreen?logo=mongodb)
![Gemini](https://img.shields.io/badge/Gemini-3_Flash-blue?logo=google)

---

## 📌 What It Does

The Bank Staff Assistant uses **Retrieval-Augmented Generation (RAG)** to answer questions grounded **exclusively** in RBI staff-regulation PDFs. It will not hallucinate or use outside knowledge — if the answer isn't in the documents, it says so.

**Key capabilities:**
- 🔍 Semantic search over RBI staff-regulation PDFs
- 🤖 LLM answer generation with source citations (page number + document name)
- 📚 Multi-turn conversation with session memory (last 6 messages as context)
- 🗂️ Full chat history with session management (create, rename, delete, search)
- 🔄 Dual LLM provider support — switch between Gemini and OpenRouter at runtime
- ⏹️ Stop-generation button to cancel in-flight requests
- 📱 Fully responsive UI (mobile sidebar overlay + desktop collapsible sidebar)

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
     ┌─────────────────┐
     │   LLM (Gemini / │
     │   OpenRouter)   │
     └────────┬────────┘
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
| `embedder.py` | Generates dense vector embeddings using **Google `gemini-embedding-001`** |
| `build_index.py` | Orchestrates the full ingestion pipeline and persists the vector store to disk |

**Chunking strategy:**
- Chunk size: **600 characters**
- Overlap: **150 characters** (preserves cross-boundary context)
- Separators: paragraph → newline → sentence → word
- Metadata enriched per chunk: `source`, `file_path`, `page`, `chunk_id`, `chunk_length`

**Rate-limit handling:** Batches of 90 documents are inserted with a 60-second pause between batches to stay within Gemini Free Tier API limits.

### 2. 🔎 Retrieval (`retrieval/retriever.py`)

At query time:
1. Query is normalised (lowercased, stripped)
2. `top_k × 3` candidates are fetched from ChromaDB via **cosine similarity search**
3. Duplicate chunks are de-duplicated (exact content match)
4. Weak matches (similarity score > 0.8) are filtered out
5. Top `k=3` results are returned with their scores and metadata

### 3. 🤖 Answer Generation (`llm.py`)

The retrieved chunks + last 6 messages of conversation history are assembled into a structured prompt and sent to the LLM:

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

## 🗃️ Vector Stores (Embedding Experiments)

Multiple vector stores were built during development — each uses a different embedding model:

| Directory | Embedding Model |
|---|---|
| `vector_store_gemini/` | `models/embedding-001` (Gemini) |
| `vector_store_gemini001/`| `gemini-embedding-001` (Gemini, latest) |
| `vector_store_minilm/` | `all-MiniLM-L6-v2` (Sentence Transformers) |
| `vector_store_ibm/` | IBM Granite Embedding |
| `vector_store_ibm30b/` | IBM Granite Embedding 30B |
| `vector_store/` | Initial prototype |

> **Currently active:** `vector_store_nvidia` — Nvidia's ` ` model, offering the best retrieval quality for this domain.

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
| `POST /chat` | POST | Main RAG query endpoint |

**Session management** is backed by **MongoDB** (local dev: `mongodb://localhost:27017`, production: configurable via `MONGO_URI` env var).

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
- ⚡ Model switcher (Gemini / OpenRouter) with live fallback hint
- ⏹️ Stop Generation button (AbortController-based)
- 🍔 Hamburger sidebar toggle — overlay on mobile, push-collapse on desktop
- Toast notifications, status badge, char counter

---

## 🔌 LLM Providers

The app supports **two providers**, switchable at runtime in the UI:

| Provider | Model | Notes |
|---|---|---|
| **Gemini** (default) | `gemini-3-flash-preview` | Direct Google AI API |
| **OpenRouter** | `google/gemini-2.5-flash` | OpenRouter proxy, useful when Gemini rate limits hit |

> 💡 Switch to **OpenRouter** in the UI if Gemini is slow or the free-tier limit is exhausted.

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| **LLM** | Google Gemini (`gemini-3-flash-preview`) via `langchain-google-genai` |
| **Embeddings** | Google `gemini-embedding-001` via `langchain-google-genai` |
| **Vector Store** | ChromaDB (`langchain-chroma`) — persisted to disk |
| **Orchestration** | LangChain (prompt templates, chains, output parsers) |
| **PDF Parsing** | PyMuPDF (`pymupdf`) |
| **Web Framework** | Flask 3.x + Flask-CORS |
| **Session Store** | MongoDB (`pymongo`) |
| **Frontend** | Vanilla HTML5 / CSS3 / JavaScript (no framework) |
| **Package Manager** | `uv` (fast Python package manager) |
| **Python** | 3.13+ |

---

## ⚙️ Setup & Running Locally

### Prerequisites
- Python 3.13+
- MongoDB running locally (`mongod`)
- [`uv`](https://github.com/astral-sh/uv) package manager

### 1. Clone & Install

```bash
git clone https://github.com/Sdhandre/RBI-Bank-staff-RAG.git
cd RBI-Bank-staff-RAG
uv sync
```

### 2. Configure Environment

Create a `.env` file in the root:

```env
GEMINI_API_KEY=your_google_gemini_api_key
OPENROUTER_API_KEY=your_openrouter_api_key   # optional, only if using OpenRouter
MONGO_URI=mongodb://localhost:27017/          # or your MongoDB Atlas URI
```

### 3. Add Your PDFs

Place RBI staff-regulation PDFs in:
```
data/pdf/
```

### 4. Build the Vector Index

```bash
uv run ingestion/build_index.py
```

> ⏳ This will embed all PDFs and save the vector store to `vector_store_gemini001/`. If you have many documents, it will pause between batches due to Gemini API rate limits.

### 5. Run the App

```bash
uv run app/app.py
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
│   ├── loader.py               # PDF loading (PyMuPDF)
│   ├── chunker.py              # Document chunking (RecursiveTextSplitter)
│   ├── embedder.py             # Embedding model (Gemini)
│   └── build_index.py          # Full ingestion pipeline runner
│
├── retrieval/
│   └── retriever.py            # Chroma semantic search + filtering
│
├── llm.py                      # LLM providers (Gemini / OpenRouter) + prompt
├── main.py                     # Entrypoint helper
│
├── data/pdf/                   # 📂 Place your RBI PDFs here
│
├── vector_store_gemini001/     # ✅ Active Chroma vector DB
├── vector_store_minilm/        # (Experimental — MiniLM embeddings)
├── vector_store_ibm/           # (Experimental — IBM Granite)
├── vector_store_gemini/        # (Experimental — older Gemini embeddings)
│
├── notebook/
│   ├── document.ipynb          # Document analysis / exploration
│   └── pdf_loader.ipynb        # PDF loader experiments
│
├── test_*.py                   # Unit/integration tests
├── pyproject.toml              # Project metadata & dependencies (uv)
├── requirements.txt            # pip-compatible dependencies
└── .env                        # API keys (not committed)
```

---

## 🧪 Tests

```bash
uv run test_llm.py          # Test LLM connection
uv run test_retriever.py    # Test retrieval pipeline
uv run test_chunking.py     # Test chunking strategy
uv run test_integration.py  # End-to-end integration test
```

---

## 🚀 Deployment

The app is **Railway-compatible**. Set the following environment variables in Railway:

| Variable | Value |
|---|---|
| `GEMINI_API_KEY` | Your Gemini API key |
| `OPENROUTER_API_KEY` | Your OpenRouter API key |
| `MONGO_URI` | MongoDB Atlas connection string |
| `PORT` | Set automatically by Railway |

Start command:
```bash
gunicorn app.app:app
```

> ⚠️ The pre-built vector store (`vector_store_gemini001/`) must be committed to the repo or uploaded separately, as Railway's free tier has no persistent disk.

---

## 📜 License

MIT — free to use, modify, and distribute.

---

## 🙋 Questions?

Open an issue or start a discussion on [GitHub](https://github.com/Sdhandre/RBI-Bank-staff-RAG).
