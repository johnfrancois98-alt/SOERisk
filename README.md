# SOE Fiscal Risk Tool

Multi-page Python/Streamlit tool for state-owned enterprises: Altman
Z''-EM distress scoring, an expanded KPI diagnostic set, Expected Fiscal
Cost (PD × EAD × LGD), and dynamic shock simulation with a Monte Carlo
distribution option. Visual system and page patterns matched to the
companion Pacific SOE fiscal-injection tool.

## Structure

```
soe_tool/
├── Home.py                 Entry point — page config, shared chrome,
│                            top-nav routing to the pages below
├── config.py                ALL tunable numbers live here
├── calculations.py          Z-EM, KPI ratios, red/amber/green classify, EFC
├── shocks.py                 Shock transmission engine + Monte Carlo
├── narrative.py              Rule-based component-attribution summaries
├── data_loader.py            Upload handling, schema validation, sample data
├── assets/
│   └── logo.png              top-nav wordmark (used via st.logo)
├── utils/
│   ├── theme.py               shared CSS, palette, stat cards, header
│   ├── charts.py               chart label wrapping, CSV+PNG download row
│   ├── filters.py               shared Sector filter bar
│   ├── summary.py                rules-based plain-language summaries
│   └── portfolio.py               latest_per_entity helper
├── app_pages/
│   ├── home.py                About + data upload
│   ├── kpi_dashboard.py        Profitability/Liquidity/Solvency/Fiscal —
│   │                            4-column layout, dropdown per column
│   ├── altman_z.py              Component matrix (X1–X4 + Z-EM), scorecard
│   │                             with rating, benchmark, donut
│   ├── efc.py                    Expected Fiscal Cost, PD×EAD×LGD
│   └── shock_scenarios.py         Single-scenario / Monte Carlo toggle,
│                                   EFC-as-%-of-GDP path
└── requirements.txt
```

## Run it locally

```bash
pip install -r requirements.txt
streamlit run Home.py
```

## Where to make changes later

Almost everything tunable lives in **`config.py`**:

- `ZEM_COEFFICIENTS` / `ZEM_CONSTANT` — the Altman Z''-EM formula itself
- `Z_DISTRESS_CUTOFF` / `Z_SAFE_CUTOFF` — zone boundaries
- `Z_RATING_TABLE` / `z_rating()` — indicative credit-rating cohort mapping
- `PD_BY_ZONE` — PD mapped from Z-EM zone, a placeholder pending
  probit-estimated probabilities
- `KPI_THRESHOLDS` — red/amber/green cutoffs, formulas' required raw
  columns, and the description shown under each chart
- `KPI_CATEGORIES` / `CATEGORY_LABELS` — which ratios show up under
  Profitability / Liquidity / Solvency / Fiscal dependency
- `SECTOR_FUEL_COST_SHARE`, `DEFAULT_SHOCK_PARAMS`, `MC_DEFAULT_*` — shock
  and Monte Carlo defaults
- `THEME` / `ZONE_COLORS` — the color palette (navy / sky-blue / gold / red)
- `CHART_LAYOUT` / `FONT_SCALE` — shared chart sizing and app-wide font scale

## Known simplifications, flagged in-app

- PD is mapped from the Z-EM zone only (0.72 / 0.35 / 0.05) — not yet
  probit-estimated from panel data.
- EAD is proxied by Total Liabilities, pending a dedicated
  exposure-at-default methodology.
- LGD is user-set (1–100%); sector reference ranges are shown but not
  auto-applied.
- The shock engine holds Tax Expense and Current Liabilities flat across
  the horizon, approximates Net Income as EBIT − Interest − Tax, and
  assumes losses are debt-financed. See `shocks.py` for full documentation.
- Chart PNG downloads need the pinned `kaleido==0.2.1` + `plotly==5.24.1`
  combination in `requirements.txt` — if it can't render an image, the
  "🖼 Chart" button simply doesn't appear; "⬇ Data" always still works.
- Portfolio averages are simple means across SOEs — not asset-weighted.
- A full guidance note (methodology, assumptions, calibration) is planned
  once the framework stabilizes — not yet built.
