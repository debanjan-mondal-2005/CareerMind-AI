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

    def _build_multi_source_prompt(self, user_question, student_profile, pdf_chunks=None, rag_chunks=None, web_results=None, memory_chunks=None):
        profile_text = self.format_student_profile(student_profile) if student_profile else "Not available"
        
        context = ""
        if memory_chunks:
            context += "Past Relevant Conversation:\n" + f"Q: {memory_chunks.get('question')}\nA: {memory_chunks.get('answer')}" + "\n\n"
        if pdf_chunks:
            context += "Document Context:\n" + "\n".join([c["text"] for c in pdf_chunks]) + "\n\n"
        if rag_chunks:
            context += "Knowledge Base:\n" + "\n".join([c["text"] for c in rag_chunks]) + "\n\n"
        if web_results:
            context += "Web Search Results:\n"
            for r in web_results:
                context += f"- {r['title']}: {r['content']} (URL: {r['url']})\n"
        
        system_prompt = f"""You are CareerMind AI, a world-class professional career mentor.
        
ABOUT THIS PLATFORM:
CareerMind AI is an advanced AI-powered career mentorship platform developed by Debanjan Mondal. It provides personalized career roadmaps, skill gap analysis, interview preparation, and PDF document analysis (like CVs and Assignments) using cutting-edge RAG technology.

IMPORTANT INSTRUCTIONS:
1. DOCUMENT EXTRACTION: If a document (PDF/CV) is uploaded, you MUST prioritize information found in the 'Document Context' for specific details like CGPA, grades, projects, and work history.
2. STRICTURE TRUTH: If the user asks for a detail (like CGPA) and it is present in the 'Document Context', PROVIDE IT IMMEDIATELY. Do not say you can't find it if it's there.
3. CONCISENESS & POLITENESS: Be extremely direct for technical questions. However, if the user says 'Thank you' or 'Thanks', respond with a warm, professional closing like 'You're very welcome! I'm glad I could help. Let me know if you have any other questions.'
4. CLOSING CHATS: If the user says 'Goodbye' or 'Bye', respond with a friendly 'Goodbye! Wishing you the best in your career journey.'

Student Profile (Current Facts):
{profile_text}

Additional Context (PDF/RAG/Memory):
{context if context else "No additional context found."}

RULES:
1. ALWAYS prioritize the 'Student Profile' for the user's current identity (University, Degree, Semester).
2. Use 'Document Context' for academic/professional history (CGPA, specific grades, projects).
3. NO REPETITIVE GREETINGS at the start of every message.
4. If the question is about who you are or what this platform is, refer to the 'ABOUT THIS PLATFORM' section above.
"""
        user_prompt = f"Question: {user_question}\nAnswer:"
        
        return system_prompt, user_prompt

    def is_llm_error(self, response):
        if not response:
            return True
        resp = str(response).lower()
        return any(kw in resp for kw in [
            "llm error", "resource_exhausted", "429",
            "quota", "rate limit"
        ])

    def _search_web(self, query):
        if not self.web_client:
            return None
        try:
            response = self.web_client.search(query=query, max_results=3, search_depth="advanced")
            return response.get("results", [])
        except Exception as e:
            print(f"Web search error: {e}")
            return None

    def answer_question(self, student_profile, user_question):
        """Non-streaming version for standard endpoints."""
        full_answer = ""
        is_image = False
        image_url = ""
        
        for token in self.stream_answer_question(student_profile, user_question):
            if "IMAGE_URL:" in token:
                parts = token.split("IMAGE_URL:")
                full_answer = parts[0].replace("🎨 Generating your image, please wait a moment...\n\n", "").strip()
                image_url = parts[1].strip()
                is_image = True
                break
            full_answer += token
            
        if is_image:
            return {
                "type": "image",
                "answer": full_answer or "Generated an image for you.",
                "url": image_url
            }
        
        return {
            "type": "text",
            "answer": full_answer.strip(),
            "sources": [] # Standard endpoints don't need detailed sources for now, but we keep the key for compatibility
        }

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

        # 0. Search Past Chat Memory
        memory_chunks = None
        if self.student_id:
            try:
                memory_chunks = search_chat_memory(self.student_id, user_question)
            except: pass

        # 1. PDF Search
        pdf_chunks = []
        if self.current_pdf:
            # A. Semantic Search
            pdf_chunks = search_pdf_vector_db(self.student_id, user_question, top_k=5, threshold=0.1)
            
            try:
                from document_ai.pdf_reader import extract_text_from_pdf
                pdf_text = extract_text_from_pdf(self.current_pdf)
                
                query_lower = user_question.lower()
                
                # B. General Document Question Detection (e.g., "What is this PDF about?")
                doc_keywords = ["about this pdf", "summarize", "what is this", "tell me about this", "extract", "contain", "pdf about"]
                is_general_doc_q = any(kw in query_lower for kw in doc_keywords)
                
                if is_general_doc_q or not pdf_chunks:
                    # Add a summary chunk (first 2000 chars) for general overview
                    summary_context = pdf_text[:2500]
                    pdf_chunks.append({"text": f"[DOCUMENT OVERVIEW]:\n{summary_context}", "score": 1.5})
                
                # C. Enhanced keyword search with synonyms
                search_keywords = [w.strip("?,.!") for w in query_lower.split() if len(w) > 2]
                
                synonyms = {
                    "cgpa": ["gpa", "marks", "percentage", "result", "grade", "pointer", "academic"],
                    "university": ["college", "institute", "school", "education", "lpu"],
                    "project": ["work", "experience", "developed", "built", "assignment"],
                    "skills": ["proficient", "knowledge", "expertise", "technical", "languages"]
                }
                
                expanded_keywords = set(search_keywords)
                for k, syns in synonyms.items():
                    if k in query_lower:
                        expanded_keywords.update(syns)
                
                relevant_lines = []
                lines = pdf_text.split('\n')
                for i, line in enumerate(lines):
                    line_lower = line.lower()
                    if any(kw in line_lower for kw in expanded_keywords):
                        start = max(0, i - 1)
                        end = min(len(lines), i + 2)
                        relevant_lines.append("\n".join(lines[start:end]))
                
                if relevant_lines:
                    unique_context = "\n---\n".join(list(set(relevant_lines))[:15])
                    pdf_chunks = (pdf_chunks or []) + [{"text": unique_context, "score": 1.2}]
            except Exception as e:
                print(f"PDF local search error: {e}")

        # 2. RAG Search
        rag_chunks = retrieve_relevant_chunks(user_question, top_k=3)

        # 3. Web Search
        web_results = []
        q_lower = user_question.lower()
        
        personal_terms = ["my name", "my university", "my cgpa", "my gpa", "my project", "my email", "i study", "about me", "who am i"]
        conversational_terms = ["hello", "hi", "hey", "how are you"]
        
        is_personal = any(term in q_lower for term in personal_terms)
        is_conversational = any(q_lower == term or q_lower.startswith(term + " ") for term in conversational_terms)
        
        if self.web_client and not is_personal and not is_conversational:
            if len(q_lower.split()) > 2: 
                web_results = self._search_web(user_question)

        # 4. Unified Prompting & Streaming
        system_prompt, user_prompt = self._build_multi_source_prompt(user_question, student_profile, pdf_chunks, rag_chunks, web_results, memory_chunks)
        
        full_response = ""
        for token in self.llm.stream_response(user_prompt, system_prompt=system_prompt):
            full_response += token
            yield token

        # 5. Background Storage (Parallel)
        if self.student_id and full_response.strip():
            import threading
            threading.Thread(
                target=store_chat_memory, 
                args=(self.student_id, user_question, full_response),
                daemon=True
            ).start()

    def format_student_profile(self, profile):
        if profile.get("student_type") == "school":
            return f"""
Name: {profile.get("full_name", "Student")}
Student Type: School Student
Class/Grade: {profile.get("grade_class", "")}
Board: {profile.get("board", "")}
Stream/Interest: {profile.get("stream_interest", "")}
Career Goal: {profile.get("career_goal", "")}
Favorite Subjects: {profile.get("favorite_subjects", "")}
Weak Subjects: {profile.get("weak_subjects", "")}
Skills Interested In: {profile.get("skills_interested", "")}
Current Skill Level: {profile.get("current_skill_level", "")}
Learning Style: {profile.get("learning_style", "")}
Future Target (Exam/Goal): {profile.get("future_target", "")}
Notes: {profile.get("notes", "")}
"""
        else:
            return f"""
Name: {profile.get("full_name", "Student")}
Student Type: College Student
Degree: {profile.get("degree", "")}
Semester: {profile.get("semester", "")}
Specialization: {profile.get("specialization", "")}
Career Goal: {profile.get("career_goal", "")}
Current Skills: {profile.get("skills", "")}
Weak Areas: {profile.get("weak_areas", "")}
Study Hours: {profile.get("daily_study_hours", "")}
"""