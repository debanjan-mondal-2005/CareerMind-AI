import sys
import json
from pathlib import Path

# Add backend to path for standalone execution
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))
if str(PROJECT_ROOT / "backend") not in sys.path:
    sys.path.append(str(PROJECT_ROOT / "backend"))

import numpy as np
from rag.embedding_manager import get_embedding

PROJECT_ROOT = Path(__file__).resolve().parents[2]
VECTOR_DB_PATH = PROJECT_ROOT / "backend" / "rag" / "vector_db.json"

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
    # Keep expansion but let the embedding manager handle the heavy lifting
    return f"Search for career guidance, skills, roadmaps, and interview prep related to: {query}"

def cosine_similarity(vec1, vec2):
    vec1 = np.array(vec1)
    vec2 = np.array(vec2)
    if vec1.shape != vec2.shape:
        # Avoid crashing if user hasn't rebuilt the vector DB after changing models
        print(f"⚠️ Embedding dimension mismatch: {vec1.shape} vs {vec2.shape}. Please run build_vector_db.py.")
        return 0
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
    try:
        vector_db = load_vector_db()
    except Exception as e:
        print(f"Vector DB not available (likely on Render): {e}")
        return []

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
    query_emb = get_embedding(query)
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