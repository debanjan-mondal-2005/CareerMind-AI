import re
from llm.llm_client import LLMClient
from rag.retriever import retrieve_relevant_chunks


class DiagramAgent:
    def __init__(self):
        self.llm = LLMClient()

    def clean_mermaid_code(self, response):
        response = response.strip()

        # Remove markdown mermaid block if Gemini adds it
        response = response.replace("```mermaid", "").replace("```", "").strip()

        return response

    def generate_diagram(self, user_request):
        rag_chunks = retrieve_relevant_chunks(user_request, top_k=3)

        rag_context = ""

        for i, chunk in enumerate(rag_chunks, start=1):
            rag_context += f"""
Context {i}
Source: {chunk["source"]}
Topic: {chunk.get("topic", "")}
Text:
{chunk["text"]}
"""

        prompt = f"""
You are a Diagram Code Agent for CareerMind AI.

Your task is to generate a clean Mermaid.js diagram code based on the user's request.

User Request:
{user_request}

Relevant RAG Context:
{rag_context}

Important rules:
- Return only Mermaid code.
- Do not add explanation.
- Do not use markdown triple backticks.
- Use flowchart TD unless another diagram type is clearly needed.
- Make the diagram clean, structured, and presentation-friendly.
- Use short node labels.
- Avoid special characters that can break Mermaid syntax.
- For HLD, show main system components.
- For LLD, show function-level flow.
- For roadmap, show learning stages.
- For pipeline, show step-by-step data/model flow.

Example format:
flowchart TD
    A[Start] --> B[Step 1]
    B --> C[Step 2]
    C --> D[End]

Now generate the Mermaid diagram code.
"""

        response = self.llm.generate_response(prompt)
        mermaid_code = self.clean_mermaid_code(response)

        return {
            "agent": "Diagram Agent",
            "diagram_code": mermaid_code,
            "sources": rag_chunks
        }