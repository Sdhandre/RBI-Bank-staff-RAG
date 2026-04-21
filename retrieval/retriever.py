from langchain_chroma import Chroma
from ingestion.embedder import get_embedding_model

PERSIST_DIRECTORY = "vector_store_nvidia"

# ✅ Load ONCE (important for performance)
_embedding = get_embedding_model()
_vectordb = Chroma(
    persist_directory=PERSIST_DIRECTORY,
    embedding_function=_embedding
)


def retrieve(query: str, top_k: int = 3, debug: bool = False):
    """
    Retrieve top_k relevant chunks for a query.

    Improvements:
    - Avoid duplicate chunks
    - Filter weak results
    - Normalize query
    - Load DB once (faster)
    """

    # ✅ Normalize query
    query = query.lower().strip()

    # ✅ Fetch more candidates for better filtering
    results = _vectordb.similarity_search_with_score(query, k=top_k * 3)

    seen = set()
    filtered = []

    # Print raw scores in debug mode so threshold can be tuned
    if debug:
        print(f"\nQuery: {query}")
        print("Raw candidate scores:")
        for doc, score in results:
            print(f"  score={score:.4f}  | {doc.page_content[:80].strip()}")

    for doc, score in results:
        content = doc.page_content.strip()

        # Skip duplicates
        if content in seen:
            continue

        # Skip very weak matches — threshold tuned for NVIDIA embeddings
        # (ChromaDB cosine distance: 0=identical, 2=opposite; good matches ~1.1–1.4)
        if score > 1.4:
            continue

        seen.add(content)
        filtered.append((doc, score))

        if len(filtered) >= top_k:
            break

    formatted_results = []

    for doc, score in filtered:
        formatted_results.append({
            "content": doc.page_content,
            "metadata": doc.metadata,
            "score": float(score)
        })

    # Debug output
    if debug:
        print(f"Returned {len(formatted_results)} results after filtering:\n")
        for r in formatted_results:
            print(f"Score: {r['score']:.4f}")
            print(r["content"][:200])
            print("---")

    return formatted_results