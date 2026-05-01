from __future__ import annotations

from typing import Protocol

from .ai_payload import validate_stored_ai_payload
from .config import AppConfig, load_config
from .models import AnalysisType, StoredAiPayload
from .summarization import build_sanitized_batch_input


class _SanitizedPromptClient(Protocol):
    def summarize_sanitized_prompt(self, prompt: str) -> str: ...


class _GroqPromptClient:
    def __init__(self, config: AppConfig | None = None) -> None:
        self.config = config or load_config()
        if not self.config.has_groq_api_key:
            raise ValueError("GROQ_API_KEY is not configured.")

    def summarize_sanitized_prompt(self, prompt: str) -> str:
        from groq import Groq

        client = Groq(api_key=self.config.groq_api_key)
        response = client.chat.completions.create(
            model=self.config.groq_model,
            messages=[
                {
                    "role": "system",
                    "content": "You summarize sanitized product-demo analytics records. Never infer customer identities.",
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,
        )
        return response.choices[0].message.content or ""


def summarize_with_llm(
    stored_payloads: list[StoredAiPayload],
    analysis_type: AnalysisType,
    *,
    config: AppConfig | None = None,
    prompt_client: _SanitizedPromptClient | None = None,
) -> str:
    """Summarize trends through the only public LLM boundary.

    Callers provide stored AI-safe payloads, not a free-form prompt string. The
    raw prompt remains an internal transport detail between this boundary and
    the provider adapter.
    """
    for stored in stored_payloads:
        validate_stored_ai_payload(stored)

    prompt = build_sanitized_batch_input(stored_payloads, analysis_type)
    client = prompt_client or _GroqPromptClient(config or load_config())
    return client.summarize_sanitized_prompt(prompt)
