from ingestion.loader import load_documents
from ingestion.chunker import split_documents

docs = load_documents("data/pdf")
chunks = split_documents(docs, debug=True)

print("\nTotal chunks:", len(chunks))