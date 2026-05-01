from __future__ import annotations

from datetime import date, datetime, time
from html import escape
from typing import Any, Sequence

import streamlit as st

from demo_recap.ai_payload import build_draft_ai_safe_payload
from demo_recap.db import (
    build_current_ai_payload,
    get_recap,
    list_competitions,
    list_demo_leads,
    list_lead_names,
    list_organization_names,
    preview_ai_payloads,
    refresh_ai_payloads,
    save_recap,
    search_recaps,
)
from demo_recap.llm import summarize_with_llm
from demo_recap.models import ANALYSIS_TYPES, AnalysisType, DemoContact, DemoRecap, SearchFilters
from demo_recap.ui_components import (
    render_info_banner,
    render_privacy_banner,
    render_safe_copy_rail,
    render_section_heading,
)
from demo_recap.ui_style import material_symbol

RAW_FIELD_LABELS: tuple[tuple[str, str, str], ...] = (
    ("organization_details", "About the organization", "area"),
    ("call_datetime", "Call date and time", "line"),
    ("with_text", "Raw WITH notes", "area"),
    ("user_count", "Number of users", "line"),
    ("first_heard_of_gat", "How they heard about GAT", "area"),
    ("competition", "Other tools they mentioned", "line"),
    ("devices", "Devices or platforms", "line"),
    ("budget", "Budget notes", "area"),
    ("authority", "Who can approve", "area"),
    ("timeline", "Timeline", "line"),
    ("needs", "Needs or pain points", "area"),
    ("demo_discussion", "What was shown or discussed", "area"),
    ("questions_answers", "Questions and answers", "area"),
    ("requests_during_demo", "Requests from the demo", "area"),
    ("follow_up", "Follow-up", "area"),
)
RAW_FIELD_META = {field: (label, widget_type) for field, label, widget_type in RAW_FIELD_LABELS}
RAW_FIELD_HELP: dict[str, str] = {
    "organization_details": "Saved for team context. Customer names here are removed from the AI copy when they match the organization field.",
    "call_datetime": "Used for search and monthly trend summaries.",
    "with_text": "Optional original attendee text. Structured contacts above are the sanitizer's primary source.",
    "first_heard_of_gat": "Useful for trends, but avoid adding personal contact details unless needed for the team notes.",
    "needs": "This is one of the main fields used for trend summaries.",
    "demo_discussion": "Summarize what came up during the demo. Customer names are removed from the AI copy.",
    "questions_answers": "Add common questions and your answers. The AI summary uses this for question trends.",
    "requests_during_demo": "Add product requests or asks. The AI summary uses this for request trends.",
    "follow_up": "Add next steps or promises made. The AI summary uses this for follow-up trends.",
}
RAW_FIELD_GROUPS: tuple[tuple[str, bool, tuple[str, ...]], ...] = (
    (
        "Call basics",
        True,
        ("call_datetime", "organization_details", "with_text"),
    ),
    (
        "Fit and buying details",
        False,
        ("user_count", "first_heard_of_gat", "competition", "devices", "budget", "authority", "timeline"),
    ),
    (
        "Demo notes",
        False,
        ("needs", "demo_discussion", "questions_answers", "requests_during_demo", "follow_up"),
    ),
)

ANALYSIS_OPTION_LABELS: dict[AnalysisType, str] = {
    "popular_requests": "Popular product requests",
    "common_questions": "Common questions",
    "common_needs": "Common needs",
    "follow_up_themes": "Follow-up themes",
    "general_trend_summary": "Overall trend summary",
}
ANALYSIS_OPTION_CAPTIONS: dict[AnalysisType, str] = {
    "popular_requests": "Find repeated feature requests and product asks.",
    "common_questions": "Group recurring prospect questions and objections.",
    "common_needs": "Surface repeated pain points and operational needs.",
    "follow_up_themes": "Summarize commitments, next steps, and open asks.",
    "general_trend_summary": "Give a broad readout across needs, questions, requests, and follow-up.",
}

REQUIRED_FIELDS: tuple[tuple[str, str], ...] = (
    ("organization_name", "Organization name"),
    ("lead_name", "Lead name"),
    ("demo_lead", "Demo lead"),
    ("location", "Location"),
)

NAV_ITEMS: tuple[tuple[str, str], ...] = (
    ("add", "Add Recap"),
    ("search", "Find Recaps"),
    ("summary", "Summarize Trends"),
)
SEARCH_SELECTED_RECAP_KEY = "search_selected_recap_id"
SEARCH_EDITING_RECAP_KEY = "search_editing_recap_id"
SEARCH_FORM_VERSION_KEY = "search_detail_form_version"
SEARCH_SAVE_MESSAGE_KEY = "search_save_message"


def validate_recap_for_save(recap: DemoRecap) -> list[str]:
    missing = [label for field, label in REQUIRED_FIELDS if not getattr(recap, field).strip()]
    if not recap.contacts:
        missing.append("At least one person on the call")
    for index, contact in enumerate(recap.contacts, start=1):
        if not contact.name.strip():
            missing.append(f"Contact {index} name")
    return missing


def analysis_option_label(analysis_type: AnalysisType) -> str:
    return ANALYSIS_OPTION_LABELS[analysis_type]


def demo_lead_select_options(current: str, demo_leads: Sequence[str]) -> list[str]:
    options: list[str] = []
    seen: set[str] = set()
    for value in demo_leads:
        cleaned = value.strip()
        if cleaned and cleaned not in seen:
            options.append(cleaned)
            seen.add(cleaned)

    current = current.strip()
    if current and current not in seen:
        options.append(current)
    return options


def contact_state_key(prefix: str, index: int, field: str) -> str:
    return f"{prefix}_contact_{index}_{field}"


def render_contact_editor(prefix: str, initial: DemoRecap, *, disabled: bool = False) -> tuple[DemoContact, ...]:
    render_section_heading("People on the call")
    if disabled:
        st.caption("People are stored internally and removed from any AI-safe copy.")
    else:
        st.caption("Enter people here so names and emails can be removed from any AI-safe copy.")
    seed_key = f"{prefix}_contacts_seed"
    count_key = f"{prefix}_contacts_count"
    seed = tuple(tuple(contact.to_dict().items()) for contact in initial.contacts)
    if st.session_state.get(seed_key) != seed:
        st.session_state[seed_key] = seed
        st.session_state[count_key] = max(1, len(initial.contacts))
        for index, contact in enumerate(initial.contacts):
            st.session_state[contact_state_key(prefix, index, "name")] = contact.name
            st.session_state[contact_state_key(prefix, index, "email")] = contact.email
            st.session_state[contact_state_key(prefix, index, "role")] = contact.role

    contact_count = int(st.session_state.get(count_key, 1))
    contacts: list[DemoContact] = []
    for index in range(contact_count):
        col1, col2, col3 = st.columns([1.2, 1.4, 1])
        label_visibility = "visible" if index == 0 else "collapsed"
        with col1:
            name = st.text_input(
                "Name",
                key=contact_state_key(prefix, index, "name"),
                placeholder="Diana Andler",
                label_visibility=label_visibility,
                disabled=disabled,
            )
        with col2:
            email = st.text_input(
                "Email",
                key=contact_state_key(prefix, index, "email"),
                placeholder="diana@example.com",
                label_visibility=label_visibility,
                disabled=disabled,
            )
        with col3:
            role = st.text_input(
                "Role",
                key=contact_state_key(prefix, index, "role"),
                placeholder="IT Manager",
                label_visibility=label_visibility,
                disabled=disabled,
            )
        contact = DemoContact(name=name, email=email, role=role)
        if not contact.is_empty():
            contacts.append(contact)
    if not disabled and st.button("Add person", key=f"{prefix}_add_person"):
        st.session_state[count_key] = contact_count + 1
        st.rerun()
    if not disabled:
        st.caption("Clear every field in a row to remove that person from the saved recap.")
    return tuple(contacts)


def parse_call_datetime(value: str) -> tuple[date, time]:
    raw = value.strip()
    for fmt in ("%Y-%m-%d %H:%M", "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M", "%Y-%m-%dT%H:%M:%S"):
        try:
            parsed = datetime.strptime(raw, fmt)
            return parsed.date(), parsed.time().replace(second=0, microsecond=0)
        except ValueError:
            continue
    now = datetime.now()
    return now.date(), now.time().replace(second=0, microsecond=0)


def format_call_datetime(call_date: date, call_time: time) -> str:
    return datetime.combine(call_date, call_time).strftime("%Y-%m-%d %H:%M")


def render_recap_form_fields(
    prefix: str,
    initial: DemoRecap | None = None,
    *,
    demo_lead_values: Sequence[str] = (),
    disabled: bool = False,
) -> DemoRecap:
    initial = initial or DemoRecap(call_datetime=datetime.now().strftime("%Y-%m-%d %H:%M"))

    with st.container(border=True):
        render_section_heading("Identifiers removed before AI")
        st.caption("These details are saved internally. If they appear in recap notes, they are removed from AI summaries.")
        col1, col2, col3, col4 = st.columns([1.1, 1.1, 1.1, 1])
        with col1:
            organization_name = st.text_input(
                "Organization name *",
                value=initial.organization_name,
                key=f"{prefix}_organization_name",
                placeholder="e.g., Acme Corp",
                help="Saved for internal search. In AI summaries it becomes [ORG].",
                disabled=disabled,
            )
        with col2:
            lead_name = st.text_input(
                "Lead name *",
                value=initial.lead_name,
                key=f"{prefix}_lead_name",
                placeholder="e.g., Alex Morgan",
                help="Saved for internal search. In AI summaries it becomes [LEAD].",
                disabled=disabled,
            )
        with col3:
            location = st.text_input(
                "Location *",
                value=initial.location,
                key=f"{prefix}_location",
                placeholder="Brighton, MA",
                help="Saved internally. In AI summaries it becomes [LOCATION].",
                disabled=disabled,
            )
        with col4:
            current_demo_lead = initial.demo_lead.strip()
            demo_lead_options = demo_lead_select_options(current_demo_lead, demo_lead_values)
            demo_lead_index = demo_lead_options.index(current_demo_lead) if current_demo_lead in demo_lead_options else None
            selected_demo_lead = st.selectbox(
                "Demo lead *",
                options=demo_lead_options,
                index=demo_lead_index,
                key=f"{prefix}_demo_lead",
                help="Internal person who led the demo. Values come from saved recaps.",
                placeholder="Select a demo lead",
                disabled=disabled,
            )
            demo_lead = selected_demo_lead or ""

    with st.container(border=True):
        contacts = render_contact_editor(prefix, initial, disabled=disabled)

    with st.container(border=True):
        render_section_heading("Full recap notes")
        values: dict[str, Any] = {
            "organization_name": organization_name,
            "lead_name": lead_name,
            "demo_lead": demo_lead,
            "location": location,
            "contacts": contacts,
        }
        for group_label, expanded, fields in RAW_FIELD_GROUPS:
            with st.expander(group_label, expanded=expanded):
                render_section_heading(group_label)
                for field in fields:
                    values[field] = render_raw_field(prefix, initial, field, disabled=disabled)

    return DemoRecap(id=initial.id, created_at=initial.created_at, updated_at=initial.updated_at, **values)


def render_raw_field(prefix: str, initial: DemoRecap, field: str, *, disabled: bool = False) -> str:
    label, widget_type = RAW_FIELD_META[field]
    current = getattr(initial, field)
    help_text = RAW_FIELD_HELP.get(field)
    if field == "call_datetime":
        initial_date, initial_time = parse_call_datetime(current)
        col1, col2 = st.columns(2)
        with col1:
            call_date = st.date_input(
                "Call date",
                value=initial_date,
                key=f"{prefix}_{field}_date",
                help=help_text,
                disabled=disabled,
            )
        with col2:
            call_time = st.time_input("Call time", value=initial_time, key=f"{prefix}_{field}_time", disabled=disabled)
        return format_call_datetime(call_date, call_time)
    if widget_type == "line":
        return st.text_input(label, value=current, key=f"{prefix}_{field}", help=help_text, disabled=disabled)

    height = 180 if field in {"with_text", "needs", "questions_answers", "requests_during_demo"} else 120
    return st.text_area(label, value=current, height=height, key=f"{prefix}_{field}", help=help_text, disabled=disabled)


def render_secondary_filter_controls(prefix: str) -> tuple[str, str, str]:
    start_col, end_col, text_col = st.columns([1, 1, 2], gap="small")
    with start_col:
        selected_start = st.date_input(
            "Demo date from",
            value=None,
            key=f"{prefix}_filter_start",
            help="Show recaps from demo calls on or after this date.",
        )
    with end_col:
        selected_end = st.date_input(
            "Demo date to",
            value=None,
            key=f"{prefix}_filter_end",
            help="Show recaps from demo calls on or before this date.",
        )
    with text_col:
        text = st.text_input(
            "Notes contains",
            key=f"{prefix}_filter_text",
            help="Case-insensitive keyword search across needs, questions, requests, and follow-up notes.",
        )
    date_start = selected_start.isoformat() if selected_start else ""
    date_end = selected_end.isoformat() if selected_end else ""
    return date_start, date_end, text


def select_filter_value(label: str, values: Sequence[str], key: str, all_label: str, help_text: str | None = None) -> str:
    options = ["", *values]
    if st.session_state.get(key) not in options:
        st.session_state[key] = ""
    return str(
        st.selectbox(
            label,
            options=options,
            key=key,
            format_func=lambda value: all_label if value == "" else value,
            help=help_text,
        )
    )


def render_saved_filter_controls(conn: Any, prefix: str) -> SearchFilters:
    with st.container(border=True):
        render_section_heading("Filters")
        st.caption("Use saved values and optional text or date filters to narrow the recap list.")
        col1, col2, col3, col4 = st.columns(4, gap="small")
        with col1:
            lead = select_filter_value(
                "Lead name",
                list_lead_names(conn),
                f"{prefix}_filter_lead",
                "All leads",
                help_text="Saved lead names from existing recaps.",
            )
        with col2:
            org = select_filter_value(
                "Organization",
                list_organization_names(conn),
                f"{prefix}_filter_org",
                "All organizations",
                help_text="Saved organization names from existing recaps.",
            )
        with col3:
            demo_lead = select_filter_value(
                "Demo lead",
                list_demo_leads(conn),
                f"{prefix}_filter_demo_lead",
                "All demo leads",
                help_text="Internal demo leads from existing recaps.",
            )
        with col4:
            competition = select_filter_value(
                "Competition",
                list_competitions(conn),
                f"{prefix}_filter_competition",
                "All competition",
                help_text="Other tools or competitors mentioned in existing recaps.",
            )

        date_start, date_end, text = render_secondary_filter_controls(prefix)

    return SearchFilters(
        lead=lead,
        org=org,
        demo_lead=demo_lead,
        date_start=date_start,
        date_end=date_end,
        competition=competition,
        text=text,
    )


def render_new_recap_tab(conn: Any) -> None:
    demo_lead_values = list_demo_leads(conn)
    render_privacy_banner()
    left, right = st.columns([1.9, 1.05], gap="large")
    with left:
        recap = render_recap_form_fields("new", demo_lead_values=demo_lead_values)

    payload: dict[str, Any] | None = None
    payload_error: str | None = None
    try:
        payload = build_draft_ai_safe_payload(recap)
    except Exception as exc:  # pragma: no cover - UI-facing preview guard.
        payload_error = f"The safe copy cannot be built yet: {exc}"

    with right:
        render_safe_copy_rail(payload, error=payload_error)
        submitted = st.button("Save recap", type="primary", use_container_width=True)

    if submitted:
        missing = validate_recap_for_save(recap)
        if missing:
            st.error("Please complete these fields before saving: " + ", ".join(missing))
            return
        try:
            saved = save_recap(conn, recap)
        except Exception as exc:  # pragma: no cover - UI-facing error handling
            st.error(f"Save failed. Details: {exc}")
            return
        st.success(f"Saved recap #{saved.id}. AI-safe copy created. Known identifiers removed: {known_identifier_summary(saved)}.")


def format_result_datetime(value: str) -> str:
    text = value.strip()
    if not text:
        return "No date"
    try:
        parsed = datetime.strptime(text, "%Y-%m-%d %H:%M")
    except ValueError:
        return text
    return f"{parsed:%b} {parsed.day}, {parsed:%Y, %H:%M}"


def recap_result_title(recap: DemoRecap) -> str:
    return recap.organization_name.strip() or f"Recap #{recap.id or ''}".strip()


def recap_result_caption(recap: DemoRecap) -> str:
    lead = recap.lead_name.strip() or "No lead"
    demo_lead = recap.demo_lead.strip() or "No demo lead"
    return f"{lead} · {demo_lead} · {format_result_datetime(recap.call_datetime)}"


def join_present(parts: Sequence[str]) -> str:
    return " · ".join(part for part in parts if part)


def compact_text(value: str, limit: int = 160) -> str:
    text = " ".join(value.split())
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "..."


def recap_analysis_context(recap: DemoRecap) -> str:
    return join_present(
        (
            f"Users: {recap.user_count.strip()}" if recap.user_count.strip() else "",
            f"Competition: {recap.competition.strip()}" if recap.competition.strip() else "",
            f"Timeline: {recap.timeline.strip()}" if recap.timeline.strip() else "",
        )
    )


def recap_analysis_excerpt(recap: DemoRecap) -> str:
    source = recap.needs.strip() or recap.requests_during_demo.strip() or recap.questions_answers.strip() or recap.follow_up.strip()
    return compact_text(source)


def render_search_results_section(recaps: list[DemoRecap]) -> None:
    with st.container(border=True):
        render_section_heading("Results")
        st.caption(f"{plural_count(len(recaps), 'matching recap')}.")
        if not recaps:
            st.info("No matching recaps found.")
            return

        labels = {recap.id: recap_result_title(recap) for recap in recaps}
        options = [recap.id for recap in recaps if recap.id is not None]
        captions = [recap_result_caption(recap) for recap in recaps if recap.id is not None]
        with st.container(height=360, border=False):
            st.radio(
                "Recap results",
                options=options,
                key=SEARCH_SELECTED_RECAP_KEY,
                format_func=lambda recap_id: labels.get(recap_id, str(recap_id)),
                captions=captions,
                label_visibility="collapsed",
            )


def render_summary_result_row(recap: DemoRecap) -> None:
    title = recap_result_title(recap)
    meta = join_present(
        (
            f"Demo #{recap.id}" if recap.id is not None else "",
            recap.lead_name.strip() or "No lead",
            recap.demo_lead.strip() or "No demo lead",
            format_result_datetime(recap.call_datetime),
        )
    )
    context = recap_analysis_context(recap)
    excerpt = recap_analysis_excerpt(recap)
    st.markdown(
        f"""
        <div class="summary-result-row">
            <div class="summary-result-title">{escape(title)}</div>
            <div class="summary-result-meta">{escape(meta)}</div>
            {f'<div class="summary-result-context">{escape(context)}</div>' if context else ''}
            {f'<div class="summary-result-excerpt">{escape(excerpt)}</div>' if excerpt else ''}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_summary_results_section(recaps: list[DemoRecap]) -> None:
    with st.container(border=True):
        render_section_heading("Results")
        st.caption(f"{plural_count(len(recaps), 'matching recap')} will be included.")
        if not recaps:
            st.info("No matching recaps found.")
            return

        with st.container(height=420, border=False):
            for recap in recaps:
                render_summary_result_row(recap)


def current_safe_payload_preview(recap: DemoRecap) -> tuple[dict[str, Any] | None, str | None]:
    try:
        return build_current_ai_payload(recap).payload, None
    except Exception as exc:
        return None, f"The safe copy cannot be built yet: {exc}"


def plural_count(count: int, singular: str, plural: str | None = None) -> str:
    label = singular if count == 1 else plural or f"{singular}s"
    return f"{count} {label}"


def known_identifier_summary(recap: DemoRecap) -> str:
    parts: list[str] = []
    if recap.organization_name.strip():
        parts.append(plural_count(1, "organization"))
    if recap.lead_name.strip():
        parts.append(plural_count(1, "lead"))
    people_count = sum(1 for contact in recap.contacts if contact.name.strip())
    if people_count:
        parts.append(plural_count(people_count, "person", "people"))
    email_count = sum(1 for contact in recap.contacts if contact.email.strip())
    if email_count:
        parts.append(plural_count(email_count, "email"))
    if recap.location.strip():
        parts.append(plural_count(1, "location"))
    return ", ".join(parts) if parts else "known identifiers"


def selected_recap_from_session(conn: Any) -> DemoRecap | None:
    selected_id = st.session_state.get(SEARCH_SELECTED_RECAP_KEY)
    if not isinstance(selected_id, int):
        return None
    return get_recap(conn, selected_id)


def ensure_search_selection(recaps: list[DemoRecap]) -> None:
    options = [recap.id for recap in recaps if recap.id is not None]
    if not options:
        st.session_state.pop(SEARCH_SELECTED_RECAP_KEY, None)
        return
    if st.session_state.get(SEARCH_SELECTED_RECAP_KEY) not in options:
        st.session_state[SEARCH_SELECTED_RECAP_KEY] = options[0]


def search_detail_form_version() -> int:
    return int(st.session_state.get(SEARCH_FORM_VERSION_KEY, 0))


def reset_search_detail_form() -> None:
    st.session_state[SEARCH_FORM_VERSION_KEY] = search_detail_form_version() + 1


def start_search_editing(recap_id: int | None) -> None:
    if recap_id is None:
        return
    st.session_state[SEARCH_EDITING_RECAP_KEY] = recap_id
    reset_search_detail_form()
    st.rerun()


def stop_search_editing() -> None:
    st.session_state.pop(SEARCH_EDITING_RECAP_KEY, None)
    reset_search_detail_form()
    st.rerun()


def save_search_edit(conn: Any, edited: DemoRecap) -> None:
    missing = validate_recap_for_save(edited)
    if missing:
        st.error("Please complete these fields before saving: " + ", ".join(missing))
        return
    try:
        saved = save_recap(conn, edited)
    except Exception as exc:  # pragma: no cover - UI-facing error handling
        st.error(f"Save failed. Details: {exc}")
        return

    st.session_state[SEARCH_SELECTED_RECAP_KEY] = saved.id
    st.session_state.pop(SEARCH_EDITING_RECAP_KEY, None)
    reset_search_detail_form()
    st.session_state[SEARCH_SAVE_MESSAGE_KEY] = (
        f"Saved changes. AI-safe copy updated. Known identifiers removed: {known_identifier_summary(saved)}."
    )
    st.rerun()


def render_search_detail_form(conn: Any, selected: DemoRecap, *, editing: bool) -> DemoRecap:
    mode = "edit" if editing else "view"
    prefix = f"detail_{mode}_{selected.id}_{search_detail_form_version()}"
    return render_recap_form_fields(
        prefix,
        selected,
        demo_lead_values=list_demo_leads(conn),
        disabled=not editing,
    )


def render_search_safety_panel(conn: Any, selected: DemoRecap, edited: DemoRecap, *, editing: bool) -> None:
    if not editing:
        payload, payload_error = current_safe_payload_preview(selected)
        render_safe_copy_rail(
            payload,
            error=payload_error,
            pill_text="Current safe copy. Nothing is sent to AI.",
        )
        if st.button("Edit", type="primary", use_container_width=True, key=f"start_edit_{selected.id}"):
            start_search_editing(selected.id)
        return

    payload: dict[str, Any] | None = None
    payload_error: str | None = None
    try:
        payload = build_draft_ai_safe_payload(edited)
    except Exception as exc:  # pragma: no cover - UI-facing preview guard.
        payload_error = f"The safe copy cannot be built yet: {exc}"

    render_safe_copy_rail(payload, error=payload_error)
    submitted = st.button("Save changes", type="primary", use_container_width=True, key=f"save_edit_{selected.id}")
    if st.button("Cancel", use_container_width=True, key=f"cancel_edit_{selected.id}"):
        stop_search_editing()
    if submitted:
        save_search_edit(conn, edited)


def render_search_details_section(conn: Any, selected: DemoRecap | None) -> None:
    render_section_heading("Details")
    message = st.session_state.pop(SEARCH_SAVE_MESSAGE_KEY, None)
    if message:
        st.success(str(message))

    if selected is None:
        st.info("Select a recap from Results to view the full internal details.")
        return

    editing = st.session_state.get(SEARCH_EDITING_RECAP_KEY) == selected.id
    left, right = st.columns([1.9, 1.05], gap="large")
    with left:
        edited = render_search_detail_form(conn, selected, editing=editing)
    with right:
        render_search_safety_panel(conn, selected, edited, editing=editing)


def render_search_tab(conn: Any) -> None:
    render_info_banner(
        "Find saved recaps",
        "Filter saved demo recaps, select a result, and review the full internal recap with AI-safe status.",
        icon="article",
    )
    filters = render_saved_filter_controls(conn, "find")
    recaps = search_recaps(conn, filters)
    ensure_search_selection(recaps)
    render_search_results_section(recaps)
    selected = selected_recap_from_session(conn)
    if selected and selected.id not in {recap.id for recap in recaps}:
        selected = None
    render_search_details_section(conn, selected)


def render_analysis_goal_section() -> AnalysisType:
    with st.container(border=True):
        render_section_heading("Analysis Goal")
        return st.radio(
            "Analysis goal",
            options=ANALYSIS_TYPES,
            index=0,
            format_func=analysis_option_label,
            captions=[ANALYSIS_OPTION_CAPTIONS[item] for item in ANALYSIS_TYPES],
            label_visibility="collapsed",
            key="summary_analysis_goal",
        )


def render_run_analysis_section(
    conn: Any,
    recaps: list[DemoRecap],
    analysis_type: AnalysisType,
    payload_errors: list[str],
    can_run: bool,
) -> None:
    with st.container(border=True):
        render_section_heading("Run Analysis")
        if payload_errors:
            st.error("Some matching recaps cannot be prepared for AI summaries.")
            for error in payload_errors:
                st.caption(error)
        elif not recaps:
            st.info("Choose filters that match at least one recap.")
        else:
            st.caption("Analysis runs on AI-safe recap data and cites supporting demo IDs only.")

        if st.button("Run analysis", type="primary", disabled=not can_run, use_container_width=True):
            payloads, _refreshed_count, generation_errors = refresh_ai_payloads(conn, recaps)
            if generation_errors:
                st.error("Some recaps could not be prepared for AI summaries.")
                for error in generation_errors:
                    st.caption(error)
                return
            try:
                with st.spinner("Generating summary from safe copies..."):
                    summary = summarize_with_llm(payloads, analysis_type)
            except Exception as exc:  # pragma: no cover - UI-facing API error handling.
                st.error(f"AI summary failed: {exc}")
                return
            st.markdown("##### Trend summary")
            st.markdown(summary)


def render_ai_summary_tab(conn: Any) -> None:
    render_info_banner(
        "Summarize trends",
        "Filter saved demo recaps, review which recaps will be included, choose an analysis goal, and run an AI summary built from sanitized recap fields.",
        icon="insights",
    )
    filters = render_saved_filter_controls(conn, "summary")
    recaps = search_recaps(conn, filters)
    render_summary_results_section(recaps)
    analysis_type = render_analysis_goal_section()
    preview_payloads, _stale_count, payload_errors = preview_ai_payloads(conn, recaps)
    render_run_analysis_section(
        conn,
        recaps,
        analysis_type,
        payload_errors,
        can_run=bool(preview_payloads) and not payload_errors,
    )


def render_sidebar() -> str:
    st.sidebar.markdown(
        f"""
        <div class="brand-lockup">
            <div class="brand-mark">{material_symbol("insights")}</div>
            <div class="brand-name">Demo<br>Insights</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    selected = st.sidebar.radio(
        "Navigation",
        options=[item[0] for item in NAV_ITEMS],
        format_func=lambda value: dict(NAV_ITEMS)[value],
        label_visibility="collapsed",
        key="navigation",
    )
    return str(selected)
