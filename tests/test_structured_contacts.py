from __future__ import annotations

import tempfile
import unittest
from contextlib import closing
from pathlib import Path

from demo_recap.ai_payload import DRAFT_DEMO_ID, build_ai_safe_payload, build_draft_ai_safe_payload
from demo_recap.config import AppConfig
from demo_recap.db import (
    connect,
    get_ai_payload,
    get_recap,
    init_db,
    preview_ai_payloads,
    refresh_ai_payload,
    save_recap,
)
from demo_recap.models import DemoContact, DemoRecap


def recap_with_structured_contact(recap_id: int | None = 1) -> DemoRecap:
    return DemoRecap(
        id=recap_id,
        organization_name="Acme School",
        lead_name="Pat Lead",
        demo_lead="Ava Chen",
        with_text="Joseph Grimes | GAT Labs | Internal demo support",
        contacts=(DemoContact(name="Marta Vale", email="marta.vale@acme.example", role="IT Lead"),),
        call_datetime="2026-04-30 10:00",
        location="Boston, MA",
        needs="Marta Vale needs delegated onboarding workflows for Acme School in Boston, MA.",
        demo_discussion="Marta Vale asked Joseph Grimes from GAT Labs about audit history.",
        questions_answers="Can alerts email marta.vale@acme.example?",
    )


class StructuredContactTest(unittest.TestCase):
    def test_structured_contacts_and_raw_with_names_are_redacted(self) -> None:
        payload = build_ai_safe_payload(recap_with_structured_contact())

        combined = "\n".join(str(value) for value in payload.values())
        self.assertIn("[CONTACT]", combined)
        self.assertIn("[EMAIL]", combined)
        self.assertNotIn("Marta Vale", combined)
        self.assertNotIn("Joseph Grimes", combined)
        self.assertNotIn("marta.vale@acme.example", combined)
        self.assertNotIn("Acme School", combined)
        self.assertNotIn("Boston, MA", combined)
        self.assertIn("GAT Labs", payload["demo_discussion"])

    def test_contacts_are_saved_with_recap_and_used_for_stored_ai_payload(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            config = AppConfig(db_path=Path(tmp_dir) / "recaps.sqlite", groq_api_key="", groq_model="test-model")
            init_db(config)
            with closing(connect(config.db_path)) as conn:
                saved = save_recap(conn, recap_with_structured_contact(recap_id=None))
                loaded = get_recap(conn, saved.id)
                stored = get_ai_payload(conn, saved.id or 0)

        self.assertIsNotNone(loaded)
        self.assertEqual(loaded.contacts[0].name, "Marta Vale")  # type: ignore[union-attr]
        self.assertIsNotNone(stored)
        self.assertIn("[CONTACT]", stored.payload["needs"])  # type: ignore[union-attr]
        self.assertNotIn("Marta Vale", stored.payload["needs"])  # type: ignore[union-attr]

    def test_draft_ai_payload_uses_same_redaction_without_database_id(self) -> None:
        payload = build_draft_ai_safe_payload(recap_with_structured_contact(recap_id=None))

        self.assertEqual(payload["demo_id"], DRAFT_DEMO_ID)
        self.assertIn("[CONTACT]", payload["needs"])
        self.assertNotIn("Marta Vale", payload["needs"])
        self.assertNotIn("Acme School", payload["needs"])

    def test_raw_with_role_fragments_do_not_become_contact_rules(self) -> None:
        recap = DemoRecap(
            id=1,
            organization_name="Pine Harbor District",
            lead_name="Marco Flynn",
            with_text="Iris Chen | iris.chen@pineharbor.example | Help Desk Lead",
            needs="Help desk staff need safer delegated workflows.",
            demo_discussion="Iris Chen asked about limited workflow permissions.",
        )

        payload = build_ai_safe_payload(recap)

        self.assertIn("Help desk staff", payload["needs"])
        self.assertNotIn("Iris Chen", "\n".join(str(value) for value in payload.values()))

    def test_refresh_ai_payload_regenerates_stored_safe_copy_without_editing_recap(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            config = AppConfig(db_path=Path(tmp_dir) / "recaps.sqlite", groq_api_key="", groq_model="test-model")
            init_db(config)
            with closing(connect(config.db_path)) as conn:
                saved = save_recap(conn, recap_with_structured_contact(recap_id=None))
                conn.execute(
                    "UPDATE demo_recap_ai_payloads SET payload_json = ? WHERE recap_id = ?",
                    ('{"demo_id": 1, "needs": "unsafe Marta Vale"}', saved.id),
                )
                conn.commit()

                refreshed = refresh_ai_payload(conn, saved)

        self.assertIn("[CONTACT]", refreshed.payload["needs"])
        self.assertNotIn("Marta Vale", refreshed.payload["needs"])

    def test_preview_ai_payloads_does_not_rewrite_stale_stored_copy(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            config = AppConfig(db_path=Path(tmp_dir) / "recaps.sqlite", groq_api_key="", groq_model="test-model")
            init_db(config)
            with closing(connect(config.db_path)) as conn:
                saved = save_recap(conn, recap_with_structured_contact(recap_id=None))
                conn.execute(
                    "UPDATE demo_recap_ai_payloads SET payload_json = ? WHERE recap_id = ?",
                    ('{"demo_id": 1, "needs": "unsafe Marta Vale"}', saved.id),
                )
                conn.commit()
                before = conn.execute(
                    "SELECT payload_json, generated_at FROM demo_recap_ai_payloads WHERE recap_id = ?",
                    (saved.id,),
                ).fetchone()

                payloads, stale_count, errors = preview_ai_payloads(conn, [saved])

                after = conn.execute(
                    "SELECT payload_json, generated_at FROM demo_recap_ai_payloads WHERE recap_id = ?",
                    (saved.id,),
                ).fetchone()

        self.assertEqual(errors, [])
        self.assertEqual(stale_count, 1)
        self.assertEqual(dict(before), dict(after))
        self.assertIn("[CONTACT]", payloads[0].payload["needs"])
        self.assertNotIn("Marta Vale", payloads[0].payload["needs"])


if __name__ == "__main__":
    unittest.main()
