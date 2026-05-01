from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any, Sequence

from .ai_payload import REDACTION_VERSION, build_ai_safe_payload
from .config import AppConfig, load_config
from .models import DemoContact, DemoRecap, SearchFilters, StoredAiPayload

RECAP_DB_FIELDS: tuple[str, ...] = (
    "organization_name",
    "lead_name",
    "demo_lead",
    "with_text",
    "call_datetime",
    "location",
    "user_count",
    "first_heard_of_gat",
    "competition",
    "devices",
    "budget",
    "authority",
    "timeline",
    "organization_details",
    "needs",
    "demo_discussion",
    "questions_answers",
    "requests_during_demo",
    "follow_up",
)
DISTINCT_FILTER_COLUMNS: frozenset[str] = frozenset({"lead_name", "organization_name", "demo_lead", "competition"})

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS demo_recaps (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    organization_name TEXT,
    lead_name TEXT,
    demo_lead TEXT,
    with_text TEXT,
    contacts_json TEXT DEFAULT '[]',
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

CREATE TABLE IF NOT EXISTS demo_recap_ai_payloads (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    recap_id INTEGER NOT NULL,
    payload_json TEXT NOT NULL,
    redaction_version TEXT DEFAULT 'v2',
    generated_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (recap_id) REFERENCES demo_recaps(id),
    UNIQUE (recap_id)
);
"""

INDEX_SQL = """
CREATE INDEX IF NOT EXISTS idx_demo_recaps_lead_name ON demo_recaps(lead_name);
CREATE INDEX IF NOT EXISTS idx_demo_recaps_organization_name ON demo_recaps(organization_name);
CREATE INDEX IF NOT EXISTS idx_demo_recaps_demo_lead ON demo_recaps(demo_lead);
CREATE INDEX IF NOT EXISTS idx_demo_recaps_call_datetime ON demo_recaps(call_datetime);
"""


def connect(db_path: Path | None = None) -> sqlite3.Connection:
    path = db_path or load_config().db_path
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(config: AppConfig | None = None) -> None:
    db_path = (config or load_config()).db_path
    conn = connect(db_path)
    try:
        conn.executescript(SCHEMA_SQL)
        _ensure_demo_recaps_columns(conn)
        conn.executescript(INDEX_SQL)
        conn.commit()
    finally:
        conn.close()


def _ensure_demo_recaps_columns(conn: sqlite3.Connection) -> None:
    columns = {str(row["name"]) for row in conn.execute("PRAGMA table_info(demo_recaps)").fetchall()}
    if "contacts_json" not in columns:
        conn.execute("ALTER TABLE demo_recaps ADD COLUMN contacts_json TEXT DEFAULT '[]'")
    if "demo_lead" not in columns:
        conn.execute("ALTER TABLE demo_recaps ADD COLUMN demo_lead TEXT DEFAULT ''")
    if "demo_owner" in columns:
        conn.execute(
            """
            UPDATE demo_recaps
            SET demo_lead = COALESCE(NULLIF(demo_owner, ''), demo_lead)
            WHERE demo_lead IS NULL OR demo_lead = ''
            """
        )


def _contacts_to_json(contacts: Sequence[DemoContact]) -> str:
    rows = [contact.to_dict() for contact in contacts if not contact.is_empty()]
    return json.dumps(rows, ensure_ascii=False, sort_keys=True)


def _contacts_from_json(raw_value: str | None) -> tuple[DemoContact, ...]:
    if not raw_value:
        return ()
    try:
        loaded = json.loads(raw_value)
    except json.JSONDecodeError:
        return ()
    if not isinstance(loaded, list):
        return ()
    contacts: list[DemoContact] = []
    for item in loaded:
        if not isinstance(item, dict):
            continue
        contact = DemoContact.from_mapping(item)
        if not contact.is_empty():
            contacts.append(contact)
    return tuple(contacts)


def recap_from_row(row: sqlite3.Row) -> DemoRecap:
    values = {field: row[field] or "" for field in RECAP_DB_FIELDS}
    contacts_json = row["contacts_json"] if "contacts_json" in row.keys() else "[]"
    return DemoRecap(
        id=int(row["id"]),
        contacts=_contacts_from_json(contacts_json),
        created_at=row["created_at"] or "",
        updated_at=row["updated_at"] or "",
        **values,
    )


def save_recap(conn: sqlite3.Connection, recap: DemoRecap) -> DemoRecap:
    """Save raw recap data and refresh the derived AI-safe payload atomically."""
    with conn:
        save_fields = (*RECAP_DB_FIELDS, "contacts_json")
        values = [getattr(recap, field) for field in RECAP_DB_FIELDS]
        values.append(_contacts_to_json(recap.contacts))
        if recap.id is None:
            columns_sql = ", ".join(save_fields)
            placeholders = ", ".join("?" for _ in save_fields)
            cursor = conn.execute(
                f"INSERT INTO demo_recaps ({columns_sql}) VALUES ({placeholders})",
                values,
            )
            saved = recap.with_id(int(cursor.lastrowid))
        else:
            set_sql = ", ".join(f"{field} = ?" for field in save_fields)
            conn.execute(
                f"UPDATE demo_recaps SET {set_sql}, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                [*values, recap.id],
            )
            saved = recap

        _upsert_ai_payload(conn, saved)
    fresh = get_recap(conn, saved.id)
    if fresh is None:
        raise RuntimeError(f"Saved recap {saved.id} could not be loaded.")
    return fresh


def _upsert_ai_payload(conn: sqlite3.Connection, recap: DemoRecap) -> None:
    payload = build_ai_safe_payload(recap)
    payload_json = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True)
    conn.execute(
        """
        INSERT INTO demo_recap_ai_payloads (recap_id, payload_json, redaction_version, generated_at)
        VALUES (?, ?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(recap_id) DO UPDATE SET
            payload_json = excluded.payload_json,
            redaction_version = excluded.redaction_version,
            generated_at = CURRENT_TIMESTAMP
        """,
        (recap.id, payload_json, REDACTION_VERSION),
    )


def build_current_ai_payload(recap: DemoRecap) -> StoredAiPayload:
    if recap.id is None:
        raise ValueError("Cannot build an AI-safe payload before the recap has a database ID.")
    return StoredAiPayload(
        recap_id=recap.id,
        payload=build_ai_safe_payload(recap),
        redaction_version=REDACTION_VERSION,
        generated_at="preview",
    )


def ai_payload_needs_refresh(stored: StoredAiPayload | None, current: StoredAiPayload) -> bool:
    return stored is None or stored.redaction_version != current.redaction_version or stored.payload != current.payload


def refresh_ai_payload(conn: sqlite3.Connection, recap: DemoRecap) -> StoredAiPayload:
    if recap.id is None:
        raise ValueError("Cannot refresh an AI-safe payload before the recap has a database ID.")
    with conn:
        _upsert_ai_payload(conn, recap)
    stored = get_ai_payload(conn, recap.id)
    if stored is None:
        raise RuntimeError(f"AI-safe payload for recap {recap.id} could not be loaded.")
    return stored


def preview_ai_payloads(conn: sqlite3.Connection, recaps: Sequence[DemoRecap]) -> tuple[list[StoredAiPayload], int, list[str]]:
    payloads: list[StoredAiPayload] = []
    stale_count = 0
    errors: list[str] = []
    for recap in recaps:
        try:
            current = build_current_ai_payload(recap)
            stored = get_ai_payload(conn, current.recap_id)
            if ai_payload_needs_refresh(stored, current):
                stale_count += 1
        except Exception as exc:
            errors.append(f"Recap #{recap.id or 'unsaved'}: {exc}")
            continue
        payloads.append(current)
    return payloads, stale_count, errors


def refresh_ai_payloads(conn: sqlite3.Connection, recaps: Sequence[DemoRecap]) -> tuple[list[StoredAiPayload], int, list[str]]:
    payloads: list[StoredAiPayload] = []
    refreshed_count = 0
    errors: list[str] = []
    for recap in recaps:
        try:
            current = build_current_ai_payload(recap)
            stored = get_ai_payload(conn, current.recap_id)
            if ai_payload_needs_refresh(stored, current):
                stored = refresh_ai_payload(conn, recap)
                refreshed_count += 1
        except Exception as exc:
            errors.append(f"Recap #{recap.id or 'unsaved'}: {exc}")
            continue
        payloads.append(stored or current)
    return payloads, refreshed_count, errors


def get_recap(conn: sqlite3.Connection, recap_id: int | None) -> DemoRecap | None:
    if recap_id is None:
        return None
    row = conn.execute("SELECT * FROM demo_recaps WHERE id = ?", (recap_id,)).fetchone()
    return recap_from_row(row) if row else None


def search_recaps(conn: sqlite3.Connection, filters: SearchFilters) -> list[DemoRecap]:
    sql = "SELECT * FROM demo_recaps"
    clauses: list[str] = []
    params: list[Any] = []

    def add_like(column_sql: str, value: str) -> None:
        if not value.strip():
            return
        clauses.append(f"LOWER({column_sql}) LIKE ?")
        params.append(f"%{value.casefold()}%")

    add_like("lead_name", filters.lead)
    add_like("demo_lead", filters.demo_lead)
    add_like("competition", filters.competition)

    if filters.org.strip():
        clauses.append("(LOWER(organization_name) LIKE ? OR LOWER(organization_details) LIKE ?)")
        pattern = f"%{filters.org.casefold()}%"
        params.extend([pattern, pattern])

    if filters.text.strip():
        pattern = f"%{filters.text.casefold()}%"
        clauses.append(
            "("
            "LOWER(needs) LIKE ? OR "
            "LOWER(questions_answers) LIKE ? OR "
            "LOWER(requests_during_demo) LIKE ? OR "
            "LOWER(follow_up) LIKE ?"
            ")"
        )
        params.extend([pattern, pattern, pattern, pattern])

    if filters.date_start.strip():
        clauses.append("date(call_datetime) >= date(?)")
        params.append(filters.date_start)
    if filters.date_end.strip():
        clauses.append("date(call_datetime) <= date(?)")
        params.append(filters.date_end)

    if clauses:
        sql += " WHERE " + " AND ".join(clauses)
    sql += " ORDER BY call_datetime DESC, id DESC"

    rows = conn.execute(sql, params).fetchall()
    return [recap_from_row(row) for row in rows]


def _list_distinct_text_values(conn: sqlite3.Connection, column: str) -> list[str]:
    if column not in DISTINCT_FILTER_COLUMNS:
        raise ValueError(f"Unsupported distinct text column: {column}")
    rows = conn.execute(
        f"""
        SELECT DISTINCT TRIM({column}) AS value
        FROM demo_recaps
        WHERE TRIM(COALESCE({column}, '')) != ''
        ORDER BY LOWER(TRIM({column})), TRIM({column})
        """
    ).fetchall()
    return [str(row["value"]) for row in rows]


def list_lead_names(conn: sqlite3.Connection) -> list[str]:
    return _list_distinct_text_values(conn, "lead_name")


def list_organization_names(conn: sqlite3.Connection) -> list[str]:
    return _list_distinct_text_values(conn, "organization_name")


def list_demo_leads(conn: sqlite3.Connection) -> list[str]:
    return _list_distinct_text_values(conn, "demo_lead")


def list_competitions(conn: sqlite3.Connection) -> list[str]:
    return _list_distinct_text_values(conn, "competition")


def get_ai_payload(conn: sqlite3.Connection, recap_id: int) -> StoredAiPayload | None:
    row = conn.execute(
        """
        SELECT recap_id, payload_json, redaction_version, generated_at
        FROM demo_recap_ai_payloads
        WHERE recap_id = ?
        """,
        (recap_id,),
    ).fetchone()
    if not row:
        return None
    return StoredAiPayload(
        recap_id=int(row["recap_id"]),
        payload=json.loads(row["payload_json"]),
        redaction_version=row["redaction_version"] or "",
        generated_at=row["generated_at"] or "",
    )


def reset_demo_tables(conn: sqlite3.Connection) -> None:
    with conn:
        conn.execute("DELETE FROM demo_recap_ai_payloads")
        conn.execute("DELETE FROM demo_recaps")
        conn.execute("DELETE FROM sqlite_sequence WHERE name IN ('demo_recaps', 'demo_recap_ai_payloads')")


def print_search_results(recaps: Sequence[DemoRecap]) -> str:
    if not recaps:
        return "No matching recaps."
    lines = ["id | call_datetime | organization | lead | demo_lead | user_count | timeline"]
    lines.append("-" * 96)
    for recap in recaps:
        lines.append(
            f"{recap.id} | {recap.call_datetime} | {recap.organization_name} | "
            f"{recap.lead_name} | {recap.demo_lead} | {recap.user_count} | {recap.timeline}"
        )
    return "\n".join(lines)
