from langchain_huggingface import HuggingFaceEmbeddings


def get_embedding_model():
    """
    Loads and returns the embedding model.

    Returns:
        HuggingFaceEmbeddings: embedding model compatible with LangChain + Chroma
    """

    embedding = HuggingFaceEmbeddings(
        model_name="BAAI/bge-small-en-v1.5",
        model_kwargs={"device": "cpu"},   # change to "cuda" if GPU available
        encode_kwargs={"normalize_embeddings": True}
    )

    return embedding