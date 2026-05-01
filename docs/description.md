# Demo Recap Intelligence Prototype

## Purpose

Build a small prototype that replaces demo recap emails with a guided form and a searchable SQLite database.

## Functional Requirements

The tool must let the demo team:

1. Answer the existing recap category questions.
2. Save the answers into a small database.
3. Search saved recaps by lead name, organization/name text, date, and demo lead.
4. Preview the sanitized AI-safe payload generated for each recap.
5. Send only stored sanitized recap sections to AI for simple trend summaries.

The prototype exists to prove the request in `docs/request.md`.

## Prototype Scope

Build only this:

- A simple web UI.
- A SQLite database.
- A new demo recap form based on the existing email headings.
- A search/list view for saved recaps.
- A recap detail view for internal users.
- An AI-safe payload builder that runs when a recap is saved or edited.
- A stored sanitized AI payload for each recap.
- A per-recap AI-safe preview so unsafe sanitization can be fixed while the recap context is small.
- A basic AI trend summary action where the user chooses an analysis type, previews the combined sanitized batch input, and the app analyzes only stored sanitized fields from saved recaps matching the user's filters.

Anything not required for that flow is out of scope for this prototype.

## Raw Recap Data

The form should ask for and save every uppercase heading from the sample recap email as raw internal data.

For each recap category, the submitted raw answer text is stored as the internal source of truth. Parsed search fields and convenience fields do not replace the original raw answer.

Raw fields saved to the database:

- `DETAILS ABOUT ORGANIZATION`
- `THE CALL TOOK PLACE ON DATE & TIME`
- `WITH`
- `USER COUNT`
- `LOCATION`
- `FIRST HEARD OF GAT`
- `COMPETITION TO GAT`
- `DEVICES`
- `BUDGET`
- `AUTHORITY`
- `TIMELINE`
- `NEEDS`
- `DEMO DISCUSSION`
- `QUESTIONS`
- `REQUESTS DURING DEMO`
- `FOLLOW UP`

These raw fields are the internal source of truth. They are used for internal recap detail, editing, and traceability.

In particular, the full `WITH` answer must be preserved exactly as submitted, even if the app derives contact names temporarily for redaction.

The corresponding database columns may use normalized snake_case names, but they store the submitted raw answer text for each recap category.

Additional internal metadata fields, captured explicitly in the form for search and reporting:

- Organization name
- Lead name
- Demo lead

These metadata fields are entered directly. They are not inferred from the raw `WITH` answer.

For implementation, the UI can group the raw recap fields and explicit metadata fields:

Identity/search fields, never sent to AI:

- Organization name
- Lead name
- Full `WITH` answer, including contact names and emails
- Call date and time
- Demo lead
- Location

AI-useful analytical fields after sanitization:

- `USER COUNT`
- `FIRST HEARD OF GAT`
- `COMPETITION TO GAT`
- `TIMELINE`
- `NEEDS`
- `DEMO DISCUSSION`
- `QUESTIONS`
- `REQUESTS DURING DEMO`
- `FOLLOW UP`

## Database

Use two SQLite tables for the prototype: one for the full internal recap and one for the derived sanitized AI-safe payload.

```sql
CREATE TABLE demo_recaps (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    organization_name TEXT,
    lead_name TEXT,
    demo_lead TEXT,
    with_text TEXT,
    call_datetime TEXT,
    location TEXT,
    user_count TEXT,
    first_heard_of_gat TEXT,
    competition TEXT,
    devices TEXT,
    budget TEXT,
    authority TEXT,
    timeline TEXT,
    organization_details TEXT,
    needs TEXT,
    demo_discussion TEXT,
    questions_answers TEXT,
    requests_during_demo TEXT,
    follow_up TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE demo_recap_ai_payloads (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    recap_id INTEGER NOT NULL,
    payload_json TEXT NOT NULL,
    redaction_version TEXT DEFAULT 'v1',
    generated_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (recap_id) REFERENCES demo_recaps(id),
    UNIQUE (recap_id)
);
```

This is enough for the prototype.

`demo_recaps` stores both the original raw category answers and separate explicit metadata fields used for internal search.

`demo_recap_ai_payloads` stores the latest derived AI-safe payload for each recap. It is not the source of truth; if the raw recap or redaction-relevant metadata changes, regenerate the payload from `demo_recaps`.

Do not edit `payload_json` directly. If the per-recap preview looks unsafe or wrong, fix the raw recap or explicit metadata, then regenerate the payload.

`save_recap()` owns the raw-save and payload-refresh lifecycle. It should save the raw recap and upsert the generated AI-safe payload in one SQLite transaction.

A successful recap save always leaves a fresh sanitized payload for that recap. If payload generation fails, report the failure and do not treat the recap as ready for AI summaries.

## Search

The search view should support:

- Lead name
- Organization/name text search
- Date range
- Demo lead
- User count text
- Competition
- Timeline
- Text search across needs, questions, requests, and follow up

Interpret the original request's "name scroll" requirement as substring text search. For the prototype, organization/name text search should run across `organization_name` and `organization_details`.

The result list should show:

- Date
- Organization
- Lead name
- Demo lead
- User count
- Timeline
- Short needs or requests excerpt

Selecting a row opens the full internal recap detail.

## AI Privacy Boundary

The LLM must never receive:

- Organization name
- Lead name
- Contact names
- Contact emails
- Exact location
- Raw full recap text

The privacy boundary is enforced by strict field selection and deterministic redaction in `build_ai_safe_payload()`.

`build_ai_safe_payload()` is the only code path allowed to read raw recap data for AI preparation and write `demo_recap_ai_payloads.payload_json`. No direct LLM call may query `demo_recaps` or receive raw recap rows, raw recap text, or identity fields.

When a recap is saved or edited, the prototype must:

1. Save the full raw questionnaire data in `demo_recaps`.
2. Call `build_ai_safe_payload()` for that recap.
3. Select only allowed AI-useful analytical fields from the saved raw recap.
4. Apply deterministic redaction for known organization names, lead names, contact names, emails, URLs, and exact locations.
5. Upsert the sanitized payload into `demo_recap_ai_payloads`.
6. Show the per-recap sanitized preview in the recap detail.

If the per-recap preview is unsafe, the user fixes the raw recap or explicit metadata and regenerates the payload. There is no separate approve/reject workflow.

Editing and saving a recap regenerates the payload automatically. The recap detail view may also expose a manual "Regenerate AI-safe payload" action for cases where redaction rules changed.

When a user requests an AI summary, the prototype must:

1. Select matching recaps using internal filters.
2. Load or refresh only their stored sanitized payloads from `demo_recap_ai_payloads`.
3. Verify the selected payloads are current and AI-safe.
4. Build the action-specific AI input from those sanitized payloads.
5. Send only that sanitized batch input when the user chooses to generate the summary.

Preview is for transparency and correction, not a substitute for sanitization. A persisted approval/rejection workflow is out of scope unless explicitly requested later.

For multi-recap summaries, the UI may show the combined sanitized batch payload in an optional preview. Mandatory human review is not the security boundary; automated field selection, redaction, staleness checks, and validation are.

Minimum redaction rules:

- Replace email addresses with `[EMAIL]`.
- Replace URLs with `[URL]`.
- Replace the organization name with `[ORG]`.
- Replace the lead name with `[LEAD]`.
- Replace known contact names with `[CONTACT]`.
- Replace the exact location with `[LOCATION]`.

Known redaction values come from explicit metadata and simple deterministic extraction:

- Organization name from `organization_name`.
- Lead name from `lead_name`.
- Exact location from `location`.
- Contact name candidates from `with_text`, split by line and `|`, excluding email addresses and empty values.

It is acceptable for the prototype to over-redact attendee names. It is not acceptable to under-redact known identifying values.

## AI-Safe Payload

The stored AI payload should contain only sanitized fields that may be useful for AI trend analysis.

The payload is a derived analytical view, not a copy of the raw recap. `build_ai_safe_payload()` selects only allowed analytical fields and applies deterministic redaction. It must not pass through identity fields or raw full recap text.

For v1, payload values should be the selected analytical field text after deterministic redaction. Do not use AI or semantic summarization to create this stored payload. If a field is too long for practical preview, the app may show a truncated preview, but the stored value should remain the sanitized field text.

Example shape:

```json
{
  "demo_id": 12,
  "call_month": "2026-04",
  "user_count": "335 showing in console",
  "first_heard_of_gat": "Google Search - Colleague had recommended GAM but not looking to go through that implementation.",
  "competition": "None",
  "timeline": "Probably after the trial it seems",
  "needs": "lots of steps to onboard/offboard employees\n\nneed to change a user's password and log in as them to set an auto responder, email forwarding etc.",
  "demo_discussion": "Customer in trial for the past 10 days\n\nThey like the look of Flow, but cannot run the actions, so want to see it in action.",
  "questions_answers": "Q1: Will any workflow actions overwrite policies in Google?\nA1: No.\n\nQ2: Can we set a time frame for deleting accounts based on certain criteria.\nA2: Demonstrated how to accomplish in Flow.",
  "requests_during_demo": "[URL]\n\nCustomer sets autoforwarding and an auto reply as part of the offboarding workflow\n\nGenerate and send 2fa backup codes to the end user over email via workflow - not sure it will be possible",
  "follow_up": "Reply to thread with documentation on GAT - Done\n\nFormal Quote Not Requested\n\nExtend trial - Done"
}
```

`call_month` is derived best-effort from `call_datetime`. If the date cannot be parsed, use `null`.

No identity fields belong in this payload.

For each AI action, the app should build a smaller action-specific view from the stored sanitized payloads.

Examples:

- Popular requests: use `requests_during_demo`, and optionally related `needs`.
- Common questions: use `questions_answers`.
- Common needs: use `needs`.
- Follow-up themes: use `follow_up`.
- General trend summary: use all AI-safe sections.

## AI Trend Summary

The AI trend summary action should be simple:

1. User chooses filters. With no filters, all saved recaps are in scope.
2. User chooses analysis type: popular requests, common questions, common needs, follow-up themes, or general trend summary.
3. App selects all saved recaps matching those filters.
4. App prepares current AI-safe payload previews through the approved builder without writing to the database.
5. App shows a compact AI-safe status and optional payload preview.
6. User clicks `Generate summary`.
7. App refreshes stale stored sanitized payloads from `demo_recap_ai_payloads`.
8. App asks the LLM to identify general or popular requests, questions, needs, or follow-up themes.
9. App displays the answer with supporting demo IDs only.

The LLM prompt should instruct the model to summarize only the provided sanitized records and avoid guessing customer identities.

## Recommended First Build

Use:

- Python
- Streamlit
- SQLite
- `sqlite3`
- An OpenAI-compatible LLM client only for the summary step

Build three tabs:

1. New Demo Recap
2. Search Recaps, with full recap detail and per-recap AI-safe preview opened from the selected result
3. AI Trend Summary, with compact AI-safe status, optional sanitized preview, and one generate action

Keep the implementation direct. Separate functions are enough:

- `save_recap()`
- `search_recaps()`
- `sanitize_text()`
- `build_ai_safe_payload()`
- `save_ai_safe_payload()`
- `summarize_with_llm()`

## Acceptance Criteria

The prototype is complete when:

1. A user can create a recap through the questionnaire.
2. The full raw recap, including the submitted `WITH` answer, is saved in SQLite.
3. Explicit search metadata including organization name, lead name, and demo lead is captured without inferring those values from `WITH`.
4. A sanitized AI payload is generated through `build_ai_safe_payload()` when the recap is saved or edited.
5. The sanitized payload is stored in `demo_recap_ai_payloads` as a derived view.
6. A user can find recaps by lead name, organization/name text, date, and demo lead.
7. A user can open the full internal recap detail and the per-recap sanitized preview.
8. If the sanitized preview is unsafe, the user can fix the raw recap or metadata; saving regenerates the payload.
9. A user can generate a simple AI summary over all saved recaps matching the user's filters after the app verifies the selected AI-safe payloads.
10. The AI summary path reads from `demo_recap_ai_payloads`, not from raw recap rows.
11. The LLM input contains no organization names, lead names, contact names, contact emails, exact locations, or raw full recap text.
