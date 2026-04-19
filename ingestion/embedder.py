from langchain_huggingface import HuggingFaceEmbeddings


def get_embedding_model():
    """
    Lightweight embedding model for RAG (suitable for low-memory environments)
    """

    embedding = HuggingFaceEmbeddings(
        model_name="ibm-granite/granite-embedding-30m-english",
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True}
    )

    return embedding