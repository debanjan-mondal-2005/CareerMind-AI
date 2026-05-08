import json
from pathlib import Path
# pyrefly: ignore [missing-import]
from sentence_transformers import SentenceTransformer
import numpy as np

EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"
CHAT_MEMORY_DIR = Path(__file__).resolve().parent / "chat_memories"
CHAT_MEMORY_DIR.mkdir(exist_ok=True)

_model = None

def _get_model():
    global _model
    if _model is None:
        _model = SentenceTransformer(EMBEDDING_MODEL_NAME)
    return _model

def cosine_similarity(vec1, vec2):
    vec1 = np.array(vec1)
    vec2 = np.array(vec2)
    dot = np.dot(vec1, vec2)
    norm1 = np.linalg.norm(vec1)
    norm2 = np.linalg.norm(vec2)
    if norm1 == 0 or norm2 == 0:
        return 0
    return dot / (norm1 * norm2)

def store_chat_memory(student_id, user_question, ai_answer):
    combined = f"Q: {user_question}\nA: {ai_answer}"
    emb = _get_model().encode(combined, convert_to_numpy=True).tolist()
    entry = {"question": user_question, "answer": ai_answer, "embedding": emb}
    db_path = CHAT_MEMORY_DIR / f"chat_{student_id}.json"
    
    if db_path.exists():
        try:
            with open(db_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except: data = []
    else:
        data = []
    
    data.append(entry)
    with open(db_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)

def search_chat_memory(student_id, query, threshold=0.6):
    db_path = CHAT_MEMORY_DIR / f"chat_{student_id}.json"
    if not db_path.exists():
        return None
    
    try:
        with open(db_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except: return None
    
    if not data:
        return None
        
    model = _get_model()
    query_emb = model.encode(query, convert_to_numpy=True)
    
    best_score = -1
    best_entry = None
    
    for entry in data:
        sim = cosine_similarity(query_emb, entry["embedding"])
        if sim > best_score:
            best_score = sim
            best_entry = entry
            
    if best_score >= threshold and best_entry:
        return {"answer": best_entry["answer"], "score": float(best_score)}
    return None