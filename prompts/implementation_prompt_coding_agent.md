# Coding Agent Implementation Prompt

You are a coding agent working inside this repository:

```text
/home/przemek/Nauka/demo-intelligence-capture-system
```

Implement the full working prototype in this repository. Do not return a ZIP. Edit files in place, create the application source files, and verify the result with the CLI commands listed below.

## Source Of Truth

Read these files first:

```text
AGENTS.md
docs/description.md
docs/request.md
```

Use `docs/description.md` as the implementation source of truth. `docs/request.md` is the original request and should only be used to understand intent.

Do not rewrite the spec while implementing unless a tiny correction is necessary to keep the implementation and spec aligned. Preserve unrelated files and user edits.

## Implementation Goal

Build a complete Streamlit + SQLite prototype that proves the risky contract:

```text
Store full demo recap data internally.
Generate a deterministic sanitized derived payload.
Summarize only from stored sanitized payloads.
Never send identifying/raw recap data to AI.
```

The result should be runnable locally and demo-ready with synthetic data.

## Non-Negotiable Requirements

- Full raw recap data is stored internally.
- The full `WITH` answer is preserved exactly as submitted.
- Organization name, lead name, and demo lead are explicit metadata fields and are not inferred from `WITH`.
- SQLite is used through `sqlite3`.
- Streamlit UI exists with three tabs:
  - `New Demo Recap`
  - `Search Recaps`
  - `AI Trend Summary`
- Two conceptual tables exist:
  - `demo_recaps`
  - `demo_recap_ai_payloads`
- `demo_recaps` is the internal source of truth.
- `demo_recap_ai_payloads` stores a derived AI-safe payload.
- Saving/editing a recap regenerates the sanitized payload.
- AI summaries read from `demo_recap_ai_payloads`, not raw recap rows.
- Direct LLM calls never receive raw recap rows, raw full recap text, organization names, lead names, contact names, contact emails, or exact locations.
- Sanitization is deterministic and not dummy placeholder logic.
- OpenAI/OpenAI-compatible client is isolated behind a small adapter abstraction.
- Dry-run/no-LLM mode exists.
- Thin CLI exists for verification.
- Meaningful synthetic demo data exists.
- Do not add tests.
- Do not add RAG, embeddings, vector database, autonomous agents, complex permissions, event pipelines, production deployment infrastructure, or invented architecture.

## Engineering Quality Bar

Implement like a staff engineer:

- Keep responsibilities clean and obvious.
- Use strong Python typing throughout.
- Prefer dataclasses or typed records where they clarify contracts.
- Keep files cohesive and reasonably short.
- Use direct functions and simple modules.
- Add abstraction only for real current boundaries, especially the LLM adapter.
- Keep the privacy boundary obvious in code.
- Avoid fake repositories, generic service frameworks, background machinery, and pass-through layers.
- Keep the UI clean and practical, not decorative or overcomplicated.
- Make the README accurate enough for another agent to run the app.
- Include a repo-local `.env.example` documenting configuration keys. Load configuration from a repo-local `.env` file when present, falling back to environment variables. Do not put real secrets in `.env.example`; use empty or obvious placeholder values.
- Choose a simple, cohesive layout that makes the main responsibilities easy to find: Streamlit entrypoint, CLI entrypoint, database/schema code, typed models, recap save/search logic, sanitization and AI-safe payload building, LLM adapter, summarization, and synthetic data.
- Keep the layout as small as the implementation allows; do not create files that do not earn their keep.

## Required Functions / Concepts

Implement direct, readable functions equivalent to:

- `save_recap()`
- `search_recaps()`
- `sanitize_text()`
- `build_ai_safe_payload()`
- `save_ai_safe_payload()`
- `summarize_with_llm()`

`save_recap()` should own the raw-save and payload-refresh lifecycle. It should save the raw recap and upsert the generated AI-safe payload in one SQLite transaction.

A successful recap save always leaves a fresh sanitized payload for that recap. If payload generation fails, report the failure and do not treat the recap as ready for AI summaries.

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

`demo_recap_ai_payloads.payload_json` is derived. Do not edit it directly in UI. If preview looks unsafe, the user fixes raw recap or explicit metadata and saves again.

## Raw Recap Fields

The form must ask for and save every uppercase heading from the sample recap email:

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

Additional metadata fields:

- Organization name
- Lead name
- Demo lead

These metadata fields are entered directly and are not inferred from `WITH`.

## Sanitization Contract

Sanitization is the highest-risk part. Implement it carefully and deterministically.

Minimum redaction:

- Replace email addresses with `[EMAIL]`.
- Replace URLs with `[URL]`.
- Replace organization name with `[ORG]`.
- Replace lead name with `[LEAD]`.
- Replace known contact names with `[CONTACT]`.
- Replace exact location with `[LOCATION]`.

Known redaction values:

- Organization name from `organization_name`.
- Lead name from `lead_name`.
- Exact location from `location`.
- Contact name candidates from `with_text`, split by line and `|`, excluding email addresses and empty values.

Implementation guidance:

- Redact case-insensitively where practical.
- Redact longer known phrases before shorter phrases.
- Escape regex inputs properly.
- It is acceptable to over-redact attendee names.
- It is not acceptable to under-redact known identifying values.
- Do not use AI for sanitization.
- Do not use NER or DLP services.

## AI-Safe Payload Contract

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

For v1, payload values should be selected analytical field text after deterministic redaction. Do not use AI or semantic summarization to create the stored payload.

`call_month` is derived best-effort from `call_datetime`. If the date cannot be parsed, use `None`/`null`.

## LLM Adapter Contract

Use the official OpenAI Python client or an OpenAI-compatible client behind a small adapter.

The rest of the app should depend on a protocol/interface like:

```python
class LlmClient(Protocol):
    def summarize(self, prompt: str) -> str: ...
```

Provide:

- `OpenAiLlmClient`
  - reads `OPENAI_API_KEY` from repo-local `.env` when present, then environment variables
  - reads `OPENAI_MODEL` from repo-local `.env` when present, then environment variables
  - optionally reads `OPENAI_BASE_URL` from repo-local `.env` when present, then environment variables

- `DryRunLlmClient`
  - deterministic no-network behavior
  - used when no API key is configured or when CLI uses `--dry-run`

No raw database rows may reach the LLM adapter.

## Streamlit UI

Build three tabs:

1. `New Demo Recap`
   - Guided form for explicit metadata and all raw recap fields.
   - Saving creates/updates the raw recap and derived sanitized payload.

2. `Search Recaps`
   - Filters by lead name, organization/name text, date range, demo lead, user count text, competition, timeline, and text across needs/questions/requests/follow-up.
   - Shows result list with date, organization, lead name, demo lead, user count, timeline, and short needs/requests excerpt.
   - Selecting a result opens full raw recap detail and per-recap sanitized AI payload preview.
   - Allows editing and saving; saving regenerates the payload.

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
   - App builds and previews exact action-specific sanitized batch input.
   - User confirms.
   - App calls the LLM adapter or dry-run client.
   - Output cites supporting demo IDs only.

## CLI Verification Surface

Implement a thin CLI with commands equivalent to:

```bash
<cli command> init-db
<cli command> seed-demo-data
<cli command> search --lead "Diana"
<cli command> preview-ai-payload --recap-id 1
<cli command> summarize --analysis popular_requests --dry-run
```

CLI commands:

- `init-db`
  - creates schema

- `seed-demo-data`
  - inserts at least 6 meaningful fake recaps
  - generates sanitized payloads

- `search`
  - supports at least `--lead`, `--org`, `--demo-lead`, and `--text`

- `preview-ai-payload --recap-id ID`
  - prints stored sanitized payload

- `summarize --analysis ANALYSIS_TYPE [--dry-run]`
  - builds same sanitized batch input as UI
  - with `--dry-run`, prints LLM input and does not call LLM

## Synthetic Data

Seed at least 6 realistic but fake demo recaps.

They should demonstrate:

- varied organizations
- varied leads
- varied demo leads
- varied locations
- varied user counts
- varied needs/questions/requests/follow-up
- emails redacted to `[EMAIL]`
- URLs redacted to `[URL]`
- organization names redacted to `[ORG]`
- lead names redacted to `[LEAD]`
- contact names redacted to `[CONTACT]`
- locations redacted to `[LOCATION]`

Use fake names, fake organizations, fake emails, and fake URLs.

## Verification To Run Before Final Response

Run the CLI verification path, using the actual CLI entrypoint chosen by the implementation:

```bash
<cli command> init-db
<cli command> seed-demo-data
<cli command> search --lead "Diana"
<cli command> preview-ai-payload --recap-id 1
<cli command> summarize --analysis popular_requests --dry-run
```

Also run a lightweight syntax/import check, for example:

```bash
python -m compileall <application source paths>
```

If dependencies need installation, install them with the repo's normal Python tooling. Keep dependency choices minimal.

Do not add tests.

## Final Response

When finished, report:

- main files created
- how to run the app
- how to seed demo data
- CLI verification commands and results
- any skipped verification or residual risks

Keep the final response concise.
