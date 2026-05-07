from llm.llm_client import LLMClient
from rag.retriever import retrieve_relevant_chunks


class BaseCareerAgent:
    def __init__(self):
        self.llm = LLMClient()

    def format_student_profile(self, profile):
        return f"""
Student Profile:
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

    def generate(self, prompt):
        return self.llm.generate_response(prompt)


class SkillGapAgent(BaseCareerAgent):
    def analyze(self, student_profile):
        query = f"""
        Required skills for {student_profile.get("career_goal", "")}.
        Current skills: {student_profile.get("skills", "")}.
        Find missing skills and priority skills.
        """

        rag_chunks = retrieve_relevant_chunks(query, top_k=3)

        prompt = f"""
You are a Skill Gap Agent for CareerMind AI.

Your task:
Analyze the student's current skills and compare them with the required skills for the student's career goal.

Give:
1. Current strong skills
2. Missing skills
3. High-priority skills
4. Medium-priority skills
5. Weak areas improvement plan
6. Final recommendation

Use the student profile and RAG context.

{self.format_student_profile(student_profile)}

RAG Context:
{self.format_rag_context(rag_chunks)}

Now generate a clear skill gap analysis.
"""

        answer = self.generate(prompt)

        return {
            "agent": "Skill Gap Agent",
            "answer": answer,
            "sources": rag_chunks
        }


class CareerRoadmapAgent(BaseCareerAgent):
    def generate_roadmap(self, student_profile):
        query = f"""
        Career roadmap for {student_profile.get("career_goal", "")}
        based on skills {student_profile.get("skills", "")}
        and weak areas {student_profile.get("weak_areas", "")}
        """

        rag_chunks = retrieve_relevant_chunks(query, top_k=3)

        prompt = f"""
You are a Career Roadmap Agent for CareerMind AI.

Your task:
Generate a personalized roadmap for the student.

The roadmap must include:
1. Current level analysis
2. Month-wise roadmap
3. Weekly study direction
4. Skills to learn first
5. Project milestones
6. Interview preparation stage
7. Deployment/MLOps stage if relevant

Use the student's daily study hours to make the roadmap realistic.

{self.format_student_profile(student_profile)}

RAG Context:
{self.format_rag_context(rag_chunks)}

Now generate the personalized career roadmap.
"""

        answer = self.generate(prompt)

        return {
            "agent": "Career Roadmap Agent",
            "answer": answer,
            "sources": rag_chunks
        }


class ProjectRecommendationAgent(BaseCareerAgent):
    def recommend_projects(self, student_profile):
        query = f"""
        Project ideas for {student_profile.get("career_goal", "")}
        based on current skills {student_profile.get("skills", "")}
        """

        rag_chunks = retrieve_relevant_chunks(query, top_k=3)

        prompt = f"""
You are a Project Recommendation Agent for CareerMind AI.

Your task:
Recommend practical projects for the student based on career goal, current skills, and weak areas.

For each project, include:
1. Project title
2. Difficulty level
3. Problem statement
4. Skills used
5. Dataset idea
6. Deployment idea
7. Why this project helps the student's career

Suggest beginner, intermediate, and advanced projects.

{self.format_student_profile(student_profile)}

RAG Context:
{self.format_rag_context(rag_chunks)}

Now generate project recommendations.
"""

        answer = self.generate(prompt)

        return {
            "agent": "Project Recommendation Agent",
            "answer": answer,
            "sources": rag_chunks
        }


class InterviewPreparationAgent(BaseCareerAgent):
    def prepare_interview(self, student_profile):
        query = f"""
        Interview preparation questions for {student_profile.get("career_goal", "")}
        skills {student_profile.get("skills", "")}
        """

        rag_chunks = retrieve_relevant_chunks(query, top_k=3)

        prompt = f"""
You are an Interview Preparation Agent for CareerMind AI.

Your task:
Create a personalized interview preparation plan.

Include:
1. HR questions
2. Technical questions
3. SQL/programming questions if relevant
4. Machine learning/data science questions if relevant
5. Project-based interview questions
6. Weak area practice questions
7. Daily interview practice plan

{self.format_student_profile(student_profile)}

RAG Context:
{self.format_rag_context(rag_chunks)}

Now generate the interview preparation plan.
"""

        answer = self.generate(prompt)

        return {
            "agent": "Interview Preparation Agent",
            "answer": answer,
            "sources": rag_chunks
        }