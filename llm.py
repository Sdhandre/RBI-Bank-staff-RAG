from typing import List, Dict

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from dotenv import load_dotenv
import os

load_dotenv()  # Load environment variables from .env file

# ------------------------------------------------------------------
# CONFIG
# ------------------------------------------------------------------

GEMINI_MODEL = "gemini-3-flash-preview"
OPENROUTER_MODEL = "google/gemini-2.5-flash"  # Use OpenRouter model string format
TEMPERATURE = 0.2                # low = factual
MAX_OUTPUT_TOKENS = 1024

NO_ANSWER_MSG = (
    "I don't know. The documents available do not contain enough "
    "information to answer this question."
)


# ------------------------------------------------------------------
# LOAD LLM
# ------------------------------------------------------------------

def get_llm(provider="gemini"):
    if provider == "openrouter":
        return ChatOpenAI(
            model=OPENROUTER_MODEL,
            temperature=TEMPERATURE,
            max_tokens=MAX_OUTPUT_TOKENS,
            api_key=os.getenv("OPENROUTER_API_KEY"),
            base_url="https://openrouter.ai/api/v1"
        )
    else:
        # Default to Gemini
        return ChatGoogleGenerativeAI(
            model=GEMINI_MODEL,
            temperature=TEMPERATURE,
            max_output_tokens=MAX_OUTPUT_TOKENS
        )


# ------------------------------------------------------------------
# BUILD CONTEXT
# ------------------------------------------------------------------

def build_context(chunks: List[Dict]) -> str:
    if not chunks:
        return "No relevant context found."

    context_parts = []

    for i, chunk in enumerate(chunks, start=1):
        source = chunk["metadata"].get("source", "unknown")
        page = chunk["metadata"].get("page", "?")

        context_parts.append(
            f"[Source {i} | {source} | Page {page}]\n{chunk['content']}"
        )

    return "\n\n".join(context_parts)


# ------------------------------------------------------------------
# MAIN FUNCTION
# ------------------------------------------------------------------

def generate_answer(query: str, chunks: List[Dict], history_text: str = "", provider: str = "gemini") -> str:
    """
    Final RAG answer generator using chosen LLM provider
    """

    # Guard: no context
    if not chunks:
        return NO_ANSWER_MSG

    # Optional: filter weak retrieval (threshold tuned for NVIDIA embeddings)
    if all(chunk["score"] > 1.4 for chunk in chunks):
        return NO_ANSWER_MSG

    context = build_context(chunks)

    prompt = ChatPromptTemplate.from_template("""
You are an expert assistant for bank staff.

STRICT RULES:
- Answer ONLY using the provided context. If the answer is not in the context, say: "{no_answer}"
- Do NOT use outside knowledge.
- Use the CONVERSATION HISTORY below to understand references in the user's latest question (e.g., if they say "what about for Grade B?", treat it as "what about [topic from history] for Grade B?").
- Be clear, structured, and professional.
- Mention source page if relevant.
- IMPORTANT: At the very end of your response, ALWAYS ask a proactive, helpful follow-up question related to the current topic to guide the user.

-----------------------
CONVERSATION HISTORY:
{history}

-----------------------
CONTEXT:
{context}
-----------------------

CURRENT QUESTION:
{query}

-----------------------
Provide a structured answer:
- Key points
- Important conditions (if any)
- Keep it concise
- End with a follow-up question (e.g. "Do you need help with X or Y?")
""")

    llm = get_llm(provider)

    chain = prompt | llm | StrOutputParser()

    response = chain.invoke({
        "context": context,
        "query": query,
        "history": history_text or "No previous history.",
        "no_answer": NO_ANSWER_MSG
    })

    return response.strip()


# ------------------------------------------------------------------
# OPTIONAL: FORMAT SOURCES (FOR UI)
# ------------------------------------------------------------------

def format_sources(chunks: List[Dict]) -> str:
    if not chunks:
        return "No sources found."

    lines = ["Sources:"]
    for i, chunk in enumerate(chunks, start=1):
        source = chunk["metadata"].get("source", "Unknown")
        page = chunk["metadata"].get("page", "?")
        lines.append(f"{i}. {source} — Page {page}")

    return "\n".join(lines)