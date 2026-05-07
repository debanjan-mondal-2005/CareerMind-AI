import os
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

class LLMClient:
    def __init__(self):
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY not found in .env")
        self.model = os.getenv("GROQ_MODEL", "llama3-8b-8192")
        self.client = Groq(api_key=api_key)

    def generate_response(self, prompt: str, max_tokens: int = 1024, temperature: float = 0.3) -> str:
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                temperature=temperature,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            return f"LLM error: {str(e)}"

    def stream_response(self, prompt: str, max_tokens: int = 1024, temperature: float = 0.3):
        try:
            stream = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                temperature=temperature,
                stream=True,
            )
            for chunk in stream:
                delta = chunk.choices[0].delta.content
                if delta:
                    yield delta
        except Exception as e:
            yield f"LLM error: {str(e)}"