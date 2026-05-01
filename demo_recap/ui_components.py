from __future__ import annotations

from datetime import datetime
from html import escape
from typing import Any

import streamlit as st

from demo_recap.ai_payload import DRAFT_DEMO_ID
from demo_recap.ui_style import material_symbol

AI_FIELD_LABELS: dict[str, str] = {
    "demo_id": "Demo ID",
    "call_month": "Call month",
    "user_count": "Number of users",
    "first_heard_of_gat": "How they heard about GAT",
    "competition": "Other tools mentioned",
    "timeline": "Timeline",
    "needs": "Needs or pain points",
    "demo_discussion": "What was shown or discussed",
    "questions_answers": "Questions and answers",
    "requests_during_demo": "Requests from the demo",
    "follow_up": "Follow-up",
}

SECTION_META: dict[str, tuple[str, str]] = {
    "Identifiers removed before AI": ("verified_user", "Customer-identifying values the sanitizer removes later."),
    "People on the call": ("groups", "Contacts are stored internally and removed from AI copy."),
    "Full recap notes": ("article", "Complete internal notes for search and handoff."),
    "Call basics": ("event", "When, where, and who."),
    "Fit and buying details": ("target", "Context about fit and buying process."),
    "Demo notes": ("chat", "What was discussed and what happens next."),
    "Filters": ("target", "Choose saved values to narrow the recap list."),
    "Results": ("article", "Review the matching recap list."),
    "Details": ("notes", "Full internal recap and AI-safe status."),
    "Analysis Goal": ("insights", "Choose the trend question for this run."),
    "Run Analysis": ("send", "Generate the summary from sanitized recap data."),
}

SAFE_RAIL_FIELDS: tuple[str, ...] = (
    "demo_id",
    "call_month",
    "user_count",
    "needs",
    "questions_answers",
    "requests_during_demo",
    "follow_up",
)

SAFE_FIELD_ICONS: dict[str, str] = {
    "demo_id": "fingerprint",
    "call_month": "calendar_month",
    "user_count": "groups",
    "needs": "target",
    "questions_answers": "help",
    "requests_during_demo": "redeem",
    "follow_up": "send",
}


def readable_value(value: Any) -> str:
    if value is None:
        return "Not provided"
    text = str(value).strip()
    return text if text else "Not provided"


def html_value(value: Any) -> str:
    text = readable_value(value)
    return "<br>".join(escape(part) for part in text.splitlines())


def format_call_month(value: Any) -> str:
    text = readable_value(value)
    if text == "Not provided":
        return text
    try:
        return datetime.strptime(text, "%Y-%m").strftime("%B %Y")
    except ValueError:
        return text


def display_payload_value(field: str, value: Any) -> str:
    if field == "demo_id" and value == DRAFT_DEMO_ID:
        return "Draft preview"
    if field == "call_month":
        return format_call_month(value)
    if field == "demo_id" and readable_value(value).isdigit():
        return f"#{value}"
    return readable_value(value)


def render_section_heading(title: str) -> None:
    icon, subtitle = SECTION_META.get(title, ("notes", ""))
    st.markdown(
        f"""
        <div class="section-heading">
            <span class="section-icon">{material_symbol(icon)}</span>
            <div>
                <div class="section-title">{escape(title)}</div>
                <div class="section-subtitle">{escape(subtitle)}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_info_banner(title: str, text: str, *, icon: str = "verified_user") -> None:
    st.markdown(
        f"""
        <div class="privacy-banner">
            <div class="privacy-emblem">{material_symbol(icon)}</div>
            <div>
                <div class="privacy-title">{escape(title)}</div>
                <div class="privacy-text">
                    {escape(text)}
                </div>
            </div>
            <div class="privacy-doc" aria-hidden="true">
                <div class="doc-lines"><span></span><span></span><span></span></div>
                <div class="doc-badge">{material_symbol("check")}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_privacy_banner() -> None:
    render_info_banner(
        "Your privacy is protected",
        "Customer details are stored in the full recap. Before anything is used for AI summaries or trend analysis, names and contact details are removed or generalized.",
    )


def render_safe_preview_card(field: str, payload: dict[str, Any]) -> None:
    label = AI_FIELD_LABELS[field]
    value = display_payload_value(field, payload.get(field))
    missing_class = " is-empty" if value == "Not provided" else ""
    st.markdown(
        f"""
        <div class="safe-preview-card{missing_class}">
            <div class="safe-preview-icon">{material_symbol(SAFE_FIELD_ICONS.get(field, "notes"))}</div>
            <div class="safe-preview-copy">
                <div class="safe-preview-label">{escape(label)}</div>
                <div class="safe-preview-value">{html_value(value)}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_safe_copy_rail(
    payload: dict[str, Any] | None,
    *,
    error: str | None = None,
    pill_text: str = "Draft preview. Nothing is sent to AI.",
) -> None:
    with st.container(border=True):
        st.markdown(
            f"""
            <div class="rail-heading">
                <span class="rail-icon">{material_symbol("verified_user")}</span>
                <div>
                    <div class="rail-title">Preview AI-safe copy</div>
                    <div class="rail-pill">{escape(pill_text)}</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if error:
            st.error(error)
            return
        if payload is None:
            st.info("Start the recap to preview the AI-safe copy.")
            return
        for field in SAFE_RAIL_FIELDS:
            if field in payload:
                render_safe_preview_card(field, payload)
