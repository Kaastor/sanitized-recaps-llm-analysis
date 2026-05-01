from __future__ import annotations

from html import escape

import streamlit as st

ICON_GLYPHS: dict[str, str] = {
    "article": "▤",
    "calendar_month": "□",
    "chat": "☰",
    "check": "✓",
    "event": "□",
    "fingerprint": "◎",
    "groups": "◌",
    "help": "?",
    "insights": "↗",
    "notes": "▤",
    "redeem": "□",
    "send": "↗",
    "target": "◎",
    "verified_user": "✓",
}


def material_symbol(name: str) -> str:
    return f'<span class="icon-glyph" aria-hidden="true">{escape(ICON_GLYPHS.get(name, "•"))}</span>'


def render_global_styles() -> None:
    st.markdown(
        """
        <style>
        :root {
            --ink: #2e1f18;
            --muted: #776d67;
            --warm: #e4572e;
            --warm-dark: #c83f1b;
            --sage: #7f8c62;
            --shadow: 0 18px 45px rgba(69, 42, 25, 0.09);
        }

        .stApp, [data-testid="stAppViewContainer"] {
            background:
                radial-gradient(circle at 80% 10%, rgba(242, 199, 168, 0.24), transparent 28rem),
                linear-gradient(135deg, #fffdfb 0%, #fbf7f3 42%, #fffaf4 100%);
            color: var(--ink);
        }

        [data-testid="stHeader"] {
            background: transparent;
        }

        [data-testid="stToolbar"],
        [data-testid="stDecoration"],
        #MainMenu {
            display: none !important;
        }

        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, #fffaf6 0%, #f8efe7 100%);
            border-right: 1px solid #eadfd8;
            box-shadow: 12px 0 30px rgba(69, 42, 25, 0.06);
        }

        [data-testid="stSidebar"] [data-testid="stSidebarContent"] {
            padding: 2rem 1rem 1.25rem;
        }

        .block-container {
            max-width: none;
            padding-top: 1.65rem;
            padding-left: clamp(1rem, 2.4vw, 2.5rem);
            padding-right: clamp(1rem, 2.4vw, 2.5rem);
            padding-bottom: 2.5rem;
        }

        .icon-glyph {
            font-family: ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
            font-weight: 800;
            font-size: 1rem;
            line-height: 1;
            display: inline-block;
            letter-spacing: normal;
            text-align: center;
        }

        .brand-lockup {
            display: flex;
            align-items: center;
            gap: 0.7rem;
            margin: 1.25rem 0 2.2rem;
            padding: 0 0.35rem;
        }

        .brand-mark {
            width: 2.45rem;
            height: 2.45rem;
            display: grid;
            place-items: center;
            border-radius: 50%;
            color: #ffffff;
            background: linear-gradient(135deg, #e9683b, #cc4f2b);
        }

        .brand-mark .icon-glyph {
            font-size: 1.2rem;
        }

        .brand-name {
            font-family: Georgia, 'Times New Roman', serif;
            font-weight: 700;
            font-size: 1.08rem;
            line-height: 1.04;
            color: var(--ink);
        }

        [data-testid="stSidebar"] [role="radiogroup"] {
            display: grid;
            gap: 0.55rem;
        }

        [data-testid="stSidebar"] [role="radiogroup"] label {
            min-height: 3.1rem;
            padding: 0.5rem 0.8rem;
            border-radius: 8px;
            color: #443730;
            border: 1px solid transparent;
        }

        [data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) {
            background: #feece3;
            border-color: #f8d5c6;
            color: var(--warm-dark);
            box-shadow: 0 8px 20px rgba(228, 87, 46, 0.08);
        }

        [data-testid="stSidebar"] [role="radiogroup"] label > div:first-child {
            display: none;
        }

        .privacy-banner {
            display: grid;
            grid-template-columns: auto minmax(0, 1fr) 9rem;
            align-items: center;
            gap: 1.2rem;
            margin-bottom: 1rem;
            padding: 1.05rem 1.25rem;
            border: 1px solid #facdbb;
            border-radius: 8px;
            background:
                linear-gradient(90deg, rgba(255,255,255,0.84), rgba(255,246,240,0.96)),
                radial-gradient(circle at 100% 0%, rgba(228, 87, 46, 0.14), transparent 14rem);
            box-shadow: 0 8px 28px rgba(93, 55, 32, 0.06);
        }

        .privacy-emblem {
            width: 3.25rem;
            height: 3.25rem;
            display: grid;
            place-items: center;
            border-radius: 50%;
            color: var(--warm);
            background: #ffe5d8;
            border: 1px solid #ffd2c0;
        }

        .privacy-emblem .icon-glyph {
            font-size: 1.35rem;
        }

        .privacy-title {
            font-weight: 700;
            color: var(--ink);
            margin-bottom: 0.25rem;
        }

        .privacy-text {
            color: #4d403a;
            font-size: 0.92rem;
            line-height: 1.55;
        }

        .privacy-doc {
            justify-self: end;
            width: 5.9rem;
            height: 4.9rem;
            border: 1px solid #f2cfbd;
            border-radius: 8px;
            background: #ffffff;
            position: relative;
            box-shadow: 0 10px 24px rgba(82, 45, 26, 0.12);
        }

        .doc-lines {
            display: grid;
            gap: 0.45rem;
            padding: 1rem 0.85rem;
        }

        .doc-lines span {
            height: 0.24rem;
            border-radius: 999px;
            background: #ebd1c2;
        }

        .doc-lines span:nth-child(2) {
            width: 72%;
        }

        .doc-lines span:nth-child(3) {
            width: 86%;
        }

        .doc-badge {
            position: absolute;
            right: -0.85rem;
            bottom: -0.7rem;
            width: 2.6rem;
            height: 2.6rem;
            display: grid;
            place-items: center;
            border-radius: 50%;
            color: #ffffff;
            background: linear-gradient(135deg, #ef774b, #d94a25);
            border: 3px solid #fff7f2;
        }

        [data-testid="stVerticalBlockBorderWrapper"] {
            border-color: rgba(224, 205, 194, 0.86) !important;
            border-radius: 8px !important;
            background: rgba(255, 255, 255, 0.84) !important;
            box-shadow: var(--shadow);
        }

        .section-heading {
            display: flex;
            align-items: center;
            gap: 0.72rem;
            margin-bottom: 0.9rem;
        }

        .section-icon {
            width: 2.15rem;
            height: 2.15rem;
            display: grid;
            place-items: center;
            border-radius: 50%;
            background: #f2f4e8;
            color: var(--sage);
            border: 1px solid #e3e8d1;
        }

        .section-title, .rail-title {
            font-family: Georgia, 'Times New Roman', serif;
            font-size: 1.18rem;
            font-weight: 700;
            color: var(--ink);
            line-height: 1.2;
        }

        .section-subtitle {
            margin-top: 0.12rem;
            color: var(--muted);
            font-size: 0.84rem;
        }

        [data-testid="stTextInput"] input,
        [data-testid="stDateInput"] input,
        [data-testid="stTextArea"] textarea,
        [data-baseweb="select"] > div {
            background: #ffffff !important;
            border: 1px solid #e2d4cd !important;
            border-radius: 8px !important;
            min-height: 2.5rem;
            box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.75);
        }

        [data-testid="stTextInput"] label p,
        [data-testid="stDateInput"] label p,
        [data-testid="stSelectbox"] label p {
            color: #3f342e;
            font-size: 0.875rem;
            line-height: 1.35;
        }

        [data-testid="stTextInput"] input:focus,
        [data-testid="stDateInput"] input:focus,
        [data-testid="stTextArea"] textarea:focus {
            border-color: var(--warm) !important;
            box-shadow: 0 0 0 1px var(--warm), 0 1px 2px rgba(15, 23, 42, 0.06) !important;
        }

        [data-testid="stExpander"] details {
            background: rgba(255, 255, 255, 0.92);
            border: 1px solid #eadfd8;
            border-radius: 8px;
            box-shadow: 0 4px 16px rgba(69, 42, 25, 0.04);
        }

        [data-testid="stExpander"] summary {
            font-weight: 700;
            color: var(--ink);
        }

        [data-testid="stMain"] [data-testid="stRadio"] [role="radiogroup"] {
            display: grid;
            gap: 0.45rem;
        }

        [data-testid="stMain"] [data-testid="stRadio"] [role="radiogroup"] label {
            width: 100%;
            min-height: 2.75rem;
            padding: 0.48rem 0.75rem;
            border: 1px solid #eadfd8;
            border-radius: 8px;
            background: rgba(255, 255, 255, 0.86);
            box-shadow: 0 5px 14px rgba(69, 42, 25, 0.04);
        }

        [data-testid="stMain"] [data-testid="stRadio"] [role="radiogroup"] label:hover {
            border-color: #f0c8b7;
            background: #fff8f4;
        }

        [data-testid="stMain"] [data-testid="stRadio"] [role="radiogroup"] label:has(input:checked) {
            border-color: #e4572e;
            background: #fff1ea;
            box-shadow: inset 3px 0 0 #e4572e, 0 8px 18px rgba(228, 87, 46, 0.08);
        }

        [data-testid="stMain"] [data-testid="stRadio"] [role="radiogroup"] label > div:first-child {
            display: none;
        }

        [data-testid="stMain"] [data-testid="stRadio"] [role="radiogroup"] label > div:last-child {
            display: flex;
            flex: 1 1 auto;
            align-items: baseline;
            gap: 0.55rem;
            width: 100%;
            min-width: 0;
        }

        [data-testid="stMain"] [data-testid="stRadio"] [role="radiogroup"] label > div:last-child > div {
            min-width: 0;
        }

        [data-testid="stMain"] [data-testid="stRadio"] [role="radiogroup"] label > div:last-child > [data-testid="stMarkdownContainer"] {
            flex: 0 1 auto;
            max-width: min(20rem, 42%);
        }

        [data-testid="stMain"] [data-testid="stRadio"] [role="radiogroup"] label > div:last-child > [data-testid="stCaptionContainer"] {
            flex: 1 1 auto;
        }

        [data-testid="stMain"] [data-testid="stRadio"] [role="radiogroup"] label > div:last-child p {
            margin: 0;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }

        [data-testid="stMain"] [data-testid="stRadio"] [role="radiogroup"] label > div:last-child > [data-testid="stMarkdownContainer"] p {
            color: #2f2824;
            font-size: 0.92rem;
            line-height: 1.25;
        }

        [data-testid="stMain"] [data-testid="stRadio"] [role="radiogroup"] label > div:last-child > [data-testid="stCaptionContainer"] p {
            color: var(--muted);
            font-size: 0.78rem !important;
            line-height: 1.25;
        }

        .summary-result-row {
            margin: 0 0 0.55rem;
            padding: 0.72rem 0.85rem;
            border: 1px solid #eadfd8;
            border-radius: 8px;
            background: rgba(255, 255, 255, 0.88);
            box-shadow: 0 5px 14px rgba(69, 42, 25, 0.04);
        }

        .summary-result-title {
            color: #2f2824;
            font-size: 0.94rem;
            font-weight: 700;
            line-height: 1.25;
            margin-bottom: 0.16rem;
        }

        .summary-result-meta,
        .summary-result-context,
        .summary-result-excerpt {
            color: var(--muted);
            font-size: 0.78rem;
            line-height: 1.35;
        }

        .summary-result-context {
            margin-top: 0.2rem;
            color: #5f554f;
        }

        .summary-result-excerpt {
            margin-top: 0.24rem;
            color: #3d332e;
        }

        [data-testid="stAlert"] {
            border-radius: 8px;
        }

        .stButton > button {
            border-radius: 8px;
            border: 1px solid #e5cfc2;
            box-shadow: 0 1px 2px rgba(15, 23, 42, 0.05);
            min-height: 2.75rem;
        }

        .stButton > button[kind="primary"] {
            background: linear-gradient(135deg, var(--warm), #db4b25);
            border-color: #d44d28;
            color: #ffffff;
            font-weight: 700;
            box-shadow: 0 12px 24px rgba(217, 74, 37, 0.2);
        }

        .rail-heading {
            display: flex;
            align-items: flex-start;
            gap: 0.82rem;
            margin-bottom: 0.95rem;
        }

        .rail-icon {
            width: 1.8rem;
            height: 1.8rem;
            display: grid;
            place-items: center;
            color: #ffffff;
            background: var(--warm);
            border-radius: 8px;
        }

        .rail-pill {
            display: inline-block;
            margin-top: 0.65rem;
            padding: 0.35rem 0.7rem;
            border-radius: 8px;
            color: #3f4b2f;
            background: #eff3e3;
            border: 1px solid #dfe7cc;
            font-size: 0.8rem;
            font-weight: 600;
        }

        .safe-preview-card {
            display: flex;
            gap: 0.8rem;
            padding: 0.82rem 0.9rem;
            margin: 0 0 0.55rem;
            border: 1px solid #eadfd8;
            border-radius: 8px;
            background: rgba(255, 255, 255, 0.88);
            box-shadow: 0 7px 18px rgba(69, 42, 25, 0.05);
        }

        .safe-preview-card.is-empty {
            background: rgba(250, 247, 244, 0.75);
        }

        .safe-preview-icon {
            flex: 0 0 auto;
            color: #77716e;
            margin-top: 0.05rem;
        }

        .safe-preview-copy {
            min-width: 0;
        }

        .safe-preview-label {
            font-size: 0.82rem;
            font-weight: 700;
            color: #2f2824;
            margin-bottom: 0.15rem;
        }

        .safe-preview-value {
            color: #3d332e;
            font-size: 0.84rem;
            line-height: 1.42;
            overflow-wrap: anywhere;
        }

        .safe-preview-card.is-empty .safe-preview-value {
            color: #938780;
        }

        @media (max-width: 900px) {
            .privacy-banner {
                grid-template-columns: auto minmax(0, 1fr);
            }
            .privacy-doc {
                display: none;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
