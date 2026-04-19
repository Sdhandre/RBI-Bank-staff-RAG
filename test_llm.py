from retrieval.retriever import retrieve
from llm import generate_answer

query = "What does Competent Authority means?"

print("\n🔍 Query:", query)

chunks = retrieve(query, debug=True)

print("\n🧠 Generating answer...\n")

answer = generate_answer(query, chunks)

print("✅ Final Answer:\n")
print(answer)