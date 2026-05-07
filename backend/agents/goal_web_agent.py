import os
from dotenv import load_dotenv
from tavily import TavilyClient

from llm.llm_client import LLMClient
from rag.retriever import retrieve_relevant_chunks


class GoalAwareWebAgent:
    def __init__(self):
        load_dotenv()

        api_key = os.getenv("TAVILY_API_KEY")

        if not api_key:
            raise ValueError("TAVILY_API_KEY not found. Please check your .env file.")

        self.web_client = TavilyClient(api_key=api_key)
        self.llm = LLMClient()

    def build_goal_search_query(self, student_profile, user_question):
        career_goal = student_profile.get("career_goal", "").strip()
        skills = student_profile.get("skills", "").strip()
        weak_areas = student_profile.get("weak_areas", "").strip()

        query = (
            f"latest {career_goal} skills internships India entry level "
            f"required skills projects interview preparation "
            f"current skills {skills} weak areas {weak_areas} "
            f"user question {user_question}"
        )

        query = " ".join(query.split())

        # Tavily query limit is 400 characters, so keep it safely below that.
        return query[:390]

    def search_web(self, query, max_results=5):
        try:
            response = self.web_client.search(
                query=query,
                search_depth="advanced",
                max_results=max_results,
                include_answer=False,
                include_raw_content=False
            )

            results = response.get("results", [])

            cleaned_results = []

            for item in results:
                cleaned_results.append({
                    "title": item.get("title", ""),
                    "url": item.get("url", ""),
                    "content": item.get("content", "")
                })

            return cleaned_results

        except Exception as e:
            return [{
                "title": "Web search error",
                "url": "",
                "content": f"Web search failed: {str(e)}"
            }]

    def format_web_context(self, web_results):
        context = ""

        for i, result in enumerate(web_results, start=1):
            context += f"""
Web Source {i}
Title: {result["title"]}
URL: {result["url"]}
Content:
{result["content"]}
"""
        return context.strip()

    def format_rag_context(self, rag_chunks):
        context = ""

        for i, chunk in enumerate(rag_chunks, start=1):
            context += f"""
Local RAG Source {i}
Source: {chunk["source"]}
Topic: {chunk.get("topic", "")}
Similarity Score: {chunk["score"]:.4f}
Text:
{chunk["text"]}
"""
        return context.strip()

    def format_student_profile(self, profile):
        return f"""
Student Profile:
Degree: {profile.get("degree", "")}
Semester: {profile.get("semester", "")}
Specialization: {profile.get("specialization", "")}
Dream/Career Goal: {profile.get("career_goal", "")}
Current Skills: {profile.get("skills", "")}
Weak Areas: {profile.get("weak_areas", "")}
Daily Study Hours: {profile.get("daily_study_hours", "")}
""".strip()

    def answer_with_web_and_rag(self, student_profile, user_question):
        web_query = self.build_goal_search_query(student_profile, user_question)

        web_results = self.search_web(web_query, max_results=3)
        rag_chunks = retrieve_relevant_chunks(web_query, top_k=3)

        web_context = self.format_web_context(web_results)
        rag_context = self.format_rag_context(rag_chunks)
        profile_text = self.format_student_profile(student_profile)

        prompt = f"""
You are CareerMind AI, a goal-aware web-connected career mentor.

You must answer using:
1. Student profile
2. Latest web search results
3. Local RAG knowledge base

Student Profile:
{profile_text}

Student Question:
{user_question}

Goal-Aware Web Search Query:
{web_query}

Latest Web Search Results:
{web_context}

Local RAG Context:
{rag_context}

Instructions:
- Personalize the answer according to the student's dream/career goal.
- Use web results for latest/current information.
- Use local RAG context for structured career guidance.
- Clearly mention what the student already knows.
- Clearly mention what the student should learn next.
- If the question is about jobs/internships, mention that openings can change and sources should be verified.
- Do not guarantee job, salary, or selection.
- End with source URLs from web results.
- Keep the answer practical and student-friendly.

Now generate the final answer.
"""

        answer = self.llm.generate_response(prompt)

        return {
            "agent": "Goal-Aware Web Research Agent",
            "answer": answer,
            "web_query": web_query,
            "web_sources": web_results,
            "rag_sources": rag_chunks
        }