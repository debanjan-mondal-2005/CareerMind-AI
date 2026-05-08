import os
import json
from pathlib import Path

import numpy as np
# pyrefly: ignore [missing-import]
from sentence_transformers import SentenceTransformer

PROJECT_ROOT = Path(__file__).resolve().parents[2]
VECTOR_DB_PATH = PROJECT_ROOT / "backend" / "rag" / "vector_db.json"

# Lightweight embedding model (downloads once, ~90 MB)
EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"

# Cache the model globally to avoid reloading on every request
_embedding_model = None

def get_embedding_model():
    global _embedding_model
    if _embedding_model is None:
        _embedding_model = SentenceTransformer(EMBEDDING_MODEL_NAME)
    return _embedding_model

_vector_db = None

def load_vector_db():
    global _vector_db
    if _vector_db is None:
        if not VECTOR_DB_PATH.exists():
            raise FileNotFoundError("vector_db.json not found. Please run build_vector_db.py first.")
        with open(VECTOR_DB_PATH, "r", encoding="utf-8") as f:
            _vector_db = json.load(f)
    return _vector_db

def expand_query(query):
    return f"Search for career guidance, skills, roadmaps, and interview prep related to: {query}"

def get_embedding(text):
    """
    Generate embedding for a single text using the local Sentence-Transformer model.
    """
    model = get_embedding_model()
    embedding = model.encode(text, convert_to_numpy=True)
    return embedding

def cosine_similarity(vec1, vec2):
    vec1 = np.array(vec1)
    vec2 = np.array(vec2)
    dot_product = np.dot(vec1, vec2)
    norm_1 = np.linalg.norm(vec1)
    norm_2 = np.linalg.norm(vec2)
    if norm_1 == 0 or norm_2 == 0:
        return 0
    return dot_product / (norm_1 * norm_2)

def retrieve_relevant_chunks(query, top_k=5):
    """
    Retrieve the most relevant chunks from the local vector DB.
    Returns a list of dicts with keys: source, topic, chunk_index, text, score.
    """
    model = get_embedding_model()
    vector_db = load_vector_db()

    expanded_query = expand_query(query)
    query_embedding = get_embedding(expanded_query)

    results = []
    for item in vector_db:
        stored_embedding = item["embedding"]
        score = cosine_similarity(query_embedding, stored_embedding)
        results.append({
            "source": item["source"],
            "topic": item.get("topic", ""),
            "chunk_index": item["chunk_index"],
            "text": item["text"],
            "score": float(score)
        })

    # Sort by score descending
    results = sorted(results, key=lambda x: x["score"], reverse=True)

    # Select top_k, prefer unique sources when possible
    selected = []
    seen_sources = set()
    for result in results:
        if result["source"] not in seen_sources:
            selected.append(result)
            seen_sources.add(result["source"])
        if len(selected) == top_k:
            break
    # If less than top_k due to uniqueness, fill with remaining
    if len(selected) < top_k:
        selected_ids = {(r["source"], r["chunk_index"]) for r in selected}
        for result in results:
            key = (result["source"], result["chunk_index"])
            if key not in selected_ids:
                selected.append(result)
                selected_ids.add(key)
            if len(selected) == top_k:
                break
    return selected

# At the end of retriever.py, add:

def search_chunks(query, chunks, top_k=3, threshold=0.4):
    """Generic search over a list of chunks (each having 'embedding' and 'text')."""
    model = get_embedding_model()
    query_emb = model.encode(query, convert_to_numpy=True)
    results = []
    for chunk in chunks:
        sim = cosine_similarity(query_emb, chunk["embedding"])
        if sim >= threshold:
            results.append({"text": chunk["text"], "score": sim})
    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:top_k]

if __name__ == "__main__":
    query = input("Enter your question: ")
    chunks = retrieve_relevant_chunks(query, top_k=5)
    print("\nTop Relevant Chunks:\n")
    for i, chunk in enumerate(chunks, start=1):
        print(f"Result {i}")
        print(f"Source: {chunk['source']}")
        print(f"Topic: {chunk['topic']}")
        print(f"Score: {chunk['score']:.4f}")
        print(f"Text:\n{chunk['text'][:900]}")
        print("-" * 80)