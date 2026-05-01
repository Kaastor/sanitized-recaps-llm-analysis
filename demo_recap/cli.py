from __future__ import annotations

import argparse
import json
import sys
from contextlib import closing
from dataclasses import replace
from pathlib import Path

from .config import load_config
from .db import (
    connect,
    get_ai_payload,
    init_db,
    print_search_results,
    refresh_ai_payloads,
    search_recaps,
)
from .llm import summarize_with_llm
from .models import ANALYSIS_TYPES, SearchFilters
from .seed_data import seed_demo_data
from .summarization import assert_valid_analysis_type


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Demo recap privacy-boundary prototype CLI")
    parser.add_argument("--db-path", help="Optional SQLite database path override.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("init-db", help="Create the SQLite schema.")

    seed_parser = subparsers.add_parser("seed-demo-data", help="Insert deterministic synthetic demo recaps.")
    seed_parser.add_argument(
        "--append",
        action="store_true",
        help="Append demo data instead of replacing existing recaps. Default replaces data for deterministic IDs.",
    )

    search_parser = subparsers.add_parser("search", help="Search saved recaps.")
    search_parser.add_argument("--lead", default="", help="Lead-name substring.")
    search_parser.add_argument("--org", default="", help="Organization/name-text substring.")
    search_parser.add_argument("--demo-lead", default="", help="Demo-lead substring.")
    search_parser.add_argument("--text", default="", help="Text across needs, questions, requests, and follow-up.")

    preview_parser = subparsers.add_parser("preview-ai-payload", help="Print one stored sanitized AI payload.")
    preview_parser.add_argument("--recap-id", type=int, required=True, help="Recap ID to preview.")

    summarize_parser = subparsers.add_parser("summarize", help="Build a sanitized trend-summary input and call the LLM.")
    summarize_parser.add_argument("--analysis", choices=ANALYSIS_TYPES, required=True, help="Analysis type.")
    summarize_parser.add_argument("--lead", default="", help="Optional lead filter.")
    summarize_parser.add_argument("--org", default="", help="Optional organization/name-text filter.")
    summarize_parser.add_argument("--demo-lead", default="", help="Optional demo-lead filter.")
    summarize_parser.add_argument("--text", default="", help="Optional text filter.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    config = load_config()
    if args.db_path:
        path = Path(args.db_path).expanduser()
        if not path.is_absolute():
            path = Path.cwd() / path
        config = replace(config, db_path=path)

    if args.command == "init-db":
        init_db(config)
        print(f"Initialized SQLite database at {config.db_path}")
        return 0

    init_db(config)
    with closing(connect(config.db_path)) as conn:
        if args.command == "seed-demo-data":
            recaps = seed_demo_data(conn, reset=not args.append)
            print(f"Seeded {len(recaps)} synthetic recaps into {config.db_path}")
            print("Recap IDs: " + ", ".join(str(recap.id) for recap in recaps))
            return 0

        if args.command == "search":
            filters = SearchFilters(lead=args.lead, org=args.org, demo_lead=args.demo_lead, text=args.text)
            print(print_search_results(search_recaps(conn, filters)))
            return 0

        if args.command == "preview-ai-payload":
            stored = get_ai_payload(conn, args.recap_id)
            if stored is None:
                parser.error(f"No stored AI payload found for recap ID {args.recap_id}")
            print(json.dumps(stored.payload, ensure_ascii=False, indent=2, sort_keys=True))
            return 0

        if args.command == "summarize":
            analysis_type = assert_valid_analysis_type(args.analysis)
            filters = SearchFilters(lead=args.lead, org=args.org, demo_lead=args.demo_lead, text=args.text)
            recaps = search_recaps(conn, filters)
            payloads, _refreshed_count, payload_errors = refresh_ai_payloads(conn, recaps)
            if payload_errors:
                for error in payload_errors:
                    print(f"AI payload failed: {error}", file=sys.stderr)
                return 1

            try:
                print(summarize_with_llm(payloads, analysis_type, config=config))
            except Exception as exc:
                print(f"AI summary failed: {exc}", file=sys.stderr)
                return 1
            return 0

    parser.error(f"Unhandled command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
