from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Any, Literal, Mapping

AnalysisType = Literal[
    "popular_requests",
    "common_questions",
    "common_needs",
    "follow_up_themes",
    "general_trend_summary",
]

ANALYSIS_TYPES: tuple[AnalysisType, ...] = (
    "popular_requests",
    "common_questions",
    "common_needs",
    "follow_up_themes",
    "general_trend_summary",
)


@dataclass(frozen=True)
class DemoContact:
    name: str = ""
    email: str = ""
    role: str = ""

    @classmethod
    def from_mapping(cls, value: Mapping[str, object]) -> "DemoContact":
        return cls(
            name=str(value.get("name") or "").strip(),
            email=str(value.get("email") or "").strip(),
            role=str(value.get("role") or "").strip(),
        )

    def is_empty(self) -> bool:
        return not any((self.name.strip(), self.email.strip(), self.role.strip()))

    def to_dict(self) -> dict[str, object]:
        return {
            "name": self.name.strip(),
            "email": self.email.strip(),
            "role": self.role.strip(),
        }


@dataclass(frozen=True)
class DemoRecap:
    id: int | None = None
    organization_name: str = ""
    lead_name: str = ""
    demo_lead: str = ""
    with_text: str = ""
    contacts: tuple[DemoContact, ...] = ()
    call_datetime: str = ""
    location: str = ""
    user_count: str = ""
    first_heard_of_gat: str = ""
    competition: str = ""
    devices: str = ""
    budget: str = ""
    authority: str = ""
    timeline: str = ""
    organization_details: str = ""
    needs: str = ""
    demo_discussion: str = ""
    questions_answers: str = ""
    requests_during_demo: str = ""
    follow_up: str = ""
    created_at: str = ""
    updated_at: str = ""

    def with_id(self, recap_id: int) -> "DemoRecap":
        return replace(self, id=recap_id)


@dataclass(frozen=True)
class SearchFilters:
    lead: str = ""
    org: str = ""
    demo_lead: str = ""
    date_start: str = ""
    date_end: str = ""
    competition: str = ""
    text: str = ""


@dataclass(frozen=True)
class StoredAiPayload:
    recap_id: int
    payload: dict[str, Any]
    redaction_version: str
    generated_at: str
