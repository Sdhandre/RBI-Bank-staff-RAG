from retrieval.retriever import retrieve

query = "What is KYC?"
chunks = retrieve(query)

print(chunks)