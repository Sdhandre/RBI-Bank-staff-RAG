"""
app/app.py — Flask API for Bank Staff RAG Chatbot
Session management via MongoDB (Render Compatible).
"""

import sys
import os
import traceback
import uuid
import json
from datetime import datetime

# ─── Path fix: ensure repo root is on sys.path AND is the CWD ───────────────
# Chroma uses a *relative* path ("vector_store/"). Pinning CWD to the repo
# root guarantees retriever.py always opens the real, pre-built index.
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
os.chdir(ROOT)   # ← must happen BEFORE importing retriever (Chroma loads at import time)

from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from pymongo import MongoClient

# ─── Import backend (vector DB loads ONCE at module import time) ──────────────
from retrieval.retriever import retrieve
from llm import generate_answer

# ─── App setup ───────────────────────────────────────────────────────────────
app = Flask(__name__, template_folder="templates", static_folder="static")
CORS(app)

# ─── MongoDB session store ───────────────────────────────────────────────────
# Use environment variable for MongoDB URI, default to localhost for local dev
MONGO_URI = os.environ.get("MONGO_URI", "mongodb://localhost:27017/")
mongo_client = MongoClient(MONGO_URI)
db = mongo_client["bank_staff_rag"]

# Collections
sessions_col = db["sessions"]
messages_col = db["messages"]


# ─── Helpers ─────────────────────────────────────────────────────────────────

def _extract_sources(chunks: list) -> list:
    sources, seen = [], set()
    for chunk in chunks:
        meta   = chunk.get("metadata", {})
        source = meta.get("source", "Unknown document")
        page   = meta.get("page", "?")
        key    = f"{source}::{page}"
        if key not in seen:
            seen.add(key)
            sources.append({"source": source, "page": page})
    return sources


def now_str():
    return datetime.now().isoformat()


# ─── Routes — UI ─────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "db": "mongodb"}), 200


# ─── Routes — Sessions ───────────────────────────────────────────────────────

@app.route("/sessions", methods=["GET"])
def list_sessions():
    """Return all sessions, optionally filtered by title search."""
    q = request.args.get("q", "").strip()
    
    query = {}
    if q:
        query["title"] = {"$regex": q, "$options": "i"}
        
    # Sort by updated_at descending
    cursor = sessions_col.find(query).sort("updated_at", -1)
    
    sessions = []
    for doc in cursor:
        sessions.append({
            "id": doc["id"],
            "title": doc["title"],
            "created_at": doc["created_at"],
            "updated_at": doc["updated_at"]
        })
        
    return jsonify(sessions), 200


@app.route("/sessions", methods=["POST"])
def create_session():
    """Create a blank session and return its id."""
    sid = str(uuid.uuid4())
    session_doc = {
        "id": sid,
        "title": "New Chat",
        "created_at": now_str(),
        "updated_at": now_str()
    }
    sessions_col.insert_one(session_doc)
    return jsonify({"id": sid, "title": "New Chat"}), 201


@app.route("/sessions/<sid>", methods=["GET"])
def get_session(sid):
    """Return session metadata + full message history."""
    session = sessions_col.find_one({"id": sid})
    if not session:
        return jsonify({"error": "Session not found"}), 404
        
    cursor = messages_col.find({"session_id": sid}).sort("created_at", 1)
    
    messages = []
    for doc in cursor:
        messages.append({
            "role":       doc["role"],
            "content":    doc["content"],
            "sources":    doc.get("sources", []),
            "created_at": doc["created_at"],
        })
        
    return jsonify({
        "session": {
            "id": session["id"],
            "title": session["title"],
            "created_at": session["created_at"],
            "updated_at": session["updated_at"]
        }, 
        "messages": messages
    }), 200


@app.route("/sessions/<sid>", methods=["PATCH"])
def rename_session(sid):
    """Rename an existing session."""
    data  = request.get_json(force=True)
    title = (data.get("title") or "").strip()
    if not title:
        return jsonify({"error": "Title required"}), 400
        
    result = sessions_col.update_one(
        {"id": sid},
        {"$set": {"title": title, "updated_at": now_str()}}
    )
    
    if result.matched_count == 0:
         return jsonify({"error": "Session not found"}), 404
         
    return jsonify({"ok": True}), 200


@app.route("/sessions/<sid>", methods=["DELETE"])
def delete_session(sid):
    """Delete session and all its messages."""
    sessions_col.delete_one({"id": sid})
    messages_col.delete_many({"session_id": sid})
    return jsonify({"ok": True}), 200


# ─── Routes — Chat ───────────────────────────────────────────────────────────

@app.route("/chat", methods=["POST"])
def chat():
    """
    POST /chat
    Body:   { "query": "...", "session_id": "...", "provider": "..." }
    Returns: { "answer": "...", "sources": [...] }
    """
    try:
        data = request.get_json(force=True)

        query = (data.get("query") or "").strip()
        sid   = (data.get("session_id") or "").strip()
        provider = data.get("provider", "gemini")

        if not query:
            return jsonify({"error": "Query must not be empty"}), 400
        if not sid:
            return jsonify({"error": "Missing 'session_id'"}), 400

        # Verify session exists
        session = sessions_col.find_one({"id": sid})
        if not session:
            return jsonify({"error": "Session not found"}), 404

        # ── Fetch Chat History ──────────────────────────────────────────────────
        history_text = ""
        # Fetch up to the last 6 messages
        cursor = messages_col.find({"session_id": sid}).sort("created_at", 1)
        recent_msgs = list(cursor)[-6:]
        
        if recent_msgs:
            history_parts = []
            for m in recent_msgs:
                role_name = "User" if m["role"] == "user" else "Assistant"
                history_parts.append(f"{role_name}: {m['content']}")
            history_text = "\n\n".join(history_parts)

        # ── RAG pipeline ──────────────────────────────────────────────────────
        chunks  = retrieve(query)
        answer  = generate_answer(query, chunks, history_text, provider)
        sources = _extract_sources(chunks)

        # ── Persist to DB ─────────────────────────────────────────────────────
        # Save user message
        messages_col.insert_one({
            "id": str(uuid.uuid4()),
            "session_id": sid,
            "role": "user",
            "content": query,
            "sources": [],
            "created_at": now_str()
        })
        
        # Save bot message
        messages_col.insert_one({
            "id": str(uuid.uuid4()),
            "session_id": sid,
            "role": "bot",
            "content": answer,
            "sources": sources,
            "created_at": now_str()
        })
        
        # Auto-generate title from first message
        if session.get("title") == "New Chat":
            auto_title = query[:60] + ("…" if len(query) > 60 else "")
            sessions_col.update_one(
                {"id": sid},
                {"$set": {"title": auto_title, "updated_at": now_str()}}
            )
        else:
            sessions_col.update_one(
                {"id": sid},
                {"$set": {"updated_at": now_str()}}
            )

        return jsonify({"answer": answer, "sources": sources}), 200

    except Exception:
        app.logger.error("Error in /chat:\n" + traceback.format_exc())
        return jsonify({
            "error": "An internal error occurred. Please try again.",
            "detail": traceback.format_exc()
        }), 500


# ─── Entry point ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=5000, use_reloader=False)
