from llm.llm_client import LLMClient
from document_ai.pdf_reader import extract_text_from_pdf   # using your existing PDF reader
import os


class PDFQAAgent:
    def __init__(self):
        self.llm = LLMClient()

    def chunk_text(self, text, chunk_size=1800, overlap=250):
        chunks = []
        start = 0

        while start < len(text):
            end = start + chunk_size
            chunk = text[start:end]

            if chunk.strip():
                chunks.append(chunk.strip())

            start = end - overlap

        return chunks

    def select_relevant_chunks(self, pdf_text, question, max_chunks=4):
        """
        Simple keyword-based retrieval for PDF.
        Later you can upgrade this to embedding-based PDF vector DB.
        """

        chunks = self.chunk_text(pdf_text)

        question_words = set(question.lower().split())

        scored_chunks = []

        for chunk in chunks:
            chunk_lower = chunk.lower()
            score = sum(1 for word in question_words if word in chunk_lower)

            scored_chunks.append({
                "text": chunk,
                "score": score
            })

        scored_chunks = sorted(scored_chunks, key=lambda x: x["score"], reverse=True)

        selected = scored_chunks[:max_chunks]

        return [item["text"] for item in selected]

    def answer_pdf_question(self, pdf_text, question):
        """
        Core logic for answering a question using extracted PDF text.
        (Kept for backward compatibility or internal use.)
        """
        if not pdf_text:
            return {
                "success": False,
                "answer": "No readable text was found in this PDF. If it is a scanned PDF, OCR is required."
            }

        relevant_chunks = self.select_relevant_chunks(pdf_text, question)

        context = "\n\n".join(relevant_chunks)

        prompt = f"""
You are CareerMind AI PDF Assistant.

Answer the user's question using only the uploaded PDF content.

Instructions:
- Use the PDF content as the source of truth.
- If the answer is not present in the PDF, clearly say that it is not found in the uploaded PDF.
- Do not invent information.
- Keep the answer clear and structured.
- If useful, mention the relevant page text section.

User Question:
{question}

Relevant PDF Content:
{context}

Now answer the question.
"""

        answer = self.llm.generate_response(prompt)

        if (
            "LLM error" in answer
            or "RESOURCE_EXHAUSTED" in answer
            or "429" in answer
            or "quota" in answer.lower()
        ):
            fallback_answer = (
                "CareerMind AI could not use the main LLM right now, "
                "but here is the most relevant text found from your PDF:\n\n"
                + context[:2500]
            )

            return {
                "success": True,
                "answer": fallback_answer,
                "fallback": True
            }

        return {
            "success": True,
            "answer": answer,
            "fallback": False
        }

    # ---- New method: answer(pdf_path, question) called by CareerMentorAgent ----
    def answer(self, pdf_path, question):
        """
        Main entry point: receives the PDF file path, extracts text,
        and answers the question.
        """
        if not os.path.exists(pdf_path):
            return f"PDF file not found at: {pdf_path}"

        try:
            # Use your existing pdf_reader function to extract text
            pdf_text = extract_text_from_pdf(pdf_path)
        except Exception as e:
            return f"Failed to extract text from PDF: {str(e)}"

        result = self.answer_pdf_question(pdf_text, question)
        return result.get("answer", "Sorry, I could not process your PDF question.")