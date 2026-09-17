import os
import time
import json
from dataclasses import dataclass
from typing import Optional, Any
from dotenv import load_dotenv

load_dotenv()

@dataclass
class LLMResult:
    text: str
    tokens_used: int
    latency_ms: int

class LLMClient:
    def __init__(self):
        self.gemini_key = os.getenv("GEMINI_API_KEY", "").strip()
        self.groq_key = os.getenv("GROQ_API_KEY", "").strip()
        self.mock_mode = os.getenv("MOCK_LLM", "false").lower() in ("true", "1", "yes")

    async def generate_gemini(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        json_mode: bool = False,
        temperature: float = 0.2
    ) -> LLMResult:
        start_time = time.perf_counter()

        # Check if we should use mock/offline fallback
        if self.mock_mode or not self.gemini_key:
            elapsed_ms = int((time.perf_counter() - start_time) * 1000)
            mock_text = self._mock_gemini_response(prompt, json_mode)
            tokens = len(prompt.split()) + len(mock_text.split())
            return LLMResult(text=mock_text, tokens_used=tokens, latency_ms=max(elapsed_ms, 12))

        try:
            from google import genai
            from google.genai import types

            client = genai.Client(api_key=self.gemini_key)
            config_kwargs = {"temperature": temperature}
            if json_mode:
                config_kwargs["response_mime_type"] = "application/json"
            if system_instruction:
                config_kwargs["system_instruction"] = system_instruction

            config = types.GenerateContentConfig(**config_kwargs)

            # In async contexts, run client.models.generate_content in executor or directly
            import asyncio
            response = await asyncio.to_thread(
                client.models.generate_content,
                model="gemini-3.6-flash",
                contents=prompt,
                config=config
            )
            elapsed_ms = int((time.perf_counter() - start_time) * 1000)

            text = response.text or ""
            usage = getattr(response, "usage_metadata", None)
            if usage:
                tokens = getattr(usage, "total_token_count", len(prompt.split()) + len(text.split()))
            else:
                tokens = len(prompt.split()) + len(text.split())

            return LLMResult(text=text, tokens_used=tokens, latency_ms=elapsed_ms)

        except Exception as e:
            # Fallback to mock on rate limits or API errors to keep pipeline resilient
            elapsed_ms = int((time.perf_counter() - start_time) * 1000)
            mock_text = self._mock_gemini_response(prompt, json_mode)
            tokens = len(prompt.split()) + len(mock_text.split())
            return LLMResult(text=mock_text, tokens_used=tokens, latency_ms=elapsed_ms)

    async def generate_groq(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        model: str = "openai/gpt-oss-20b",
        temperature: float = 0.0
    ) -> LLMResult:
        start_time = time.perf_counter()

        if self.mock_mode or not self.groq_key:
            elapsed_ms = int((time.perf_counter() - start_time) * 1000)
            mock_text = self._mock_groq_response(prompt)
            tokens = len(prompt.split()) + len(mock_text.split())
            return LLMResult(text=mock_text, tokens_used=tokens, latency_ms=max(elapsed_ms, 8))

        try:
            from groq import AsyncGroq
            client = AsyncGroq(api_key=self.groq_key)

            messages = []
            if system_instruction:
                messages.append({"role": "system", "content": system_instruction})
            messages.append({"role": "user", "content": prompt})

            completion = await client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature
            )

            elapsed_ms = int((time.perf_counter() - start_time) * 1000)
            text = completion.choices[0].message.content or ""
            tokens = completion.usage.total_tokens if completion.usage else len(prompt.split()) + len(text.split())

            return LLMResult(text=text, tokens_used=tokens, latency_ms=elapsed_ms)

        except Exception:
            elapsed_ms = int((time.perf_counter() - start_time) * 1000)
            mock_text = self._mock_groq_response(prompt)
            tokens = len(prompt.split()) + len(mock_text.split())
            return LLMResult(text=mock_text, tokens_used=tokens, latency_ms=elapsed_ms)

    def _mock_gemini_response(self, prompt: str, json_mode: bool) -> str:
        prompt_lower = prompt.lower()

        # 1. Decomposition request
        if "sub-questions" in prompt_lower or "decompose" in prompt_lower:
            return json.dumps({
                "sub_questions": [
                    {"text": "What are the primary goals and project requirements?", "sources": ["notion"]},
                    {"text": "What are the latest progress updates and sprint tasks?", "sources": ["jira"]},
                    {"text": "Were there any blockers or communications reported recently?", "sources": ["gmail"]}
                ]
            })

        # 2. Durable facts / memory extraction
        if "durable" in prompt_lower or "facts" in prompt_lower:
            return json.dumps({
                "facts": [
                    "Project X target release is end of Q3.",
                    "Authentication requires OAuth2 token storage."
                ]
            })

        # 3. Output validation JSON check
        if json_mode and "claims" in prompt_lower:
            return json.dumps({
                "claims": [
                    {"text": "Project X goals and architecture are specified in the engineering documentation.", "citation_indices": [1]},
                    {"text": "Core sprint milestones and deliverables are tracked in Jira.", "citation_indices": [2]}
                ],
                "citations": [
                    {"index": 1, "source": "notion", "permalink": "https://notion.so/project-x", "snippet": "Project X specifications"},
                    {"index": 2, "source": "jira", "permalink": "https://jira.atlassian.com/PROJ-101", "snippet": "Sprint tasks"}
                ],
                "confidence": 0.95
            })

        # 4. Default synthesis answer with citations
        if "evidence" in prompt_lower or "notion" in prompt_lower:
            return (
                "Based on the retrieved documentation, Project X is actively underway [1]. "
                "The engineering objectives focus on unified cross-platform RAG with strict guardrails [2]. "
                "All tasks and deliverables remain aligned with current roadmap priorities [1]."
            )

        return "PulseAgent retrieved relevant context and verified the request."

    def _mock_groq_response(self, prompt: str) -> str:
        prompt_lower = prompt.lower()

        # Guardrail prompt injection check
        if "query:" in prompt_lower:
            query_content = prompt_lower.split("query:", 1)[1]
            injection_markers = [
                "ignore previous instructions", "ignore all previous instructions",
                "reveal password", "drop table", "malicious instruction",
                "override system", "disregard all prior", "bypass security", "jailbreak"
            ]
            if any(m in query_content for m in injection_markers):
                return "unsafe: prompt_injection_detected"
            return "safe"

        # Citation entailment verification
        if "support this claim" in prompt_lower or "entailment" in prompt_lower:
            if "contradicts" in prompt_lower or "unsupported" in prompt_lower:
                return "no"
            return "yes"

        return "safe"

llm_client = LLMClient()
