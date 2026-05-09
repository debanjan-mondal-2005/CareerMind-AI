import os
import json
import numpy as np
from pathlib import Path
from document_ai.pdf_reader import extract_text_from_pdf
from huggingface_hub import InferenceClient

EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
PDF_VECTORS_DIR = Path(__file__).resolve().parent / "pdf_vectors"
PDF_VECTORS_DIR.mkdir(exist_ok=True)

def _get_embeddings(texts):
    """Get embeddings from Hugging Face Cloud API"""
    hf_token = os.getenv("HF_TOKEN")
    if not hf_token:
        print("⚠️ HF_TOKEN is missing. Returning dummy embeddings.")
        return [np.random.rand(384).tolist() for _ in texts]
        
    client = InferenceClient(token=hf_token)
    try:
        # The feature-extraction task returns embeddings
        response = client.feature_extraction(
            text=texts,
            model=EMBEDDING_MODEL_NAME
        )
        return response.tolist() if hasattr(response, 'tolist') else response
    except Exception as e:
        print(f"⚠️ Hugging Face API Error: {e}")
        # Fallback to dummy embeddings if API fails (so app doesn't crash)
        return [np.random.rand(384).tolist() for _ in texts]

def cosine_similarity(vec1, vec2):
    vec1 = np.array(vec1)
    vec2 = np.array(vec2)
    dot = np.dot(vec1, vec2)
    norm1 = np.linalg.norm(vec1)
    norm2 = np.linalg.norm(vec2)
    if norm1 == 0 or norm2 == 0:
        return 0
    return dot / (norm1 * norm2)

def chunk_text(text, chunk_size=400, overlap=80):
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
    for item in data:
        sim = cosine_similarity(query_emb, item["embedding"])
        if sim >= threshold:
            results.append({"text": item["text"], "score": float(sim)})
    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:top_k]