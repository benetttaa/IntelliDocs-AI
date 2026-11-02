from __future__ import annotations

import os
from typing import Any

import httpx


class MockLLMAdapter:
    def generate(self, question: str, evidence: list[dict[str, Any]]) -> str:
        if not evidence:
            return "I could not find enough reliable evidence to answer this question confidently."

        summary = evidence[0]["text"]
        if len(summary) > 280:
            summary = summary[:277] + "..."

        return (
            f"Based on the retrieved documents, the most relevant evidence suggests: \"{summary}\". "
            "This answer is grounded in the uploaded material and may require additional review for strict compliance use cases."
        )


class OpenAIAdapter:
    def __init__(self, api_key: str, model: str = "gpt-4o-mini"):
        self.api_key = api_key
        self.model = model

    def generate(self, question: str, evidence: list[dict[str, Any]]) -> str:
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY is missing.")

        context = "\n\n".join(f"Source: {item['file_name']}\n{item['text']}" for item in evidence)
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": "Answer with grounded, concise, evidence-based responses. If the evidence does not support a claim, say you cannot determine it."},
                {"role": "user", "content": f"Question: {question}\n\nEvidence:\n{context}"},
            ],
            "temperature": 0.2,
        }

        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        response = httpx.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=30,
        )
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"].strip()


class LLMService:
    def __init__(self, api_key: str = "", model: str = "gpt-4o-mini"):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY", "")
        self.model = model
        self.provider = "openai" if self.api_key else "mock"

    def generate_answer(self, question: str, evidence: list[dict[str, Any]]) -> str:
        if self.provider == "openai":
            return OpenAIAdapter(self.api_key, self.model).generate(question, evidence)
        return MockLLMAdapter().generate(question, evidence)
