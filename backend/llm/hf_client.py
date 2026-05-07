import os
from dotenv import load_dotenv
from huggingface_hub import InferenceClient


class HFClient:
    """
    Hugging Face client for simple chat/small talk.
    Used for greetings, goodbye, name questions, and basic assistant conversation.
    """

    def __init__(self):
        load_dotenv()

        self.hf_token = os.getenv("HF_TOKEN")
        
        # HF_TOKEN is optional - app can work without it using fallback responses
        if self.hf_token:
            self.client = InferenceClient(
                provider="auto",
                api_key=self.hf_token
            )
        else:
            self.client = None
            print("[HF] ⚠️  HF_TOKEN not found. Will use fallback responses only.")

        # Always try multiple models for resilience
        # Primary: Custom model if specified, otherwise try premium models
        # Fallback chain ensures service continues even if some models fail
        custom_model = os.getenv("HF_MODEL", "").strip()
        
        self.model_names = []
        
        # Add custom model first if specified
        if custom_model:
            self.model_names.append(custom_model)
        
        # Add fallback models (including those already in list)
        fallback_models = [
            "mistralai/Mistral-7B-Instruct-v0.2",
            "tiiuae/falcon-7b-instruct",
            "meta-llama/Llama-2-7b-chat-hf",
            "gpt2",
        ]
        
        # Add fallbacks that aren't already in the list
        for model in fallback_models:
            if model not in self.model_names:
                self.model_names.append(model)

    def generate_simple_chat(self, student_name, student_profile, user_message):
        user_message_clean = user_message.strip()
        q = user_message_clean.lower().strip()

        system_prompt = f"""
You are CareerMind AI, a friendly and professional AI career mentor.

Student Name: {student_name}
Career Goal: {student_profile.get("career_goal", "")}
Degree: {student_profile.get("degree", "")}
Semester: {student_profile.get("semester", "")}
Specialization: {student_profile.get("specialization", "")}

Rules:
- Understand the student's message carefully.
- Reply naturally and shortly.
- Use the student's name only when it feels natural.
- If the student greets you, greet them warmly.
- If the student asks how you are, answer naturally and ask how you can help.
- If the student says goodbye, say goodbye politely and wish them well.
- If the student asks your name, say you are CareerMind AI.
- If the student asks what you can do, explain briefly.
- Do not give a career roadmap for simple chat.
- Keep the answer under 2 sentences.
"""

        last_error = None
        
        # Skip HF if no token available
        if not self.client:
            print("[HF] ⚠️  No HF client available. Using fallback responses.")
        else:
            for idx, model_name in enumerate(self.model_names):
                try:
                    print(f"[HF] Attempting model ({idx + 1}/{len(self.model_names)}): {model_name}")
                    response = self.client.chat.completions.create(
                        model=model_name,
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_message_clean}
                        ],
                        max_tokens=80,
                        temperature=0.6
                    )

                    answer = response.choices[0].message.content

                    if answer:
                        print(f"[HF] ✅ Success with model: {model_name}")
                        return answer.strip()

                except Exception as e:
                    last_error = str(e)
                    print(f"[HF] ❌ Model failed: {model_name}")
                    print(f"[HF] Error: {last_error[:200]}")  # First 200 chars
                    continue

        print(f"[HF] ⚠️  All HF models exhausted. Using fallback responses.")
        if last_error:
            print(f"[HF] Last error: {last_error[:200]}")

        # Clean fallback if Hugging Face fails
        if q in ["hello", "hello ai", "hi", "hi ai", "hey", "hey ai", "hii"]:
            return f"Hello {student_name}! How can I help you with your career today?"

        if q in ["how are you", "how are you?", "how r u", "how are u"]:
            return f"I am doing great, {student_name}! I am ready to help you with your career goals."

        if q in ["what is your name", "who are you"]:
            return "I am CareerMind AI, your personalized AI career mentor."

        if q in ["what can you do", "help", "how can you help me", "can you help me"]:
            return "I can help you with skill gaps, career roadmaps, projects, interview preparation, diagrams, and latest career guidance."

        if q in ["bye", "goodbye", "good bye", "see you", "see you later", "ok bye"]:
            return f"Goodbye {student_name}! Keep learning consistently. I will be here whenever you need career guidance."

        return f"I understand, {student_name}. How can I help you with your career today?"