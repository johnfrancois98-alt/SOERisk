import streamlit as st

from utils import theme

st.set_page_config(page_title="SOE Fiscal Risk Tool", layout="wide", page_icon="🏛️")
theme.inject()

home_page = st.Page("app_pages/home.py", title="Home", icon="🏠", default=True)
kpi_page = st.Page("app_pages/kpi_dashboard.py", title="KPI Dashboard", icon="📊")
altman_page = st.Page("app_pages/altman_z.py", title="Altman Z-EM", icon="📉")
efc_page = st.Page("app_pages/efc.py", title="Expected Fiscal Cost", icon="💰")
shock_page = st.Page("app_pages/shock_scenarios.py", title="Shock Scenarios", icon="⚡")
gre_page = st.Page("app_pages/strategic_soe.py", title="Government Support", icon="🏛️")

pg = st.navigation([home_page, kpi_page, altman_page, efc_page, shock_page, gre_page], position="top")
pg.run()
