from langchain_huggingface import HuggingFaceEmbeddings


def get_embedding_model():
    """
    Lightweight embedding model for RAG (suitable for low-memory environments)
    """

    embedding = HuggingFaceEmbeddings(
        model_name="ibm-granite/granite-embedding-125m-english",
        model_kwargs={"device": "cpu"},   # keep CPU for Render
        encode_kwargs={"normalize_embeddings": True}
    )

    return embedding