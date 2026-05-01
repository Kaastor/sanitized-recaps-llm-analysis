from __future__ import annotations

import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path

from demo_recap.config import AppConfig
from demo_recap.db import (
    connect,
    init_db,
    list_competitions,
    list_demo_leads,
    list_lead_names,
    list_organization_names,
    search_recaps,
)
from demo_recap.models import SearchFilters


class DemoLeadMigrationTest(unittest.TestCase):
    def test_init_db_carries_legacy_demo_owner_values_into_demo_lead(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            db_path = Path(tmp_dir) / "legacy.sqlite"
            raw_conn = sqlite3.connect(db_path)
            try:
                raw_conn.executescript(
                    """
                    CREATE TABLE demo_recaps (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        organization_name TEXT,
                        lead_name TEXT,
                        demo_owner TEXT,
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
                    INSERT INTO demo_recaps (
                        organization_name,
                        lead_name,
                        demo_owner,
                        call_datetime,
                        location
                    )
                    VALUES (
                        'Acme School',
                        'Pat Lead',
                        'Ava Chen',
                        '2026-04-30 10:00',
                        'Boston, MA'
                    );
                    """
                )
                raw_conn.commit()
            finally:
                raw_conn.close()

            config = AppConfig(db_path=db_path, groq_api_key="", groq_model="test-model")
            init_db(config)

            with closing(connect(db_path)) as conn:
                recaps = search_recaps(conn, SearchFilters(demo_lead="Ava Chen"))

        self.assertEqual(len(recaps), 1)
        self.assertEqual(recaps[0].demo_lead, "Ava Chen")

    def test_list_demo_leads_returns_distinct_saved_values(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            config = AppConfig(db_path=Path(tmp_dir) / "recaps.sqlite", groq_api_key="", groq_model="test-model")
            init_db(config)
            with closing(connect(config.db_path)) as conn:
                conn.executemany(
                    "INSERT INTO demo_recaps (demo_lead) VALUES (?)",
                    [("June Park",), ("Ava Chen",), ("June Park",), ("",), ("  Miles Carter  ",), (None,)],
                )
                conn.commit()

                demo_leads = list_demo_leads(conn)

        self.assertEqual(demo_leads, ["Ava Chen", "June Park", "Miles Carter"])

    def test_list_find_filter_values_return_distinct_saved_values(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            config = AppConfig(db_path=Path(tmp_dir) / "recaps.sqlite", groq_api_key="", groq_model="test-model")
            init_db(config)
            with closing(connect(config.db_path)) as conn:
                conn.executemany(
                    """
                    INSERT INTO demo_recaps (lead_name, organization_name, demo_lead, competition)
                    VALUES (?, ?, ?, ?)
                    """,
                    [
                        ("Pat Lead", "Acme School", "June Park", "BetterCloud"),
                        ("Riley Stone", "Brighton District", "Ava Chen", "CloudM"),
                        ("Pat Lead", "Acme School", "June Park", "BetterCloud"),
                        ("  Alex Morgan  ", "  Cedar Trust  ", "Miles Carter", "  GAM  "),
                        ("", "", "", ""),
                        (None, None, None, None),
                    ],
                )
                conn.commit()

                lead_names = list_lead_names(conn)
                organization_names = list_organization_names(conn)
                demo_leads = list_demo_leads(conn)
                competitions = list_competitions(conn)

        self.assertEqual(lead_names, ["Alex Morgan", "Pat Lead", "Riley Stone"])
        self.assertEqual(organization_names, ["Acme School", "Brighton District", "Cedar Trust"])
        self.assertEqual(demo_leads, ["Ava Chen", "June Park", "Miles Carter"])
        self.assertEqual(competitions, ["BetterCloud", "CloudM", "GAM"])


if __name__ == "__main__":
    unittest.main()
