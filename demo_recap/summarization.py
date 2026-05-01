from __future__ import annotations

import json
from typing import Any

from .models import ANALYSIS_TYPES, AnalysisType, StoredAiPayload

ANALYSIS_LABELS: dict[AnalysisType, str] = {
    "popular_requests": "popular or repeated product requests",
    "common_questions": "common questions asked during demos",
    "common_needs": "common prospect needs and pain points",
    "follow_up_themes": "common follow-up themes and commitments",
    "general_trend_summary": "general trends across the sanitized demo recaps",
}

ANALYSIS_FIELD_MAP: dict[AnalysisType, tuple[str, ...]] = {
    "popular_requests": ("requests_during_demo", "needs"),
    "common_questions": ("questions_answers",),
    "common_needs": ("needs",),
    "follow_up_themes": ("follow_up",),
    "general_trend_summary": (
        "user_count",
        "first_heard_of_gat",
        "competition",
        "timeline",
        "needs",
        "demo_discussion",
        "questions_answers",
        "requests_during_demo",
        "follow_up",
    ),
}

CONTEXT_FIELDS: tuple[str, ...] = ("demo_id", "call_month")


def assert_valid_analysis_type(analysis_type: str) -> AnalysisType:
    if analysis_type not in ANALYSIS_TYPES:
        valid = ", ".join(ANALYSIS_TYPES)
        raise ValueError(f"Unsupported analysis type {analysis_type!r}. Valid values: {valid}")
    return analysis_type  # type: ignore[return-value]


def build_action_specific_records(
    stored_payloads: list[StoredAiPayload], analysis_type: AnalysisType
) -> list[dict[str, Any]]:
    fields = ANALYSIS_FIELD_MAP[analysis_type]
    records: list[dict[str, Any]] = []
    for stored in sorted(stored_payloads, key=lambda item: item.recap_id):
        payload = stored.payload
        record: dict[str, Any] = {field: payload.get(field) for field in CONTEXT_FIELDS}
        for field in fields:
            record[field] = payload.get(field, "")
        records.append(record)
    return records


def build_sanitized_batch_input(
    stored_payloads: list[StoredAiPayload], analysis_type: AnalysisType
) -> str:
    records = build_action_specific_records(stored_payloads, analysis_type)
    records_json = json.dumps(records, ensure_ascii=False, indent=2, sort_keys=True)
    label = ANALYSIS_LABELS[analysis_type]
    return f"""You are summarizing sanitized product demo recap records for internal product planning.

Analysis type: {analysis_type}
Analysis goal: Identify {label}.

Rules:
- Use only the sanitized records provided below.
- Do not guess, infer, reconstruct, or name customer organizations, leads, attendees, contact details, or exact locations.
- Treat placeholders such as [ORG], [LEAD], [CONTACT], [EMAIL], [URL], and [LOCATION] as intentional redactions.
- Do not cite or invent customer names. Cite supporting demo IDs only.
- Prefer concise, decision-useful themes. Merge duplicates. Note uncertainty when evidence is thin.

Output format:
1. A short executive summary.
2. Ranked themes with supporting demo IDs only.
3. Any notable outliers or one-off requests with supporting demo IDs only.

Sanitized records:
{records_json}
"""

