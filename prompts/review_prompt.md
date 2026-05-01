# Review Prompt

You are a senior/staff coding agent. Your task is to review multiple candidate implementations of the same prototype, compare them against the project specification, choose the best implementation, and decide whether merging pieces from multiple candidates is better than taking one winner as-is.

This review may be run from inside the original spec repository. That repository may also be one of the candidate implementations if it now contains an implemented app.

## Inputs

You will be given:

- The original project/spec repository path.
- One or more candidate implementation repository paths.

Fill in the paths before running the review:

```text
SPEC_REPO=/home/przemek/Nauka/demo-intelligence-capture-system/
CANDIDATE_LOCAL=/home/przemek/Nauka/demo-intelligence-capture-system/demo_recap
CANDIDATE_A=/home/przemek/Downloads/demo_inteligence_apps/demo_recap_privacy_app
CANDIDATE_B=/home/przemek/Downloads/demo_inteligence_apps/demo_recap_privacy_app_2
CANDIDATE_C=/home/przemek/Downloads/demo_inteligence_apps/demo_recap_privacy_prototype_3
CANDIDATE_D=/home/przemek/Downloads/demo_inteligence_apps/demo_recap_privacy_prototype_4
CANDIDATE_E=/home/przemek/Downloads/demo_inteligence_apps/demo_recap_privacy_ap_5
```

Add or remove candidate paths as needed. If the current repository is not an implementation candidate, omit `CANDIDATE_LOCAL`. If `SPEC_REPO` and a candidate path are the same path, read the spec from that path first, then evaluate the application code in the same working tree.

The source specification is:

```text
$SPEC_REPO/docs/description.md
```

This is a review task. Do not edit candidate repositories unless the user explicitly asks for fixes. Running local verification commands is allowed. Avoid destructive cleanup commands.

If a candidate has uncommitted changes, review the working tree as-is and mention that in the verification log.

## Review Goal

Produce a concise but rigorous comparison that answers:

1. Which candidate best satisfies the spec?
2. Why is it the winner?
3. What are the important defects or risks in each candidate?
4. Should we use the winner as-is, or merge selected parts from other candidates?
5. If merging is recommended, exactly what should be merged and why?
6. What verification commands were run, and what passed/failed?

## Hard Requirements To Check

Each implementation must be checked against these non-negotiable requirements:

- Full raw recap data is stored internally.
- The full `WITH` answer is preserved exactly as submitted.
- Organization name, lead name, and demo lead are explicit metadata fields and are not inferred from `WITH`.
- SQLite is used through `sqlite3`.
- Streamlit UI exists with the required flows:
  - create recap
  - search recaps
  - view/edit recap detail
  - view per-recap sanitized AI-safe payload
  - run AI trend summary from sanitized payloads
- Two conceptual tables exist:
  - `demo_recaps`
  - `demo_recap_ai_payloads`
- `demo_recaps` is the internal source of truth.
- `demo_recap_ai_payloads` stores a derived AI-safe payload.
- Saving/editing a recap regenerates the sanitized payload.
- AI summaries read from `demo_recap_ai_payloads`, not raw recap rows.
- Direct LLM calls never receive raw recap rows, raw full recap text, organization names, lead names, contact names, contact emails, or exact locations.
- Sanitization is deterministic and not a dummy placeholder.
- Sanitization redacts:
  - emails to `[EMAIL]`
  - URLs to `[URL]`
  - organization name to `[ORG]`
  - lead name to `[LEAD]`
  - known contact names to `[CONTACT]`
  - exact location to `[LOCATION]`
- Known contact names are extracted deterministically from `with_text` using simple parsing.
- The OpenAI/OpenAI-compatible client is isolated behind a small adapter abstraction.
- A dry-run/no-LLM path exists.
- A thin CLI exists for verification.
- Meaningful synthetic demo data exists.
- No RAG, embeddings, vector database, autonomous agents, complex permissions, event pipelines, production deployment infrastructure, or invented architecture.
- No test suite was added unless the original prompt was explicitly changed.

## Staff-Level Quality Criteria

Assess implementation quality, not just feature presence:

- Clear, cohesive module boundaries.
- Small, readable files.
- Strong Python typing where useful.
- Direct, boring implementation over speculative architecture.
- No fake abstractions or pass-through layers.
- No raw DB rows leaking into AI prompt construction.
- Privacy boundary is obvious in code.
- `build_ai_safe_payload()` or equivalent is the enforced AI-safe boundary.
- Saving raw recap and upserting sanitized payload is one clear operation.
- Search code is understandable and not overbuilt.
- Streamlit UI is usable, pleasant, and not overcomplicated.
- CLI is thin and useful for verification.
- Synthetic data is realistic enough for demo.
- README instructions are accurate.

## Suggested Review Procedure

For each candidate:

1. Inspect repository structure.
2. Read README and dependency file.
3. Locate core modules:
   - DB/schema
   - models/types
   - save/edit service
   - sanitization
   - AI payload builder
   - summarization/LLM adapter
   - CLI
   - Streamlit UI
   - sample data
4. Run static text checks for risk:
   - Search for direct OpenAI imports outside adapter modules.
   - Search for LLM calls that use raw recap records.
   - Search for `demo_recaps` usage in summary generation.
   - Search for sanitization placeholders or TODOs.
   - Search for unrelated architecture: embeddings, vector, agent, auth, permissions, background jobs.
5. Install dependencies if feasible.
6. Run CLI verification commands.
7. Start or smoke-check the Streamlit app if feasible.
8. Inspect generated sanitized payloads to verify redaction.
9. Compare code quality and maintainability.

Use commands equivalent to these, adjusted for each repository's actual README/CLI entrypoint:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
<cli command> init-db
<cli command> seed-demo-data
<cli command> search --lead "Diana"
<cli command> preview-ai-payload --recap-id 1
<cli command> summarize --analysis popular_requests --dry-run
```

If commands differ, note the difference and whether it is justified. Do not penalize a candidate for choosing a different package/module name if the CLI is clear, documented, and equivalent.

## Privacy Boundary Review

This is the most important part of the review.

For each candidate, answer:

- Where is the AI-safe payload built?
- Is there exactly one enforced path for LLM input?
- Does the builder select only allowed analytical fields?
- Does it exclude identity fields?
- Does it redact deterministic known values?
- Does the summary path read stored sanitized payloads?
- Can raw recap rows accidentally reach the LLM adapter?
- Does the CLI dry-run show the exact sanitized LLM input?
- Does sample seeded data prove redaction works?

If a candidate fails the privacy boundary, it should not win unless all candidates fail and it is still easiest to fix.

## Merge Decision Guidance

Prefer one winner as the base unless there is a clear reason to merge.

Recommend merging only when:

- The winning candidate is clearly best overall but has a localized weakness.
- Another candidate has a strictly better isolated component.
- The component can be copied or adapted without pulling in a worse architecture.
- The merge reduces risk or improves clarity without expanding scope.

Do not recommend merging just to average candidates. Avoid combining incompatible architectures.

Examples of reasonable merge candidates:

- Better sanitization implementation.
- Cleaner CLI.
- Better sample data.
- Better README.
- Small UI polish that does not change architecture.

Examples of poor merge candidates:

- Importing a whole service/repository framework.
- Adding a status workflow not required by the spec.
- Adding auth, permissions, embeddings, vector storage, agents, or background jobs.
- Replacing a clear direct implementation with generic abstractions.

## Required Output Format

Write the review as:

```markdown
# Implementation Comparison

## Summary

- Winner: `<candidate path/name>`
- Recommendation: `use as-is` / `use as base with targeted merges` / `no acceptable winner`
- Reason in 3-5 sentences.

## Scorecard

| Area | Candidate Local | Candidate A | Candidate B | Candidate C |
|---|---:|---:|---:|
| Spec completeness |  |  |  |
| Privacy boundary |  |  |  |
| Sanitization quality |  |  |  |
| Data model correctness |  |  |  |
| LLM adapter design |  |  |  |
| CLI verification |  |  |  |
| UI usability |  |  |  |
| Synthetic data |  |  |  |
| Code clarity |  |  |  |
| Scope control |  |  |  |
```

Use a simple 1-5 score or `pass/warn/fail`, but explain material differences below. Do not let numeric scores hide serious privacy failures.

```markdown
## Findings By Candidate

### Candidate Local: `<path>`

- Strengths:
- Defects:
- Privacy risks:
- Verification:

### Candidate A: `<path>`

- Strengths:
- Defects:
- Privacy risks:
- Verification:
```

Add, remove, or rename candidate sections as needed to match the actual paths reviewed.

```markdown
## Winner Rationale

Explain why the winner is the best base. Be specific about privacy, simplicity, and maintainability.

## Merge Recommendation

State whether merging is recommended.

If yes, list exact files/components to port and why.

If no, explain why the winner should be used as-is or fixed directly.

## Verification Log

List commands run for each candidate and the result.

## Residual Risks

List any issues that should be fixed before demo or before extending the prototype.
```

## Review Standard

Be direct. Prioritize correctness, privacy, and implementation clarity over surface polish.

Do not reward invented complexity. Do not penalize simple code that honestly satisfies the spec.

The best candidate is the one that proves the risky contract cleanly:

```text
Store full data internally.
Generate a deterministic sanitized derived payload.
Summarize only from stored sanitized payloads.
Never send identifying/raw recap data to AI.
```
