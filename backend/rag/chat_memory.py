import os
import json
from pathlib import Path
import numpy as np
from huggingface_hub import InferenceClient

EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
CHAT_MEMORY_DIR = Path(__file__).resolve().parent / "chat_memories"
CHAT_MEMORY_DIR.mkdir(exist_ok=True)

def _get_embedding(text):
    hf_token = os.getenv("HF_TOKEN")
    if not hf_token:
        print("⚠️ HF_TOKEN is missing. Returning dummy embedding.")
        return np.random.rand(384).tolist()
        
    client = InferenceClient(token=hf_token)
    try:
        response = client.feature_extraction(text=[text], model=EMBEDDING_MODEL_NAME)
        emb = response.tolist() if hasattr(response, 'tolist') else response
        return emb[0] if len(emb) > 0 else np.random.rand(384).tolist()
    except Exception as e:
        print(f"⚠️ Hugging Face API Error in Chat Memory: {e}")
        return np.random.rand(384).tolist()

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
    emb = _get_embedding(combined)
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

def search_chat_memory(student_id, query, threshold=0.3, top_k=3):
    db_path = CHAT_MEMORY_DIR / f"chat_{student_id}.json"
    if not db_path.exists():
        return []
    
    try:
        with open(db_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except: return []
    
    if not data:
        return []
        
    query_emb = _get_embedding(query)
    scored_entries = []
    
    for entry in data:
        sim = cosine_similarity(query_emb, entry["embedding"])
        if sim >= threshold:
            scored_entries.append({
                "question": entry.get("question", ""),
                "answer": entry.get("answer", ""),
                "score": float(sim)
            })
            
    scored_entries.sort(key=lambda x: x["score"], reverse=True)
    return scored_entries[:top_k]