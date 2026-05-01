from __future__ import annotations

from datetime import datetime
from typing import Any, Mapping

from .models import DemoRecap, StoredAiPayload
from .sanitization import (
    build_redaction_rules,
    find_basic_identifier_patterns,
    find_unredacted_known_values,
    sanitize_text,
)

REDACTION_VERSION = "v2"
DRAFT_DEMO_ID = "draft"

AI_PAYLOAD_ALLOWED_FIELDS: tuple[str, ...] = (
    "demo_id",
    "call_month",
    "user_count",
    "first_heard_of_gat",
    "competition",
    "timeline",
    "needs",
    "demo_discussion",
    "questions_answers",
    "requests_during_demo",
    "follow_up",
)
AI_PAYLOAD_ALLOWED_FIELD_SET: frozenset[str] = frozenset(AI_PAYLOAD_ALLOWED_FIELDS)

_DATE_FORMATS: tuple[str, ...] = (
    "%Y-%m-%d %H:%M",
    "%Y-%m-%d %H:%M:%S",
    "%Y-%m-%dT%H:%M",
    "%Y-%m-%dT%H:%M:%S",
    "%Y-%m-%d",
    "%m/%d/%Y %H:%M",
    "%m/%d/%Y",
    "%d/%m/%Y %H:%M",
    "%d/%m/%Y",
)


def derive_call_month(call_datetime: str) -> str | None:
    raw = (call_datetime or "").strip()
    if not raw:
        return None
    normalized = raw.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(normalized)
        return parsed.strftime("%Y-%m")
    except ValueError:
        pass

    for fmt in _DATE_FORMATS:
        try:
            parsed = datetime.strptime(raw, fmt)
            return parsed.strftime("%Y-%m")
        except ValueError:
            continue
    return None


def build_ai_safe_payload(recap: DemoRecap) -> dict[str, Any]:
    if recap.id is None:
        raise ValueError("Cannot build an AI payload before the recap has a database ID.")

    return _build_ai_safe_payload(recap, recap.id)


def build_draft_ai_safe_payload(recap: DemoRecap) -> dict[str, Any]:
    return _build_ai_safe_payload(recap, DRAFT_DEMO_ID)


def _build_ai_safe_payload(recap: DemoRecap, demo_id: int | str) -> dict[str, Any]:
    rules = build_redaction_rules(
        organization_name=recap.organization_name,
        lead_name=recap.lead_name,
        location=recap.location,
        with_text=recap.with_text,
        contacts=recap.contacts,
    )

    payload: dict[str, Any] = {
        "demo_id": demo_id,
        "call_month": derive_call_month(recap.call_datetime),
    }
    for field_name in AI_PAYLOAD_ALLOWED_FIELDS:
        if field_name in payload:
            continue
        raw_value = getattr(recap, field_name)
        payload[field_name] = sanitize_text(raw_value, rules)

    _validate_payload(payload, rules)
    return payload


def _validate_payload(payload: dict[str, Any], rules: object) -> None:
    text = "\n".join(str(value) for value in payload.values() if value is not None)
    issues = find_basic_identifier_patterns(text)
    # The rule list already contains exact metadata values and deterministic
    # contact candidates. If any still appear after sanitization, fail closed.
    issues.extend(find_unredacted_known_values(text, rules))
    if issues:
        unique_issues = sorted(set(issues), key=str.casefold)
        raise ValueError("AI payload still contains unredacted identifiers: " + ", ".join(unique_issues))


def validate_ai_safe_payload(payload: Mapping[str, Any]) -> None:
    fields = set(payload)
    unexpected = sorted(fields - AI_PAYLOAD_ALLOWED_FIELD_SET)
    if unexpected:
        raise ValueError("AI payload contains unapproved fields: " + ", ".join(unexpected))

    missing = [field for field in AI_PAYLOAD_ALLOWED_FIELDS if field not in payload]
    if missing:
        raise ValueError("AI payload is missing required fields: " + ", ".join(missing))

    text = "\n".join(str(value) for value in payload.values() if value is not None)
    issues = find_basic_identifier_patterns(text)
    if issues:
        unique_issues = sorted(set(issues), key=str.casefold)
        raise ValueError("AI payload contains identifier patterns: " + ", ".join(unique_issues))


def validate_stored_ai_payload(stored: StoredAiPayload) -> None:
    if not stored.generated_at or stored.generated_at == "preview":
        raise ValueError(f"AI payload for recap #{stored.recap_id} is a preview, not a stored safe payload.")
    if stored.redaction_version != REDACTION_VERSION:
        raise ValueError(
            f"AI payload for recap #{stored.recap_id} uses stale redaction "
            f"{stored.redaction_version or 'unknown'}; expected {REDACTION_VERSION}."
        )
    if stored.payload.get("demo_id") != stored.recap_id:
        raise ValueError(f"AI payload for recap #{stored.recap_id} has a mismatched demo_id.")
    validate_ai_safe_payload(stored.payload)
