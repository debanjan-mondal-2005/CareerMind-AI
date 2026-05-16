import os
import re
import numpy as np
from typing import List, Union
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env")

# Global variables for caching
_MODEL_CACHE = {}

def get_model():
    """
    Load and cache the embedding model globally (Lazy Loading).
    """
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError:
        print("[EMBEDDING] sentence-transformers package not found.")
        return None

    use_indic = os.getenv("USE_INDIC_EMBEDDINGS", "false").lower() == "true"
    model_name = os.getenv("EMBEDDING_MODEL", "l3cube-pune/indic-sentence-similarity-sbert")
    fallback_model_name = os.getenv("FALLBACK_EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
    
    target_model = model_name if use_indic else fallback_model_name

    if target_model in _MODEL_CACHE:
        # print("[EMBEDDING] Using cached model")
        return _MODEL_CACHE[target_model]

    print(f"[EMBEDDING] Lazy loading model: {target_model}...")
    
    try:
        model = SentenceTransformer(target_model)
        # Ensure we use CPU for Render Free Tier stability
        try:
            model.to("cpu")
        except: pass
        
        _MODEL_CACHE[target_model] = model
        print(f"[EMBEDDING] Model loaded successfully")
        return model
    except Exception as e:
        print(f"[EMBEDDING] Failed to load target model: {e}")
        if target_model != fallback_model_name:
            print(f"[EMBEDDING] Falling back to {fallback_model_name}")
            try:
                model = SentenceTransformer(fallback_model_name)
                try: model.to("cpu")
                except: pass
                _MODEL_CACHE[fallback_model_name] = model
                print(f"[EMBEDDING] Fallback model loaded successfully")
                return model
            except Exception as e2:
                print(f"[EMBEDDING] Critical error: Could not load fallback model: {e2}")
                raise e2
        else:
            raise e

def get_embedding(text: str) -> List[float]:
    """
    Generate a normalized embedding for a single text string.
    """
    try:
        model = get_model()
        if model is None:
            return np.random.rand(384).tolist()
        
        # Ensure we always deal with a single string
        if not isinstance(text, str):
            text = str(text)
        
        # normalize_embeddings=True for better cosine similarity search
        embedding = model.encode(text, normalize_embeddings=True)
        return embedding.tolist()
    except Exception as e:
        print(f"[EMBEDDING] Error generating embedding: {e}")
        # Fallback to a zero vector or random vector if all else fails
        # 384 is the dimension for MiniLM, 768 for many SBERT models
        # We'll try to infer dimension from model if possible
        dim = 384
        if target_model := next(iter(_MODEL_CACHE.values()), None):
            dim = target_model.get_sentence_embedding_dimension()
        return np.random.rand(dim).tolist()

def get_embeddings(texts: List[str]) -> List[List[float]]:
    """
    Generate normalized embeddings for a list of text strings.
    """
    try:
        model = get_model()
        if model is None:
            return [get_embedding(t) for t in texts]
        embeddings = model.encode(texts, normalize_embeddings=True)
        return embeddings.tolist()
    except Exception as e:
        print(f"[EMBEDDING] Error generating embeddings: {e}")
        return [get_embedding(t) for t in texts]

def detect_language(text: str) -> str:
    """
    Detect the language/style of the text using Unicode ranges and heuristics.
    Returns: 'bn', 'hi', 'en', 'bn-en', 'hi-en'
    """
    if not text:
        return "en"

    # Unicode ranges
    # Bengali: \u0980-\u09FF
    # Hindi (Devanagari): \u0900-\u097F
    
    has_bengali = bool(re.search(r'[\u0980-\u09FF]', text))
    has_hindi = bool(re.search(r'[\u0900-\u097F]', text))
    has_english = bool(re.search(r'[a-zA-Z]', text))

    # Detect transliterated Hinglish/Benglish
    # This is trickier. We check for common markers or simple English presence with Indic.
    
    if has_bengali and has_english:
        return "bn-en"
    if has_hindi and has_english:
        return "hi-en"
    if has_bengali:
        return "bn"
    if has_hindi:
        return "hi"
    
    # Check for transliterated Hinglish/Benglish (phonetic English)
    # Common words in Hinglish/Benglish often used in career context
    hinglish_markers = r'\b(hai|mein|ka|ki|ko|ke|ho|chahta|hu|banna|chaiye|shuru|karna)\b'
    benglish_markers = r'\b(ami|hote|chai|korte|hobe|eita|oita|kore|ache|nei)\b'
    
    if re.search(benglish_markers, text.lower()):
        return "bn-en"
    if re.search(hinglish_markers, text.lower()):
        return "hi-en"

    return "en"

def is_casual_query(text: str) -> bool:
    """
    Detect if a query is casual/greeting/language-related to bypass RAG.
    """
    if not text: return False
    
    text_clean = text.lower().strip().replace("?", "")
    
    # 1. Direct short greetings
    greetings = {"hi", "hello", "hey", "hii", "hola", "namaste", "asalam", "ki obostha", "kemon acho", "kaise ho"}
    if text_clean in greetings:
        print("[RAG] Casual chat detected (greeting), bypassing retrieval")
        return True
    
    # 2. Pattern based detection
    casual_patterns = [
        r'^(how are you|kaise ho|kemon acho|ki obostha|whats up|how r u)\b',
        r'(can you|tumi ki|aap kya|aapko|tumi)\s+(speak|talk|kotha bolte|bolte|baat|aati)\s+(bengali|bangla|hindi|english)\b',
        r'^(thank you|thanks|dhanyabad|dhonnobad|shukriya)\b',
        r'^(who are you|tum kon ho|tumi ke|apne ke|aap kaun)\b',
        r'^(who made you|who developed you|tumi ke baniyeche|tumhe kisne banaya)\b',
        r'^(good morning|good afternoon|good evening|good night)\b',
        r'^(bye|goodbye|see you|ok bye)\b',
        r'^(can you|tumi ki)\s+(help|sahajyo|madad)\b'
    ]
    
    for pattern in casual_patterns:
        if re.search(pattern, text_clean):
            print(f"[RAG] Casual chat detected, bypassing retrieval")
            return True
            
    return False

def clean_response(response: str) -> str:
    """
    Aggressively clean response to remove any repeated sentences or paragraphs.
    """
    if not response:
        return ""

    # 1. Split into paragraphs and remove exact duplicates
    paragraphs = response.split('\n\n')
    unique_paragraphs = []
    seen_paragraphs = set()
    for p in paragraphs:
        p_clean = p.strip()
        if not p_clean: continue
        if p_clean.lower() not in seen_paragraphs:
            unique_paragraphs.append(p_clean)
            seen_paragraphs.add(p_clean.lower())
    
    # 2. Split into sentences and remove any sentence that appears more than once
    def deduplicate_sentences(text):
        sentences = re.split(r'(?<=[.!?।])\s+', text)
        final_sentences = []
        seen_sentences = set()
        for s in sentences:
            s_clean = s.strip()
            if not s_clean: continue
            if s_clean.lower() not in seen_sentences:
                final_sentences.append(s_clean)
                seen_sentences.add(s_clean.lower())
        return ' '.join(final_sentences)

    final_output = []
    for p in unique_paragraphs:
        deduped_p = deduplicate_sentences(p)
        if deduped_p:
            final_output.append(deduped_p)
    
    return '\n\n'.join(final_output).strip()

def clean_multilingual_response(response: str) -> str:
    return clean_response(response)

if __name__ == "__main__":
    test_queries = [
        "আমি data scientist হতে চাই",
        "Mujhe AI engineer banna hai",
        "What roadmap should I follow for ML?",
        "Ami machine learning engineer hote chai",
        "मुझे AI Engineer बनना है"
    ]
    
    for q in test_queries:
        lang = detect_language(q)
        print(f"Query: {q} | Detected Language: {lang}")
