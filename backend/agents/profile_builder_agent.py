import json
from llm.llm_client import LLMClient


class ProfileBuilderAgent:
    def __init__(self):
        self.llm = LLMClient()

    def build_prompt(self, onboarding_answers):
        formatted_answers = ""

        for row in onboarding_answers:
            formatted_answers += f"Question: {row['question']}\n"
            formatted_answers += f"Answer: {row['answer']}\n\n"

        prompt = f"""
You are a Profile Builder Agent for an AI Career Mentor system.

Your task is to convert student onboarding answers into a clean structured JSON profile.

Extract the following fields:
1. degree
2. semester
3. specialization
4. career_goal
5. skills
6. weak_areas
7. daily_study_hours

Important rules:
- Return only valid JSON.
- Do not use markdown.
- Do not use ```json.
- Do not add explanation.
- skills should be a list.
- weak_areas should be a list.
- If any field is missing, keep it as an empty string or empty list.

Student onboarding answers:

{formatted_answers}

Return JSON in this exact format:

{{
  "degree": "",
  "semester": "",
  "specialization": "",
  "career_goal": "",
  "skills": [],
  "weak_areas": [],
  "daily_study_hours": ""
}}
"""
        return prompt

    def clean_json_response(self, response):
        response = response.strip()

        if response.startswith("```json"):
            response = response.replace("```json", "", 1).strip()

        if response.startswith("```"):
            response = response.replace("```", "", 1).strip()

        if response.endswith("```"):
            response = response[:-3].strip()

        return response

    def build_profile(self, onboarding_answers):
        prompt = self.build_prompt(onboarding_answers)
        response = self.llm.generate_response(prompt)

        cleaned_response = self.clean_json_response(response)

        try:
            profile = json.loads(cleaned_response)
            return {
                "success": True,
                "profile": profile
            }

        except json.JSONDecodeError:
            return {
                "success": False,
                "message": "LLM returned invalid JSON",
                "raw_response": response,
                "cleaned_response": cleaned_response
            }