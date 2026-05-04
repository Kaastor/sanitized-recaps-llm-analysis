from __future__ import annotations

from contextlib import closing

import streamlit as st

from demo_recap.config import load_config
from demo_recap.db import connect, init_db
from demo_recap.ui_pages import render_ai_summary_tab, render_new_recap_tab, render_search_tab, render_sidebar
from demo_recap.ui_style import render_global_styles


def main() -> None:
    st.set_page_config(page_title="Demo Insights", page_icon="🛡️", layout="wide", initial_sidebar_state="expanded")
    render_global_styles()
    selected_page = render_sidebar()

    config = load_config()
    init_db(config)

    with closing(connect(config.db_path)) as conn:
        if selected_page == "add":
            render_new_recap_tab(conn)
        elif selected_page == "search":
            render_search_tab(conn)
        else:
            render_ai_summary_tab(conn)


if __name__ == "__main__":
    main()
