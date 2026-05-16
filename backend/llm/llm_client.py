import os
from dotenv import load_dotenv
# pyrefly: ignore [missing-import]
from groq import Groq

load_dotenv()

class LLMClient:
    def __init__(self):
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY not found in .env")
        self.model = os.getenv("GROQ_MODEL", "llama3-8b-8192")
        self.client = Groq(api_key=api_key)

    def generate_response(self, prompt: str, system_prompt: str = None, max_tokens: int = 1024, temperature: float = 0.1, top_p: float = 1.0) -> str:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
                top_p=top_p,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            return f"LLM error: {str(e)}"

    def stream_response(self, prompt: str, system_prompt: str = None, max_tokens: int = 1024, temperature: float = 0.1, top_p: float = 1.0):
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        try:
            stream = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
                top_p=top_p,
                stream=True,
            )
            for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        except Exception as e:
            yield f"LLM error: {str(e)}"