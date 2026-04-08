from retrieval.retriever import retrieve

query = "house rent allowence per month for group I?"

results = retrieve(query, top_k=3, debug=True)

print("\nFinal Output:\n")
for r in results:
    print(r)