# Bank Staff RAG System Guidelines

## Architecture

This is a Retrieval-Augmented Generation (RAG) system for bank staff to query internal documents.

**3-Layer Pipeline:**
- **Ingestion**: PDF loading → chunking (600 tokens, 150 overlap) → embeddings (BAAI/bge-small-en-v1.5) → Chroma vector store
- **Retrieval**: Similarity search with deduplication and score filtering (threshold 0.6)
- **LLM**: (Pending) Anthropic Claude integration for grounded answers

Key decisions: Local Chroma DB (persistent), CPU embeddings (change to CUDA for GPU), PyMuPDF for PDF processing.

## Build and Test

- Install: `uv sync` (requires uv package manager)
- Run tests: `uv run test_retriever.py`, `uv run test_chunking.py`, `uv run test_integration.py`
- Python 3.13 required (see `.python-version`)

## Conventions

- **Naming**: Snake_case for functions/variables, descriptive names
- **Documentation**: Use docstrings with purpose, args, returns; emojis for visual markers
- **Imports**: Relative imports in ingestion/ (run from correct directory)
- **Testing**: Direct script execution (no pytest framework)
- **Debug**: Use `debug=True` parameter for verbose output

## Pitfalls

- Vector store is pre-built—DO NOT rebuild unless necessary
- First embedder run downloads ~133MB model
- Chroma DB path hardcoded to "vector_store/"—ensure correct working directory
- Import path issues: Run build_index.py from ingestion/ directory

See [README.md](README.md) for project overview and [notebook/pdf_loader.ipynb](notebook/pdf_loader.ipynb) for detailed pipeline walkthrough.