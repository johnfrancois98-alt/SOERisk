"""
Shared look and feel for every page: top nav bar (dark navy, logo, icon
links — no sidebar), the light content area, glossy stat cards, and
chip/badge helpers. Colors come from config.THEME — change them there,
not here. Every font-size below is wrapped in fs(...), so config.FONT_SCALE
controls all of them from one place.
"""

from pathlib import Path

import streamlit as st

from config import BASE_ROOT_PX, FONT_SCALE, THEME, fs

_LOGO_PATH = Path(__file__).resolve().parent.parent / "assets" / "logo.png"


def inject():
    if _LOGO_PATH.exists():
        st.logo(str(_LOGO_PATH))

    st.markdown(
        f"""
        <style>
        html {{ font-size: {round(BASE_ROOT_PX * FONT_SCALE, 2)}px; }}
        html, body, [class*="css"] {{
            font-family: "Segoe UI", Inter, system-ui, -apple-system, sans-serif;
        }}
        .stApp {{ background: {THEME['bg']}; }}
        #MainMenu {{visibility: hidden;}}
        div[data-testid="stAppDeployButton"] {{ display: none !important; }}
        .block-container {{ padding-top: 88px; max-width: 1220px; }}

        /* ---------------- Top nav bar (replaces the sidebar) ---------------- */
        header[data-testid="stHeader"] {{
            background: {THEME['sidebar_bg']} !important;
            height: 60px;
        }}
        [data-testid="stHeaderLogo"] {{ height: 34px !important; width: auto !important; }}
        [data-testid="stTopNavLink"] {{
            color: {THEME['sidebar_text']} !important;
            border-radius: 10px;
            padding: 7px 12px !important;
            font-size: {fs(14)};
            font-weight: 500;
            transition: background 0.12s ease;
        }}
        [data-testid="stTopNavLink"] * {{ color: {THEME['sidebar_text']} !important; }}
        [data-testid="stTopNavLink"]:hover {{ background: {THEME['sidebar_bg_active']}; }}
        [data-testid="stTopNavLink"]:hover * {{ color: {THEME['sidebar_text_active']} !important; }}
        [data-testid="stTopNavLink"][aria-current="page"] {{
            background: {THEME['blue']};
            font-weight: 600;
        }}
        [data-testid="stTopNavLink"][aria-current="page"] * {{ color: #FFFFFF !important; }}
        span[data-testid="stMainMenu"] {{ visibility: visible !important; }}
        span[data-testid="stMainMenu"] svg {{ fill: {THEME['sidebar_text']} !important; }}

        /* ---------------- Headings ---------------- */
        .sfp-eyebrow {{
            color: {THEME['blue']}; font-size: {fs(12)}; font-weight: 700;
            letter-spacing: 0.04em; margin-bottom: 6px;
        }}
        .sfp-page-title {{ font-size: {fs(26)}; font-weight: 700; color: {THEME['text']}; margin: 0 0 4px; }}
        .sfp-page-subtitle {{
            font-size: {fs(14)}; color: {THEME['muted']}; margin: 0 0 20px; max-width: 720px; line-height: 1.5;
        }}

        /* ---------------- Cards ---------------- */
        .sfp-card {{
            background: {THEME['card']}; border: 1px solid {THEME['border']}; border-radius: 16px;
            padding: 15px 18px; margin-bottom: 14px;
            box-shadow: 0 1px 2px rgba(16,24,40,0.04), 0 1px 8px rgba(16,24,40,0.04);
        }}
        .sfp-title {{
            font-size: {fs(15.5)} !important; font-weight: 700 !important; color: {THEME['text']} !important;
            margin: 0 0 8px !important; line-height: 1.25 !important; display: block;
        }}
        .sfp-card-compact {{
            background: {THEME['card']}; border: 1px solid {THEME['border']}; border-radius: 14px;
            padding: 6px 10px; margin-bottom: 6px;
            box-shadow: 0 1px 2px rgba(16,24,40,0.04), 0 1px 8px rgba(16,24,40,0.04);
        }}
        .sfp-compact-title {{
            font-size: {fs(13.5)} !important; font-weight: 700 !important; color: {THEME['blue']} !important;
            margin: 0 0 4px !important; line-height: 1.25 !important; display: block;
        }}
        .sfp-kpi-desc {{
            font-size: {fs(10.45)} !important; color: {THEME['muted']} !important; line-height: 1.42 !important;
            margin: 5px 0 0 !important; min-height: 92px; display: block;
        }}

        /* ---------------- Stat cards ---------------- */
        .sfp-stat {{
            background: {THEME['card']}; border: 1px solid {THEME['border']}; border-radius: 16px;
            padding: 18px 20px;
            box-shadow: 0 1px 2px rgba(16,24,40,0.04), 0 1px 8px rgba(16,24,40,0.04);
        }}
        .sfp-stat-top {{ display: flex; align-items: center; gap: 10px; margin-bottom: 14px; }}
        .sfp-stat-icon {{
            width: 38px; height: 38px; border-radius: 10px; flex-shrink: 0;
            display: flex; align-items: center; justify-content: center; font-size: {fs(17)};
        }}
        .sfp-stat-label {{ font-size: {fs(13)}; font-weight: 600; color: {THEME['text']}; }}
        .sfp-stat-value {{ font-size: {fs(26)}; font-weight: 700; color: {THEME['text']}; line-height: 1.15; }}
        .sfp-stat-caption {{ font-size: {fs(12)}; color: {THEME['muted']}; margin-top: 5px; }}
        .sfp-stat-caption b.up {{ color: {THEME['green']}; }}
        .sfp-stat-caption b.down {{ color: {THEME['red']}; }}

        /* ---------------- Top filter bar ---------------- */
        .sfp-topbar {{
            background: {THEME['card']}; border: 1px solid {THEME['border']}; border-radius: 14px;
            padding: 10px 16px; margin-bottom: 18px;
        }}
        span[data-tag] {{ background-color: {THEME['blue']} !important; border-radius: 6px !important; }}
        span[data-tag] span[title] {{ color: #FFFFFF !important; }}
        span[data-tag] button {{ color: #FFFFFF !important; }}
        span[data-tag] button svg {{ stroke: #FFFFFF !important; }}

        /* ---------------- Alerts ---------------- */
        .sfp-alert {{ font-size: {fs(12.5)}; padding: 9px 12px; border-radius: 9px; margin-top: 10px; line-height: 1.45; }}
        .sfp-alert.ok {{ background: {THEME['green_bg']}; color: #1F5A4B; }}
        .sfp-alert.info {{ background: {THEME['blue_bg']}; color: #1E3E82; }}
        .sfp-alert.warn {{ background: {THEME['red_bg']}; color: #8C3A1C; }}

        .sfp-hint {{ font-size: {fs(12)}; color: {THEME['muted']}; line-height: 1.5; }}
        .sfp-summary {{
            background: {THEME['blue_bg']}; border-left: 3px solid {THEME['blue']}; border-radius: 8px;
            padding: 11px 13px; font-size: {fs(12.5)}; line-height: 1.5; color: {THEME['text']}; margin-top: 10px;
        }}
        .sfp-summary .tag {{ font-size: {fs(10)}; color: {THEME['muted']}; display: block; margin-bottom: 3px; }}

        /* ---------------- Tables ---------------- */
        table.sfp-table {{ border-collapse: collapse; width: 100%; font-size: {fs(13)}; }}
        table.sfp-table th {{
            text-align: left; font-size: {fs(11)}; color: {THEME['muted']}; font-weight: 700;
            padding: 8px 10px; border-bottom: 1.5px solid {THEME['border']}; white-space: nowrap;
        }}
        table.sfp-table td {{ padding: 9px 10px; border-bottom: 1px solid {THEME['border']}; white-space: nowrap; }}
        /* Wrap variant — for tables holding paragraph-length text (glossary
           definitions, criteria descriptions), where nowrap runs long text
           off the edge instead of wrapping it. Scorecard tables (short
           values, ratings) keep the default nowrap above. */
        table.sfp-table-wrap td {{ white-space: normal; word-wrap: break-word; vertical-align: top; }}
        table.sfp-table-wrap th {{ white-space: normal; }}
        .sfp-dot {{ display:inline-block; width:8px; height:8px; border-radius:50%; margin-right:6px; }}
        .sfp-chip {{ display:inline-block; padding: 3px 10px; border-radius: 999px; font-size: {fs(11.5)}; font-weight: 700; }}
        .sfp-chip.red {{ background:{THEME['red_bg']}; color:{THEME['red']}; }}
        .sfp-chip.amber {{ background:{THEME['amber_bg']}; color:{THEME['amber']}; }}
        .sfp-chip.green {{ background:{THEME['green_bg']}; color:{THEME['green']}; }}
        .sfp-chip.muted {{ background:#EEF0F4; color:{THEME['muted']}; }}

        .sfp-footnote {{ font-size: {fs(11.5)}; color: {THEME['muted']}; line-height: 1.6; }}

        /* ---------------- Info tooltip icon ---------------- */
        .sfp-info {{
            display: inline-block; cursor: help; color: {THEME['muted']}; font-size: {fs(12)};
            margin-left: 4px; border-bottom: 1px dotted {THEME['muted']};
        }}
        .sfp-info:hover {{ color: {THEME['blue']}; }}

        .stButton>button {{ border-radius: 9px; }}
        .stDownloadButton>button {{ border-radius: 9px; }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def info_icon(text):
    """A small (?) icon that shows `text` as a native browser tooltip on
    hover — use inline next to a label or title, e.g.:
    st.markdown(f'Z-EM score {theme.info_icon(config.GLOSSARY["Z-EM score"])}', unsafe_allow_html=True)"""
    return f'<span class="sfp-info" title="{text}">ⓘ</span>'


def header(eyebrow, title, subtitle):
    st.markdown(
        f"""
        <div class="sfp-eyebrow">{eyebrow}</div>
        <div class="sfp-page-title">{title}</div>
        <div class="sfp-page-subtitle">{subtitle}</div>
        """,
        unsafe_allow_html=True,
    )


def stat_card(icon, color_key, label, value, caption=""):
    """color_key: one of 'blue', 'green', 'amber', 'red', 'gold', 'purple',
    'chart_navy' (see config.THEME). Returns an HTML string — wrap the call
    in st.markdown(..., unsafe_allow_html=True)."""
    bg = THEME.get(f"{color_key}_bg", THEME["blue_bg"])
    fg = THEME.get(color_key, THEME["blue"])
    return (
        f'<div class="sfp-stat">'
        f'<div class="sfp-stat-top">'
        f'<div class="sfp-stat-icon" style="background:{bg};color:{fg}">{icon}</div>'
        f'<div class="sfp-stat-label">{label}</div>'
        f"</div>"
        f'<div class="sfp-stat-value">{value}</div>'
        f'<div class="sfp-stat-caption">{caption}</div>'
        f"</div>"
    )


def summary_box(text):
    st.markdown(
        f'<div class="sfp-summary"><span class="tag">Automated summary — generated from the data on screen, '
        f'not written by a person</span>{text}</div>',
        unsafe_allow_html=True,
    )
