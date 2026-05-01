# AGENTS.md

## Project Intent

This repository is for a prototype demo recap intelligence system.

The prototype should prove the request in `docs/request.md`:

- Ask the demo team the recap category questions.
- Save the full answers into a small database.
- Allow internal users to search saved recaps by lead name, organization/name text, date, and demo lead.
- Send only sanitized, non-identifying recap sections to AI for simple trend summaries.

## Engineering Posture

Build this as a prototype with real GenAI system discipline at the boundaries that matter.

The right shape is production-shaped, not production-complete:

- Use real-system patterns where failure would be expensive: data boundaries, LLM payload construction, sanitization, prompt contracts, and traceability.
- Keep surrounding machinery simple: Streamlit, SQLite, direct functions, and clear data flow are enough.
- Do not add architecture just to make the prototype look larger.

The staff-level rule for this project:

```text
Prototype the riskiest contract honestly, and defer the surrounding machinery.
```

For this system, the riskiest contract is privacy: customer-identifiable information must not be sent to AI.

## Required Prototype Behavior

The prototype should save full recap information internally.

This includes:

- Organization name
- Lead name
- Contact names and emails
- Call date and time
- Demo lead
- Location
- User count
- First heard of GAT
- Competition
- Devices
- Budget
- Authority
- Timeline
- Details about organization
- Needs
- Demo discussion
- Questions and answers
- Requests during demo
- Follow up

Use full stored data for internal search and recap detail views.

Sanitize only when preparing data for AI. The boundary is:

```text
Store full data internally.
Send only sanitized analytical data to AI.
```

## AI Boundary Rules

No direct LLM call may access raw database rows or raw recap text.

Every AI call must go through an explicit AI-safe payload builder, such as:

```text
build_ai_safe_payload()
```

The AI-safe payload builder must:

- Select only approved analytical fields.
- Exclude organization name, lead name, contact names, contact emails, exact location, and raw full recap text.
- Redact known identifying values before sending.
- Produce a payload that can be previewed before the LLM call.

Minimum redaction rules:

- Replace email addresses with `[EMAIL]`.
- Replace URLs with `[URL]`.
- Replace the organization name with `[ORG]`.
- Replace known contact names with `[CONTACT]`.
- Replace exact location with `[LOCATION]`.

AI summaries should reference supporting demo IDs, not customer names.

## Include In Prototype

Use these real-system approaches even in the prototype:

- Full recap saved internally.
- AI receives only a separate sanitized payload.
- One enforced LLM input path through `build_ai_safe_payload()`.
- AI-safe preview before sending.
- Deterministic redaction for known fields.
- Supporting demo IDs in summaries.
- Optional storage of sanitized AI input if needed for debugging.

## Do Not Add Yet

Do not add these unless explicitly requested:

- RAG.
- Embeddings.
- Vector database.
- Autonomous agents.
- Complex permissions.
- NER or DLP services.
- Event pipelines.
- Normalized CRM schema.
- Multi-service backend.
- Prompt/version/eval framework.
- Production deployment infrastructure.

## Preferred Prototype Stack

Use:

- Python
- Streamlit
- SQLite
- `sqlite3`
- An OpenAI-compatible LLM client only for the summary step

Keep implementation direct. Separate functions are enough:

- `save_recap()`
- `search_recaps()`
- `sanitize_text()`
- `build_ai_safe_payload()`
- `summarize_with_llm()`

