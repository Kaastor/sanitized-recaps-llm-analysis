from __future__ import annotations

import unittest

from demo_recap.ai_payload import REDACTION_VERSION
from demo_recap.llm import summarize_with_llm
from demo_recap.models import StoredAiPayload


class CapturingPromptClient:
    def __init__(self) -> None:
        self.prompt = ""

    def summarize_sanitized_prompt(self, prompt: str) -> str:
        self.prompt = prompt
        return "summary"


class LlmBoundaryTest(unittest.TestCase):
    def stored_payload(
        self,
        *,
        version: str = REDACTION_VERSION,
        generated_at: str = "2026-04-30 12:00:00",
        extra: dict[str, str] | None = None,
    ) -> StoredAiPayload:
        payload = {
            "demo_id": 7,
            "call_month": "2026-04",
            "user_count": "250",
            "first_heard_of_gat": "Referral",
            "competition": "Manual reports",
            "timeline": "Q2",
            "needs": "Needs delegated workflows for onboarding.",
            "demo_discussion": "",
            "questions_answers": "",
            "requests_during_demo": "",
            "follow_up": "",
        }
        if extra:
            payload.update(extra)
        return StoredAiPayload(
            recap_id=7,
            payload=payload,
            redaction_version=version,
            generated_at=generated_at,
        )

    def test_summarize_with_llm_builds_prompt_from_current_safe_payload(self) -> None:
        client = CapturingPromptClient()
        payload = self.stored_payload()

        result = summarize_with_llm([payload], "common_needs", prompt_client=client)

        self.assertEqual(result, "summary")
        self.assertIn("Needs delegated workflows for onboarding.", client.prompt)
        self.assertIn('"demo_id": 7', client.prompt)

    def test_summarize_with_llm_rejects_unapproved_safe_payload_fields(self) -> None:
        client = CapturingPromptClient()
        payload = self.stored_payload(
            extra={
                "organization_name": "Acme Private School",
                "lead_name": "Jane Customer",
                "with_text": "Jane Customer | jane@example.com",
            }
        )

        with self.assertRaisesRegex(ValueError, "unapproved fields"):
            summarize_with_llm([payload], "common_needs", prompt_client=client)

        self.assertNotIn("Acme Private School", client.prompt)
        self.assertNotIn("Jane Customer", client.prompt)
        self.assertNotIn("jane@example.com", client.prompt)
        self.assertNotIn("with_text", client.prompt)

    def test_summarize_with_llm_rejects_stale_payload_versions(self) -> None:
        client = CapturingPromptClient()
        payload = self.stored_payload(version="v1")

        with self.assertRaisesRegex(ValueError, "stale redaction"):
            summarize_with_llm([payload], "common_needs", prompt_client=client)

    def test_summarize_with_llm_rejects_preview_payloads(self) -> None:
        client = CapturingPromptClient()
        payload = self.stored_payload(generated_at="preview")

        with self.assertRaisesRegex(ValueError, "preview"):
            summarize_with_llm([payload], "common_needs", prompt_client=client)


if __name__ == "__main__":
    unittest.main()
