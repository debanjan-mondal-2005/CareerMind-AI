import os
import json
import sys
from pathlib import Path

# No need for dotenv or genai
from sentence_transformers import SentenceTransformer

# Add backend folder path (for possible imports)
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

PROJECT_ROOT = Path(__file__).resolve().parents[2]
KNOWLEDGE_BASE_DIR = PROJECT_ROOT / "knowledge_base"
VECTOR_DB_PATH = PROJECT_ROOT / "backend" / "rag" / "vector_db.json"

# Use the same lightweight model as retriever.py
EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"

def get_embedding_model():
    """Load Sentence-Transformer embedding model."""
    return SentenceTransformer(EMBEDDING_MODEL_NAME)

def read_txt_files():
    """Read all .txt files from the knowledge base folder."""
    documents = []
    for file_path in sorted(KNOWLEDGE_BASE_DIR.glob("*.txt")):
        text = file_path.read_text(encoding="utf-8")
        documents.append({
            "source": file_path.name,
            "text": text
        })
    return documents

def get_document_topic(source_name):
    """Infer a topic label from the filename."""
    source_name = source_name.lower()
    if "data_scientist" in source_name:
        return "Data Scientist skills, roadmap, job requirements, projects, interview preparation"
    elif "software_engineer" in source_name:
        return "Software Engineer skills, DSA, backend, frontend, projects, interview preparation"
    elif "ai_ml" in source_name:
        return "AI ML Engineer skills, machine learning, deep learning, NLP, computer vision, deployment"
    elif "data_analyst" in source_name:
        return "Data Analyst skills, SQL, Excel, Power BI, dashboards, business analysis"
    elif "mlops" in source_name:
        return "MLOps skills, deployment, Docker, CI CD, monitoring, data drift, model drift"
    elif "job_skills" in source_name:
        return "Job skill requirements for different roles"
    elif "project" in source_name:
        return "Project ideas, project recommendations, portfolio projects"
    elif "interview" in source_name:
        return "Interview questions, interview preparation, technical and HR questions"
    elif "resume" in source_name or "ats" in source_name:
        return "Resume ATS guidelines, resume improvement, job matching"
    elif "rag" in source_name or "agents" in source_name:
        return "RAG, AI agents, embeddings, vector search, agentic AI"
    elif "deployment" in source_name or "monitoring" in source_name:
        return "Deployment, MLOps, monitoring, logging, data drift, model drift"
    else:
        return "Career guidance, skills, roadmap, projects, interview preparation"

def chunk_text(text, chunk_size=400, overlap=80):
    """Split text into overlapping chunks."""
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        start = end - overlap
    return chunks

def build_embedding_text(source, topic, chunk):
    """Create a rich text representation used for embedding."""
    return f"""
Source File: {source}
Document Topic: {topic}
Purpose: This content is used for CareerMind AI RAG retrieval.
Relevant Keywords: career guidance, required skills, roadmap, job requirements, interview preparation, project recommendation, MLOps, deployment.
Content:
{chunk}
""".strip()

def build_vector_db():
    model = get_embedding_model()
    documents = read_txt_files()

    if not documents:
        print("No .txt files found in knowledge_base folder.")
        return

    vector_data = []
    print(f"Found {len(documents)} documents.")

    for doc in documents:
        source = doc["source"]
        topic = get_document_topic(source)
        chunks = chunk_text(doc["text"])

        print(f"Processing {source} → {len(chunks)} chunks")

        for idx, chunk in enumerate(chunks):
            embedding_text = build_embedding_text(source, topic, chunk)
            # Generate embedding using the local model (return list of floats -> store as list)
            embedding = model.encode(embedding_text, convert_to_numpy=True).tolist()

            vector_data.append({
                "id": f"{source}_chunk_{idx}",
                "source": source,
                "topic": topic,
                "chunk_index": idx,
                "text": chunk,
                "embedding_text": embedding_text,
                "embedding": embedding        # list of floats
            })

    with open(VECTOR_DB_PATH, "w", encoding="utf-8") as f:
        json.dump(vector_data, f, ensure_ascii=False)

    print("\nVector database created successfully!")
    print(f"Saved at: {VECTOR_DB_PATH}")
    print(f"Total chunks: {len(vector_data)}")

if __name__ == "__main__":
    build_vector_db()