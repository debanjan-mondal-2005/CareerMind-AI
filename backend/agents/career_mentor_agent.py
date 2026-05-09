from llm.llm_client import LLMClient
from rag.retriever import retrieve_relevant_chunks          
from rag.pdf_vector_store import search_pdf_vector_db       
from rag.chat_memory import search_chat_memory, store_chat_memory
import os
# pyrefly: ignore [missing-import]
from tavily import TavilyClient

class CareerMentorAgent:
    def __init__(self):
        self.llm = LLMClient()
        self.student_id = None    
        self.current_pdf = None
        
        tavily_key = os.getenv("TAVILY_API_KEY")
        self.web_client = TavilyClient(api_key=tavily_key) if tavily_key else None

    def set_student_id(self, sid):
        self.student_id = sid

    def set_current_pdf(self, pdf_path: str):
        if os.path.exists(pdf_path):
            self.current_pdf = pdf_path
        else:
            raise FileNotFoundError(f"PDF not found: {pdf_path}")

    def is_image_generation_request(self, user_question: str) -> bool:
        image_keywords = [
            "generate image", "draw", "create picture", "make a diagram",
            "visualize", "illustrate", "create an image", "generate a diagram",
            "image of", "draw a", "paint a", "generate a picture"
        ]
        q = user_question.lower()
        return any(kw in q for kw in image_keywords)

    def _build_multi_source_prompt(self, user_question, student_profile, pdf_chunks=None, rag_chunks=None, web_results=None):
        formatted_profile = self.format_student_profile(student_profile)
        
        pdf_text = ""
        if pdf_chunks:
            pdf_text = "\n".join([c["text"] for c in pdf_chunks])
            
        rag_text = ""
        if rag_chunks:
            rag_text = "\n".join([c["text"] for c in rag_chunks])
            
        web_text = ""
        if web_results:
            for i, res in enumerate(web_results, start=1):
                web_text += f"Source {i}: {res['title']}\nContent: {res['content']}\nURL: {res['url']}\n\n"

        prompt = f"""You are CareerMind AI, a professional and personalized Career Mentor.
        
Student Profile:
{formatted_profile}

Information Sources:
1. Student Profile (Primary): Use this for all personal questions about the student (name, skills, goals).
2. Uploaded Document (PDF): {pdf_text if pdf_text else "No relevant info found."}
3. Internal Career Database: {rag_text if rag_text else "No relevant info found."}
4. Web Search Results: {web_text if web_text else "No relevant info found."}

Question: "{user_question}"

Instructions:
1. Act as a Career Mentor. Be encouraging and professional.
2. PRIORITY: Student Profile > PDF > Internal Database > Web Search.
3. If the question is about the student personally (e.g., "what do you know about me", "my name", "my skills"), you MUST answer using the Student Profile provided above. NEVER use web search results for personal information about the student.
4. Only use Web Search for general career advice, company information, or market trends.
5. If the user just says "Hello" or "Hi", reply warmly as CareerMind AI and offer career assistance.
6. Include source URLs ONLY if you used web search results.
7. Be direct and helpful.

Answer:"""
        return prompt

    def _build_answer_prompt(self, context_chunks, user_question, student_profile=None):
        context = "\n\n".join([c["text"] for c in context_chunks])
        profile_text = self.format_student_profile(student_profile) if student_profile else "Not available"
        
        return f"""You are CareerMind AI, a precise career mentor. Answer the student's question using the Student Profile and Context below.

Student Profile:
{profile_text}

Context from Document:
{context}

Question: {user_question}

Instructions:
1. If the answer is present in the document context or student profile, provide it directly and concisely.
2. Do NOT summarize the entire context; only answer the specific question asked.
3. If the information is not present in either, respond ONLY with "NOT_FOUND_IN_CONTEXT".
4. Be direct. If asked for a name, just give the name.
5. DO NOT include "Student Profile", "Context from Document", or "Instructions" in your final response. Just give the answer.

Answer:"""

    def _answer_from_context(self, user_question, context_chunks, student_profile=None):
        if not context_chunks:
            return None
        # This is a legacy method, keeping for backward compatibility if needed elsewhere
        context = "\n\n".join([c["text"] for c in context_chunks])
        prompt = f"Answer this question based on context:\nContext: {context}\nQuestion: {user_question}"
        return self.llm.generate_response(prompt)

    def is_llm_error(self, response):
        if not response:
            return True
        resp = str(response).lower()
        return any(kw in resp for kw in [
            "llm error", "resource_exhausted", "429",
            "quota", "rate limit", "generate_content_free_tier"
        ])

    def _search_web(self, query):
        if not self.web_client:
            return None
        try:
            # Simple web search
            response = self.web_client.search(query=query, max_results=3, search_depth="advanced")
            return response.get("results", [])
        except Exception as e:
            print(f"Web search error: {e}")
            return None

    def _answer_from_web(self, user_question, web_results, student_profile):
        if not web_results:
            return None
        
        web_context = ""
        for i, res in enumerate(web_results, start=1):
            web_context += f"Source {i}: {res['title']}\nContent: {res['content']}\nURL: {res['url']}\n\n"
        
        prompt = f"""You are CareerMind AI, a helpful and precise career mentor.
        
Student Question: "{user_question}"

I searched the web because this information was not found in the student's uploaded document.

Web Results:
{web_context}

Instructions:
1. If the question is about the student personally and the web results are clearly unrelated, state that you couldn't find it in their document.
2. If the question is general (e.g., "latest trends", "how to learn X", "job openings"), answer it thoroughly using the web results.
3. Be helpful, concise, and personalized based on the student's profile.
4. Always include the source URLs at the end.

Answer:"""
        return self.llm.generate_response(prompt)

    def answer_question(self, student_profile, user_question):
        # Image generation
        if self.is_image_generation_request(user_question):
            try:
                from image_ai.hf_image_client import generate_image
                url = generate_image(user_question)
                return {"type": "image", "url": url,
                        "answer": "Image generated successfully! Now you can download it.",
                        "sources": [], "fallback": False}
            except Exception as e:
                return {"type": "error",
                        "answer": f"Failed to generate image: {str(e)}",
                        "sources": [], "fallback": False}

        if not self.student_id:
            answer = self.llm.generate_response(user_question)
            return {"answer": answer, "sources": [], "fallback": False}

        # 1. PDF Search
        pdf_chunks = []
        if self.current_pdf:
            pdf_chunks = search_pdf_vector_db(self.student_id, user_question, top_k=5, threshold=0.15)
            try:
                from document_ai.pdf_reader import extract_text_from_pdf
                pdf_text = extract_text_from_pdf(self.current_pdf)
                keywords = [w.strip("?,.!") for w in user_question.lower().split() if len(w) > 3]
                relevant_lines = [l for l in pdf_text.split('\n') if any(kw in l.lower() for kw in keywords)]
                if relevant_lines:
                    pdf_chunks = (pdf_chunks or []) + [{"text": "\n".join(relevant_lines[:10]), "score": 1.0}]
            except: pass

        # 2. RAG Search
        rag_chunks = retrieve_relevant_chunks(user_question, top_k=3)

        # 3. Web Search
        web_results = []
        q_lower = user_question.lower()
        
        # Expanded personal and conversational terms
        personal_terms = ["my name", "my university", "my cgpa", "my gpa", "my project", "my email", "i study", "about me", "know about me", "who am i"]
        conversational_terms = ["hello", "hi", "hey", "how are you", "good morning", "good evening", "what's up"]
        
        is_personal = any(term in q_lower for term in personal_terms)
        is_conversational = any(q_lower == term or q_lower.startswith(term + " ") for term in conversational_terms)
        
        # ONLY search web if NOT personal and NOT conversational
        if self.web_client and not is_personal and not is_conversational:
            # Also don't search web if it's a simple career goal check
            if len(q_lower.split()) > 2: 
                web_results = self._search_web(user_question)

        # 4. Generate Response
        prompt = self._build_multi_source_prompt(user_question, student_profile, pdf_chunks, rag_chunks, web_results)
        answer = self.llm.generate_response(prompt)
        
        # 5. Result metadata
        sources = []
        if pdf_chunks: sources.append({"source": "Uploaded PDF", "topic": "Document"})
        if web_results: sources.extend([{"source": res['title'], "url": res["url"]} for res in web_results[:2]])
        
        store_chat_memory(self.student_id, user_question, answer)
        return {"answer": answer, "sources": sources, "fallback": bool(web_results)}

    def stream_answer_question(self, student_profile, user_question):
        if self.is_image_generation_request(user_question):
            yield "🎨 Generating your image, please wait a moment...\n\n"
            try:
                from image_ai.hf_image_client import generate_image
                url_or_error = generate_image(user_question)
                
                if url_or_error.startswith("Error:"):
                    yield f"⚠️ {url_or_error}"
                else:
                    yield f"Image generated successfully! Now you can download it.\n\nIMAGE_URL:{url_or_error}"
            except Exception as e:
                yield f"⚠️ Failed to generate image: {str(e)}"
            return

        # 1. PDF Search
        pdf_chunks = []
        if self.current_pdf:
            from rag.pdf_vector_store import search_pdf_vector_db
            pdf_chunks = search_pdf_vector_db(self.student_id, user_question, top_k=5, threshold=0.15)
            try:
                from document_ai.pdf_reader import extract_text_from_pdf
                pdf_text = extract_text_from_pdf(self.current_pdf)
                keywords = [w.strip("?,.!") for w in user_question.lower().split() if len(w) > 3]
                relevant_lines = [l for l in pdf_text.split('\n') if any(kw in l.lower() for kw in keywords)]
                if relevant_lines:
                    pdf_chunks = (pdf_chunks or []) + [{"text": "\n".join(relevant_lines[:10]), "score": 1.0}]
            except: pass

        # 2. RAG Search
        rag_chunks = retrieve_relevant_chunks(user_question, top_k=3)

        # 3. Web Search
        web_results = []
        q_lower = user_question.lower()
        
        # Expanded personal and conversational terms
        personal_terms = ["my name", "my university", "my cgpa", "my gpa", "my project", "my email", "i study", "about me", "know about me", "who am i"]
        conversational_terms = ["hello", "hi", "hey", "how are you", "good morning", "good evening", "what's up"]
        
        is_personal = any(term in q_lower for term in personal_terms)
        is_conversational = any(q_lower == term or q_lower.startswith(term + " ") for term in conversational_terms)
        
        # ONLY search web if NOT personal and NOT conversational
        if self.web_client and not is_personal and not is_conversational:
            # Also don't search web if it's a simple career goal check
            if len(q_lower.split()) > 2: 
                web_results = self._search_web(user_question)

        # 4. Unified Prompting & Streaming
        prompt = self._build_multi_source_prompt(user_question, student_profile, pdf_chunks, rag_chunks, web_results)
        for token in self.llm.stream_response(prompt):
            yield token

    # ---- helper for streaming (copied from old version) ----
    def format_student_profile(self, profile):
        return f"""
Student Profile:
Name: {profile.get("full_name", "Student")}
Degree: {profile.get("degree", "")}
Semester: {profile.get("semester", "")}
Specialization: {profile.get("specialization", "")}
Career Goal: {profile.get("career_goal", "")}
Current Skills: {profile.get("skills", "")}
Weak Areas: {profile.get("weak_areas", "")}
Daily Study Hours: {profile.get("daily_study_hours", "")}
""".strip()

    def format_rag_context(self, chunks):
        context = ""
        for i, chunk in enumerate(chunks, start=1):
            context += f"""
Context {i}
Source: {chunk["source"]}
Topic: {chunk.get("topic", "")}
Similarity Score: {chunk["score"]:.4f}
Text:
{chunk["text"]}
"""
        return context.strip()

    def build_pdf_aware_prompt(self, student_profile, user_question, rag_chunks, pdf_text=None):
        formatted_profile = self.format_student_profile(student_profile)
        rag_context = self.format_rag_context(rag_chunks)
        pdf_section = ""
        if pdf_text:
            pdf_section = f"""
***** Uploaded Document Content *****
{self._truncate_text(pdf_text, 3000)}
"""
        prompt = f"""You are CareerMind AI, a precise career mentor. Answer the question directly and concisely using the context provided.
Do NOT summarize the entire profile unless asked. Just answer the specific question.

{formatted_profile}

{pdf_section}

RAG Context:
{rag_context}

Question: {user_question}
Answer:"""
        return prompt

    def _truncate_text(self, text, max_chars):
        if len(text) <= max_chars:
            return text
        return text[:max_chars].rsplit(' ', 1)[0] + "..."