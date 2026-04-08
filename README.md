# Bank Staff RAG

A Retrieval-Augmented Generation (RAG) system designed for bank staff to query and retrieve information from PDF documents using natural language.

## Features

- **PDF Document Processing**: Load and process PDF files from a specified directory
- **Text Chunking**: Split documents into manageable chunks with configurable overlap
- **Vector Embeddings**: Generate embeddings using Sentence Transformers (all-MiniLM-L6-v2)
- **Vector Database**: Store and retrieve documents using ChromaDB
- **Semantic Search**: Perform similarity search on document chunks
- **RAG Pipeline**: End-to-end retrieval and generation pipeline

## Project Structure

```
bank_staff_rag/
├── main.py                 # Main entry point
├── pyproject.toml          # Project configuration and dependencies
├── requirements.txt        # Additional dependencies
├── README.md              # This file
├── data/
│   ├── pdf/               # Directory for PDF documents
│   └── vector_store/      # Generated vector database (ignored in git)
├── notebook/
│   ├── pdf_loader.ipynb   # Complete RAG pipeline implementation
│   └── document.ipynb     # Data ingestion experiments
└── .gitignore             # Git ignore rules
```

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd bank-staff-rag
   ```

2. **Set up Python environment**:
   ```bash
   # Using uv (recommended)
   uv sync

   # Or using pip
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Install dependencies**:
   ```bash
   uv pip install -e .
   # or
   pip install -e .
   ```

## Usage

### Running the Notebooks

1. **PDF Loader Pipeline** (`notebook/pdf_loader.ipynb`):
   - Loads PDF documents from `data/pdf/`
   - Splits text into chunks
   - Generates embeddings
   - Creates vector store
   - Implements RAG retriever for querying

2. **Data Ingestion** (`notebook/document.ipynb`):
   - Experimental notebook for document loading
   - Uses LangChain document loaders

### Key Components

#### EmbeddingManager
- Loads Sentence Transformer model
- Generates embeddings for text chunks
- Configurable model selection

#### VectorStore
- Manages ChromaDB collection
- Adds documents with metadata
- Performs similarity search

#### RAGRetriever
- Combines vector search with document retrieval
- Returns relevant document chunks for queries

## Configuration

- **Chunk Size**: Default 1000 characters with 200 overlap
- **Embedding Model**: `all-MiniLM-L6-v2` (384 dimensions)
- **Vector Database**: ChromaDB with persistent storage

## Dependencies

- `langchain` - Framework for LLM applications
- `sentence-transformers` - Text embeddings
- `chromadb` - Vector database
- `pymupdf` - PDF processing
- `faiss-cpu` - Vector similarity search
- `ipykernel` - Jupyter notebook support

## Development

- Python 3.13+
- Uses `uv` for dependency management
- Jupyter notebooks for experimentation
- ChromaDB for vector storage

## License

[Add license information here]

## Contributing

[Add contribution guidelines here]
