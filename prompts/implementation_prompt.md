# Implementation Prompt

You are ChatGPT Pro acting as a senior/staff Python engineer. Build a complete working prototype application from the self-contained specification below and return it as a downloadable ZIP archive.

The goal is not to create a large architecture. The goal is a small, production-shaped prototype where the privacy boundary is implemented with real discipline.

## Output Requirements

Return a ZIP archive containing a full working application. Include all source files, a `README.md`, dependency file, and setup/run instructions.

Do not return only snippets. Do not omit files. Do not ask follow-up questions unless the spec is impossible to implement.

Include a repo-local `.env.example` file documenting configuration keys. The app should load configuration from a repo-local `.env` file when present, falling back to environment variables. Do not include real secrets in `.env.example`; use empty or obvious placeholder values.

The app must run locally with a simple setup. Include the exact commands in `README.md`. The flow should be equivalent to:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
<cli command> init-db
<cli command> seed-demo-data
<streamlit command>
```

Also include CLI verification commands so an automated coding agent can validate the important behavior without clicking through the UI. The command names may differ, but the verification flow must be equivalent to:

```bash
<cli command> init-db
<cli command> seed-demo-data
<cli command> search --lead "Diana"
<cli command> preview-ai-payload --recap-id 1
<cli command> summarize --analysis popular_requests --dry-run
```

Do not add a test suite. The CLI is the verification surface for this prototype.

## Engineering Quality Bar

Implement with staff-level quality:

- Keep responsibilities clean and obvious.
- Use strong Python typing throughout.
- Prefer dataclasses or typed records over loose dictionaries where they clarify contracts.
- Keep files cohesive and reasonably short.
- Use direct functions and simple modules; do not invent frameworks, services, repositories, event buses, or generic layers.
- Add abstraction only where the current prototype needs a real boundary.
- The OpenAI client must be behind a small adapter abstraction so the rest of the app does not import or depend directly on OpenAI.
- The database layer should use `sqlite3` directly.
- The UI should be clean, practical, and pleasant, but not overdesigned.
- The prototype should feel demo-ready with sensible synthetic data.
- Do not add authentication, permissions, background jobs, embeddings, RAG, vector databases, agents, telemetry frameworks, or deployment infrastructure.
- Do not add tests.

The privacy/sanitization code is the highest-risk part. It must not be dummy logic. It should be deterministic, readable, and easy to inspect.

## Implementation Guidelines

Use Python 3.11+.

Choose a simple, cohesive project layout that makes the main responsibilities easy to find: Streamlit entrypoint, CLI entrypoint, database/schema code, typed models, recap save/search logic, sanitization and AI-safe payload building, LLM adapter, summarization, and synthetic data. Keep the layout as small as the implementation allows, and document the exact run commands in `README.md`.

## Required Behavior Summary

Build a Streamlit + SQLite prototype that:

1. Lets the demo team enter a demo recap through a guided form.
2. Saves the full raw recap internally.
3. Saves explicit metadata for search: organization name, lead name, demo lead.
4. Preserves the full `WITH` answer exactly as submitted.
5. Generates and stores a sanitized AI-safe payload whenever a recap is saved or edited.
6. Lets internal users search recaps.
7. Lets internal users open the full raw recap detail and view the per-recap sanitized AI payload.
8. If the sanitized preview is unsafe, users can edit raw recap/metadata and saving regenerates the payload.
9. Lets users run simple AI trend summaries over selected recaps.
10. AI trend summaries must read from stored sanitized payloads, not raw recap rows.
11. The LLM input must contain no organization names, lead names, contact names, contact emails, exact locations, or raw full recap text.

## UI Requirements

Build three Streamlit tabs:

1. `New Demo Recap`
   - Form for explicit metadata and all raw recap category fields.
   - Save button.
   - Saving creates/updates the raw recap and the derived sanitized payload.

2. `Search Recaps`
   - Search/filter by lead name, organization/name text, date range, demo lead, user count text, competition, timeline, and text across needs/questions/requests/follow-up.
   - Show result list with date, organization, lead name, demo lead, user count, timeline, and short needs/requests excerpt.
   - Selecting a result opens the full raw recap detail plus the per-recap sanitized AI payload preview.
   - Allow editing a recap and saving; saving regenerates the sanitized payload.

3. `AI Trend Summary`
   - User chooses filters.
   - User chooses analysis type:
     - `popular_requests`
     - `common_questions`
     - `common_needs`
     - `follow_up_themes`
     - `general_trend_summary`
   - App selects matching recaps.
   - App loads stored sanitized payloads only.
   - App builds the exact action-specific sanitized batch input.
   - App previews the combined sanitized batch input once.
   - User confirms the request.
   - App calls the LLM through the adapter and displays a summary with supporting demo IDs only.
   - Include a dry-run/no-LLM mode if no API key is configured.

The UI should be usable and polished enough for a demo, but keep it straightforward. Avoid decorative complexity.

## CLI Requirements

Implement a thin CLI using `argparse` or another standard/simple option:

- `init-db`
  - Creates the SQLite schema.

- `seed-demo-data`
  - Inserts meaningful synthetic recaps and generates sanitized payloads.
  - Data should look realistic but must be fake.

- `search`
  - Supports at least `--lead`, `--org`, `--demo-lead`, and `--text`.
  - Prints matching recap IDs and key fields.

- `preview-ai-payload --recap-id ID`
  - Prints the stored sanitized payload for one recap.

- `summarize --analysis ANALYSIS_TYPE [--dry-run]`
  - Builds the same sanitized batch input the UI would use.
  - With `--dry-run`, prints the LLM input and does not call the LLM.
  - Without `--dry-run`, calls the configured LLM adapter.

The CLI should make the app easy for a coding agent to verify without tests.

## LLM Adapter Requirements

Use the official OpenAI Python client or an OpenAI-compatible client, but isolate it behind an adapter.

The rest of the app should depend on a small protocol/interface like:

```python
class LlmClient(Protocol):
    def summarize(self, prompt: str) -> str: ...
```

Provide:

- `OpenAiLlmClient`
  - Reads API key/model/base URL from repo-local `.env` when present, then environment variables.
  - Reasonable configuration names:
    - `OPENAI_API_KEY`
    - `OPENAI_MODEL`
    - `OPENAI_BASE_URL` optional.

- `DryRunLlmClient`
  - Returns a deterministic placeholder summary and/or prints the prompt.
  - Used when no API key is configured or when CLI uses `--dry-run`.

Do not let raw database rows reach the LLM adapter. The adapter should only receive the already built sanitized batch prompt/input.

## Synthetic Data Requirements

Include at least 6 realistic synthetic demo recaps. They should cover different:

- organizations
- leads
- demo leads
- locations
- user counts
- needs
- questions
- requests
- follow-up themes

Use fake names, fake organizations, fake emails, and fake URLs. Do not use real customer data.

The seeded data should demonstrate that sanitization works:

- emails become `[EMAIL]`
- URLs become `[URL]`
- organization names become `[ORG]`
- lead names become `[LEAD]`
- contact names from `WITH` become `[CONTACT]`
- exact locations become `[LOCATION]`

## Sanitization Requirements

Sanitization is not dummy logic. Implement it carefully.

Minimum redaction:

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

Implementation guidance:

- Redact case-insensitively where practical.
- Redact longer known phrases before shorter phrases to avoid partial replacement problems.
- Escape regex inputs properly.
- Keep `sanitize_text()` small and readable.
- Keep contact-name extraction deterministic and easy to audit.
- Do not use AI for sanitization.
- Do not use NER or DLP services.

## Database Contract

Use SQLite with `sqlite3` directly.

Create these two conceptual tables:

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

`demo_recaps` is the internal source of truth.

`demo_recap_ai_payloads` is a derived AI-safe view. Do not edit `payload_json` directly. If preview looks unsafe, users fix the raw recap or explicit metadata, then saving regenerates the payload.

`save_recap()` owns the raw-save and payload-refresh lifecycle. It should save the raw recap and upsert the generated AI-safe payload in one SQLite transaction.

A successful recap save always leaves a fresh sanitized payload for that recap. If payload generation fails, report the failure and do not treat the recap as ready for AI summaries.

## Raw Recap Fields

The form should ask for and save every uppercase heading from the sample recap email as raw internal data:

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

For each recap category, the submitted raw answer text is stored as the internal source of truth. Parsed search fields and convenience fields do not replace the original raw answer.

In particular, the full `WITH` answer must be preserved exactly as submitted, even if the app derives contact names temporarily for redaction.

Additional metadata fields are captured explicitly in the form:

- Organization name
- Lead name
- Demo lead

These metadata fields are entered directly. They are not inferred from the raw `WITH` answer.

## AI-Safe Payload Contract

The stored AI payload should contain only sanitized fields useful for AI trend analysis.

Allowed payload fields:

- `demo_id`
- `call_month`
- `user_count`
- `first_heard_of_gat`
- `competition`
- `timeline`
- `needs`
- `demo_discussion`
- `questions_answers`
- `requests_during_demo`
- `follow_up`

No identity fields belong in this payload.

The payload is a derived analytical view, not a copy of the raw recap. `build_ai_safe_payload()` selects only allowed analytical fields and applies deterministic redaction. It must not pass through identity fields or raw full recap text.

For v1, payload values should be the selected analytical field text after deterministic redaction. Do not use AI or semantic summarization to create this stored payload. If a field is too long for practical preview, the app may show a truncated preview, but the stored value should remain the sanitized field text.

`call_month` is derived best-effort from `call_datetime`. If the date cannot be parsed, use `null`.

Example payload shape:

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

## Search Contract

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

## AI Trend Summary Contract

Supported analysis types:

- `popular_requests`: use `requests_during_demo`, optionally with `needs`.
- `common_questions`: use `questions_answers`.
- `common_needs`: use `needs`.
- `follow_up_themes`: use `follow_up`.
- `general_trend_summary`: use all AI-safe sections.

Flow:

1. User chooses filters. With no filters, all saved recaps are in scope.
2. User chooses analysis type.
3. App selects all saved recaps matching those filters.
4. App loads their stored sanitized payloads from `demo_recap_ai_payloads`.
5. App builds and previews the exact action-specific sanitized batch input.
6. After user confirmation, app asks the LLM to identify general or popular requests, questions, needs, or follow-up themes.
7. App displays the answer with supporting demo IDs only.

For multi-recap summaries, preview the combined sanitized batch payload once. The user confirms the AI request as a whole; individual per-recap approval is not required.

The LLM prompt should instruct the model to summarize only the provided sanitized records and avoid guessing customer identities.

The LLM output must cite supporting demo IDs, not customer names.

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
9. A user can generate a simple AI summary over all saved recaps matching the user's filters after confirming the combined sanitized batch preview.
10. The AI summary path reads from `demo_recap_ai_payloads`, not from raw recap rows.
11. The LLM input contains no organization names, lead names, contact names, contact emails, exact locations, or raw full recap text.

## Final Response Format

Return the completed project as a ZIP archive. Also include a brief note with:

- how to install
- how to seed demo data
- how to run the Streamlit app
- how to run CLI dry-run verification
