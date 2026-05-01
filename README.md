# Demo Insights

A small Streamlit + SQLite prototype for internal demo recaps with a strict privacy boundary for AI summaries.

The app stores full raw recaps internally in `demo_recaps`, including the exact submitted `WITH` answer and structured attendee rows. Every create/update also regenerates a derived sanitized payload in `demo_recap_ai_payloads`. AI trend summaries read from those stored sanitized payloads only.

## What is included

- Streamlit app with three tabs:
  - `Add Recap`
  - `Find Recaps`
  - `Summarize Trends`
- SQLite schema using `sqlite3` directly.
- Thin CLI verification surface.
- Deterministic sanitization for:
  - emails -> `[EMAIL]`
  - URLs -> `[URL]`
  - organization names -> `[ORG]`
  - lead names -> `[LEAD]`
  - structured contact names and deterministic raw `WITH` attendee candidates -> `[CONTACT]`
  - exact locations -> `[LOCATION]`
- Groq provider adapter isolated behind `summarize_with_llm(stored_payloads, analysis_type)`.
- Missing or failed API calls are shown as explicit errors.
- Six realistic synthetic, fake demo recaps.

## Project layout

```text
.
├── app.py                         # Streamlit entrypoint
├── demo_recap/
│   ├── ai_payload.py              # AI-safe payload selection + validation
│   ├── cli.py                     # argparse CLI
│   ├── config.py                  # repo-local .env + environment config
│   ├── db.py                      # sqlite3 schema, search, save lifecycle
│   ├── llm.py                     # Safe LLM boundary and Groq adapter
│   ├── models.py                  # typed dataclasses and analysis types
│   ├── sanitization.py            # deterministic privacy redaction
│   └── seed_data.py               # synthetic demo recaps
├── requirements.txt
└── .env.example
```

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

On Windows PowerShell, activate with:

```powershell
.venv\Scripts\Activate.ps1
```

## Configuration

Copy the example file if you want local configuration:

```bash
cp .env.example .env
```

Supported keys:

```bash
DEMO_RECAP_DB_PATH=
GROQ_API_KEY=
GROQ_MODEL=llama-3.3-70b-versatile
```

When `.env` is present, non-empty values from the repo-local `.env` file are used first. Empty or missing keys fall back to process environment variables. `GROQ_API_KEY` is required for AI summaries; missing keys or API failures are surfaced as errors.

## Initialize and seed the database

```bash
python -m demo_recap.cli init-db
python -m demo_recap.cli seed-demo-data
```

`seed-demo-data` replaces existing demo rows by default so the demo IDs are deterministic. Use `--append` to add another copy instead.

## Run the Streamlit app

```bash
streamlit run app.py
```

## CLI verification commands

These commands validate the main behavior without using the UI:

```bash
python -m demo_recap.cli init-db
python -m demo_recap.cli seed-demo-data
python -m demo_recap.cli search --lead "Diana"
python -m demo_recap.cli preview-ai-payload --recap-id 1
```

Expected verification results:

- `search --lead "Diana"` prints recap `1` with key search metadata.
- `preview-ai-payload --recap-id 1` prints JSON containing only allowed AI payload fields.
- The payload preview shows redaction placeholders such as `[EMAIL]`, `[URL]`, `[ORG]`, `[LEAD]`, `[CONTACT]`, and `[LOCATION]`.
- The UI `Summarize Trends` tab shows AI-safe status and optional readable safe-copy previews before generating a summary.

## Optional live LLM summary

Set an API key in `.env` or in the environment:

```bash
GROQ_API_KEY=your_key_here
GROQ_MODEL=llama-3.3-70b-versatile
```

Then run:

```bash
python -m demo_recap.cli summarize --analysis popular_requests
```

The public LLM boundary accepts stored sanitized payloads and an analysis type. Raw recap rows and arbitrary prompt strings are not passed from the app or CLI into the provider adapter.

## Privacy boundary notes

`demo_recaps` is the internal source of truth. `demo_recap_ai_payloads` is a derived analytical view. Do not edit `payload_json` directly. If a payload preview looks unsafe, edit the raw recap, structured contact rows, raw `WITH` attendees, or explicit metadata and save again; `save_recap()` refreshes the stored sanitized payload inside the same SQLite transaction. Trend summaries preview current safe copies without writing, then refresh stale stored payloads immediately before the LLM call.

The stored AI payload contains only:

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

No organization name, lead name, structured contacts, `WITH` answer, contact email, contact name, exact location, or full raw recap text is included in the AI payload.
