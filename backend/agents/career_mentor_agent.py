from llm.llm_client import LLMClient
from rag.retriever import retrieve_relevant_chunks          
from rag.pdf_vector_store import search_pdf_vector_db       
from rag.chat_memory import search_chat_memory, store_chat_memory
from rag.embedding_manager import detect_language, clean_response, is_casual_query
import os
# pyrefly: ignore [missing-import]
from tavily import TavilyClient

class CareerMentorAgent:
    def __init__(self):
        self.llm = LLMClient()
        self.student_id = None    
        self.current_pdf = None
        
        tavily_key = os.getenv("TAVILY_API_KEY")
        self.tavily = TavilyClient(api_key=tavily_key) if tavily_key else None

    def set_student_id(self, sid):
        self.student_id = sid

    def set_current_pdf(self, pdf_path: str):
        if os.path.exists(pdf_path):
            self.current_pdf = pdf_path
        else:
            print(f"⚠️ PDF not found at: {pdf_path}")

    def is_image_generation_request(self, user_question: str) -> bool:
        image_keywords = ["generate image", "draw", "create picture", "make a diagram", "visualize", "illustrate"]
        q = user_question.lower()
        return any(kw in q for kw in image_keywords)

    def _build_multi_source_prompt(self, user_question, student_profile, pdf_chunks=None, rag_chunks=None, web_results=None, memory_chunks=None, language="en"):
        profile_text = self.format_student_profile(student_profile) if student_profile else "Not available"
        
        context = ""
        if memory_chunks:
            # memory_chunks is usually a list of dicts from search_chat_memory
            if isinstance(memory_chunks, list) and len(memory_chunks) > 0:
                context += "Past Relevant Conversation:\n"
                for m in memory_chunks:
                    context += f"Q: {m.get('question')}\nA: {m.get('answer')}\n"
                context += "\n"
                
        if pdf_chunks:
            context += "Document Context:\n" + "\n".join([c["text"] for c in pdf_chunks]) + "\n\n"
        if rag_chunks:
            context += "Knowledge Base:\n" + "\n".join([c["text"] for c in rag_chunks]) + "\n\n"
        if web_results:
            context += "Web Search Results:\n"
            for r in web_results:
                context += f"- {r['title']}: {r['content']} (URL: {r['url']})\n"
        
        system_prompt = f"""You are CareerMind AI, a professional AI career mentor.

ABOUT THIS PLATFORM:
CareerMind AI is an advanced career mentorship platform developed by Debanjan Mondal.

Language behavior:
- Detect the language used by the user.
- If the user writes in Bengali script, answer in Bengali script.
- If the user writes in English, answer in English.
- If the user writes in Hindi, answer in Hindi.
- If the user writes in Banglish/Hinglish, answer naturally and briefly.
- Never repeat sentences.
- Never repeat paragraphs.
- Never generate looping text.
- Never repeatedly say you can speak Bengali/Hindi/English.
- Keep responses concise and human-like.
- Avoid robotic transliteration.
- Prefer native Bengali script over transliteration.
- Answer directly and professionally.
- If the user asks a simple question, give a short direct answer.
- Technical terms like Python, SQL, Machine Learning, FastAPI, Docker, etc., MUST stay in English.

Student Profile (Current Facts):
{profile_text}

Additional Context:
{context if context else "No additional context found."}

RESPONSE STRUCTURE (for technical advice/roadmaps only):
1. Career Goal
2. Industry Role Explanation
3. Recommended Tech Stack
4. Learning Phases
5. Timeline
6. Projects Per Phase
7. Industry Skills
8. Deployment & DevOps
9. Interview Preparation
10. What To Learn Next
"""
        user_prompt = f"Question: {user_question}\nAnswer:"
        return system_prompt, user_prompt

    def stream_answer_question(self, student_profile, user_question: str):
        """
        Orchestrates retrieval and generation in a streaming fashion.
        """
        if self.is_image_generation_request(user_question):
            yield "🎨 Generating your image, please wait a moment...\n\n"
            try:
                from image_ai.hf_image_client import generate_image
                url_or_error = generate_image(user_question)
                if url_or_error.startswith("Error:"):
                    yield f"⚠️ {url_or_error}"
                else:
                    yield f"Image generated successfully!\n\nIMAGE_URL:{url_or_error}"
            except Exception as e:
                yield f"⚠️ Failed to generate image: {str(e)}"
            return

        # 1. Detect language and casual intent
        detected_lang = detect_language(user_question)
        casual = is_casual_query(user_question)

        # 2. Context retrieval
        if not student_profile and self.student_id:
            from database.db import get_student_profile_data
            student_profile = get_student_profile_data(self.student_id)
        
        # Limit memory to last 5 relevant messages (History Limit)
        memory_chunks = search_chat_memory(self.student_id, user_question, top_k=5) if self.student_id else []
        
        pdf_chunks = []
        rag_chunks = []
        web_results = []
        
        if not casual:
            # PDF Search (Only if PDF is active or query is PDF-related)
            pdf_related_keywords = ["pdf", "resume", "cv", "file", "document", "uploaded"]
            is_pdf_query = any(kw in user_question.lower() for kw in pdf_related_keywords)
            
            if self.current_pdf or is_pdf_query:
                pdf_chunks = search_pdf_vector_db(self.student_id, user_question) if self.student_id else []
            
            # RAG Search + Deduplication (Lightweight Retrieval)
            raw_rag = retrieve_relevant_chunks(user_question, top_k=5)
            seen = set()
            for c in raw_rag:
                text_clean = c["text"].strip().lower()
                if text_clean not in seen:
                    rag_chunks.append(c)
                    seen.add(text_clean)
            
            print(f"[RAG] Retrieved {len(rag_chunks)} unique knowledge chunks")
            
            # Web Search
            if self.tavily and len(user_question.split()) > 2:
                try:
                    web_results = self.tavily.search(user_question, search_depth="basic")["results"]
                except: pass

        # 3. Build prompts
        system_prompt, user_prompt = self._build_multi_source_prompt(
            user_question, student_profile, pdf_chunks, rag_chunks, web_results, memory_chunks, language=detected_lang
        )
        
        # 4. Stream from LLM with stability constraints (Render Optimized)
        gen_temp = 0.4 if casual else 0.5
        gen_tokens = 250 if casual else 512
        gen_top_p = 0.8
        
        full_response = ""
        for token in self.llm.stream_response(user_prompt, system_prompt=system_prompt, temperature=gen_temp, max_tokens=gen_tokens, top_p=gen_top_p):
            full_response += token
            yield token

        # 5. Cleanup and store
        print(f"[CLEANUP] Processing AI response (length: {len(full_response)})")
        cleaned = clean_response(full_response)
        if self.student_id and cleaned.strip():
            import threading
            threading.Thread(
                target=store_chat_memory, 
                args=(self.student_id, user_question, cleaned),
                daemon=True
            ).start()

    def answer_question(self, student_profile, user_question):
        full_answer = ""
        for token in self.stream_answer_question(student_profile, user_question):
            if "IMAGE_URL:" in token:
                return {"type": "image", "answer": "Image generated.", "url": token.split("IMAGE_URL:")[1]}
            full_answer += token
        return {"type": "text", "answer": clean_response(full_answer), "sources": []}

    def format_student_profile(self, profile):
        if not profile: return "Not available"
        if profile.get("student_type") == "school":
            return f"Name: {profile.get('full_name')}\nGrade: {profile.get('grade_class')}\nGoal: {profile.get('career_goal')}"
        return f"Name: {profile.get('full_name')}\nDegree: {profile.get('degree')}\nGoal: {profile.get('career_goal')}"