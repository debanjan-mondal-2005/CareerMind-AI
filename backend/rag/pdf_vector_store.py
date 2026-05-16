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
from document_ai.pdf_reader import extract_text_from_pdf
from rag.embedding_manager import get_embedding, get_embeddings

PDF_VECTORS_DIR = Path(__file__).resolve().parent / "pdf_vectors"
PDF_VECTORS_DIR.mkdir(exist_ok=True)

def _get_embeddings(texts):
    """Get embeddings from embedding manager"""
    return get_embeddings(texts)

def cosine_similarity(vec1, vec2):
    vec1 = np.array(vec1)
    vec2 = np.array(vec2)
    if vec1.shape != vec2.shape:
        return -1.0 # Mismatch indicator
    dot = np.dot(vec1, vec2)
    norm1 = np.linalg.norm(vec1)
    norm2 = np.linalg.norm(vec2)
    if norm1 == 0 or norm2 == 0:
        return 0
    return dot / (norm1 * norm2)

def chunk_text(text, chunk_size=800, overlap=150):
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        start = end - overlap
    return chunks

def build_pdf_vector_db(student_id, pdf_path):
    """Extract text, chunk, embed via cloud, save as pdfs_{student_id}.json."""
    try:
        text = extract_text_from_pdf(pdf_path)
    except Exception as e:
        raise RuntimeError(f"Could not extract text: {e}")
    if not text.strip():
        raise ValueError("No readable text in PDF.")
    chunks = chunk_text(text)
    if not chunks:
        raise ValueError("PDF too short.")
    
    # Get embeddings for all chunks at once via Cloud API
    print("☁️ Calling Hugging Face Cloud API for embeddings...")
    embeddings = _get_embeddings(chunks)
    
    vector_data = []
    for idx, chunk in enumerate(chunks):
        emb = embeddings[idx] if idx < len(embeddings) else embeddings[0]
        vector_data.append({"id": f"pdf_{idx}", "text": chunk, "embedding": emb})
        
    db_path = PDF_VECTORS_DIR / f"pdfs_{student_id}.json"
    with open(db_path, "w", encoding="utf-8") as f:
        json.dump(vector_data, f, ensure_ascii=False)
    return str(db_path), len(chunks)

def search_pdf_vector_db(student_id, query, top_k=3, threshold=0.4):
    db_path = PDF_VECTORS_DIR / f"pdfs_{student_id}.json"
    if not db_path.exists():
        return []
    with open(db_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    # Get embedding for search query via Cloud API
    embeddings = _get_embeddings([query])
    query_emb = embeddings[0]
    
    results = []
    mismatch_warned = False
    for item in data:
        sim = cosine_similarity(query_emb, item["embedding"])
        if sim == -1.0:
            if not mismatch_warned:
                print(f"⚠️ PDF context for Student {student_id} is outdated (dimension mismatch). Skipping PDF search. Please re-upload PDF to sync.")
                mismatch_warned = True
            return [] # Return empty if dimensions mismatch
        if sim >= threshold:
            results.append({"text": item["text"], "score": float(sim)})
    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:top_k]