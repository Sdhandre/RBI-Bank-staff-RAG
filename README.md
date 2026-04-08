# 🏦 Bank Staff RAG System

A Retrieval-Augmented Generation (RAG) system that helps bank staff query internal documents (policies, rules, etc.) using natural language.

---

## 🚧 Current Status

### ✅ Completed (Backend Ready)

* PDF processing and cleaning
* Intelligent chunking
* Embeddings using **BAAI/bge-small-en-v1.5**
* Vector database using **Chroma**
* Optimized retrieval system (no duplicates, filtered results)

👉 **Important:**
You do NOT need to rebuild embeddings or vector database.

---

## 📁 Project Structure

```
bank_staff_rag/
│
├── data/
│   └── pdf/                   # Input PDF documents
│
├── vector_store/              # Prebuilt Chroma DB (READY)
│
├── ingestion/
│   ├── loader.py
│   ├── chunker.py
│   ├── embedder.py
│   └── build_index.py
│
├── retrieval/
│   └── retriever.py           # ⭐ MAIN MODULE
│
├── llm/                       # (To be implemented)
├── app/                       # (To be implemented)
│
├── test_retriever.py
├── pyproject.toml
└── README.md
```

---

## ⚙️ Setup Instructions

We are using **uv (Python package manager)** for environment setup.

---

### 🔹 Step 1 — Install uv

```bash
pip install uv
```

---

### 🔹 Step 2 — Clone Repository

```bash
git clone https://github.com/YOUR_USERNAME/bank-staff-rag.git
cd bank-staff-rag
```

---

### 🔹 Step 3 — Install Dependencies

```bash
uv sync
```

This will:

* Create a virtual environment
* Install all required dependencies

---

### 🔹 Step 4 — Activate Environment

**Windows:**

```bash
.venv\Scripts\activate
```

**Mac/Linux:**

```bash
source .venv/bin/activate
```

---

### 🔹 Step 5 — Test the System

```bash
uv run -m test_retriever
```

You should see relevant document chunks printed.

---

## 🔍 How to Use Retrieval

```python
from retrieval.retriever import retrieve

chunks = retrieve("What is KYC?")
```

---

### 📦 Output Format

```python
[
  {
    "content": "...",
    "metadata": {
      "page": 14,
      "source": "document.pdf"
    },
    "score": 0.32
  }
]
```

---

## 🚀 Team Responsibilities

---

### 👤 LLM Module (Person 2)

Create file:

```
llm/model.py
```

Implement:

```python
def generate_answer(query, chunks):
    """
    Input:
    - query (str)
    - chunks (retrieved context)

    Output:
    - final answer (str)
    """
```

Requirements:

* Use `chunk["content"]` as context
* Answer ONLY from context
* If answer not found → return "I don't know"
* Avoid hallucination

---

### 👤 UI Module (Person 3)

Create file:

```
app/streamlit_app.py
```

Flow:

```python
query = user_input
chunks = retrieve(query)
answer = generate_answer(query, chunks)
```

Display:

* Final answer
* Sources (page + document name)

---

## 🔗 System Flow

```
User → UI → retrieve() → chunks → LLM → answer → UI
```

---

## ⚠️ Important Notes

❌ Do NOT:

* Rebuild embeddings
* Modify vector_store
* Use notebooks for execution

✅ Use only:

```python
retrieve(query)
```

---

## 🧪 Debug Mode

```python
retrieve("KYC documents", debug=True)
```

---

## 🧠 Key Insight

This project depends on:

👉 **Retrieval quality, not just LLM**

---

## 📌 Future Improvements

* Better chunking (section-aware)
* Reranking models
* Hybrid search (keyword + embeddings)
* Conversation memory

---

## 👥 Team Status

* Retrieval → ✅ Completed
* LLM → 🔄 In Progress
* UI → 🔄 In Progress

---

## 📞 Contact

If something breaks, contact the project owner.
