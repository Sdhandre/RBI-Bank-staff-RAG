from langchain_text_splitters import RecursiveCharacterTextSplitter


def split_documents(documents, chunk_size=600, chunk_overlap=150, debug=False):
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
        separators=["\n\n", "\n", ".", " "]
    )

    split_docs = text_splitter.split_documents(documents)

    # Enhance metadata
    for i, doc in enumerate(split_docs):
        doc.metadata["chunk_id"] = i
        doc.metadata["chunk_length"] = len(doc.page_content)

    if debug:
        print(f"Split {len(documents)} documents into {len(split_docs)} chunks.\n")
        print("Example chunk:")
        print(split_docs[0].page_content[:200])
        print(split_docs[0].metadata)

    return split_docs