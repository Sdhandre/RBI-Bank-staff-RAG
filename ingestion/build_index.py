from ingestion.loader import load_documents
from ingestion.chunker import split_documents
from ingestion.embedder import get_embedding_model
from langchain_chroma import Chroma




def build_vectorstore(
    data_path: str = "data/pdf",
    persist_directory: str = "vector_store_ibm30b"
):
    """
    Builds and persists the Chroma vector database.

    Steps:
    1. Load documents
    2. Split into chunks
    3. Generate embeddings
    4. Store in Chroma DB
    """

    print("🔹 Loading documents...")
    documents = load_documents(data_path)

    print("🔹 Splitting documents into chunks...")
    chunks = split_documents(documents)

    print(f"🔹 Total chunks created: {len(chunks)}")

    print("🔹 Loading embedding model...")
    embedding = get_embedding_model()

    print("🔹 Creating vector store (Chroma)...")
    vectordb = Chroma.from_documents(
        documents=chunks,
        embedding=embedding,
        persist_directory=persist_directory
    )



    print("✅ Vector store created successfully!")

    return vectordb


if __name__ == "__main__":
    build_vectorstore()