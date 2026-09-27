"""
Calculation layer: Z''-EM, supplementary KPIs, red/amber/green classification,
and Expected Fiscal Cost. Pure functions operating on a pandas DataFrame in
the long-format schema defined in config.REQUIRED_COLUMNS.
"""

import numpy as np
import pandas as pd

import config


def compute_zem_components(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["X1"] = (out["Current Assets"] - out["Current Liabilities"]) / out["Total Assets"]
    out["X2"] = out["Retained Earnings"] / out["Total Assets"]
    out["X3"] = out["Operating Profits (EBIT)"] / out["Total Assets"]
    out["X4"] = out["Equity"] / out["Total Liabilities"]

    for comp, beta in config.ZEM_COEFFICIENTS.items():
        out[f"{comp}_contrib"] = out[comp] * beta

    out["Z_EM"] = sum(out[f"{c}_contrib"] for c in config.ZEM_COEFFICIENTS) + config.ZEM_CONSTANT
    out["Zone"] = out["Z_EM"].apply(classify_zone)
    out["Rating"] = out["Z_EM"].apply(config.z_rating)
    return out


def classify_zone(z_score: float) -> str:
    if pd.isna(z_score):
        return "Unknown"
    for zone, lower, upper in config.ZONES:
        if lower < z_score <= upper:
            return zone
    return "Unknown"


def classify_zem_from_values(working_capital, total_assets, retained_earnings,
                               ebit, equity, total_liabilities):
    """Scalar version, for the dynamic shock projection loop."""
    x1 = working_capital / total_assets if total_assets else np.nan
    x2 = retained_earnings / total_assets if total_assets else np.nan
    x3 = ebit / total_assets if total_assets else np.nan
    x4 = equity / total_liabilities if total_liabilities else np.nan
    z = (
        config.ZEM_COEFFICIENTS["X1"] * x1 + config.ZEM_COEFFICIENTS["X2"] * x2
        + config.ZEM_COEFFICIENTS["X3"] * x3 + config.ZEM_COEFFICIENTS["X4"] * x4
        + config.ZEM_CONSTANT
    )
    return x1, x2, x3, x4, z, classify_zone(z)


def _safe_div(numerator, denominator):
    with np.errstate(divide="ignore", invalid="ignore"):
        result = numerator / denominator
    return result.replace([np.inf, -np.inf], np.nan)


def compute_kpis(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    revenue = out["Revenues"]
    ebit = out["Operating Profits (EBIT)"]

    out["operating_margin"] = _safe_div(ebit, revenue)
    out["net_margin"] = _safe_div(out["Net Income"], revenue)
    out["ebitda_margin"] = _safe_div(out["EBITDA"], revenue)
    out["roa"] = _safe_div(out["Net Income"], out["Total Assets"])
    # ROE/Debt-Equity/Debt-EBITDA flip sign under negative equity/EBITDA —
    # suppressed (NaN) rather than shown as a false "good" reading.
    out["roe"] = _safe_div(out["Net Income"], out["Equity"]).where(out["Equity"] > 0)

    out["current_ratio"] = _safe_div(out["Current Assets"], out["Current Liabilities"])
    out["working_capital_ratio"] = out.get("X1", _safe_div(
        out["Current Assets"] - out["Current Liabilities"], out["Total Assets"]
    ))

    out["debt_to_ebitda"] = _safe_div(out["Total Liabilities"], out["EBITDA"]).where(out["EBITDA"] > 0)
    out["liabilities_to_assets"] = _safe_div(out["Total Liabilities"], out["Total Assets"])
    out["interest_coverage"] = _safe_div(ebit, out["Interest Expense"])
    out["debt_to_equity"] = _safe_div(out["Total Liabilities"], out["Equity"]).where(out["Equity"] > 0)

    out["asset_turnover"] = _safe_div(revenue, out["Total Assets"])
    out["depreciation_to_ebitda"] = _safe_div(out["Depreciation"], out["EBITDA"]).where(out["EBITDA"] > 0)

    out["grants_to_revenue"] = _safe_div(out["Government Grants"], revenue)
    out["grants_to_expense"] = _safe_div(out["Government Grants"], out["Total Expense"])
    out["effective_tax_rate"] = _safe_div(out["Tax Expense"], ebit).where(ebit > 0)

    out["negative_equity_flag"] = out["Equity"] <= 0
    out["negative_ebitda_flag"] = out["EBITDA"] <= 0
    return out


def available_kpis(df: pd.DataFrame, category=None):
    """Which KPIs have all required raw columns present and non-null
    somewhere in df. Pass a category key to filter, or omit for all."""
    keys = config.KPI_CATEGORIES[category] if category else list(config.KPI_THRESHOLDS.keys())
    available = []
    for key in keys:
        spec = config.KPI_THRESHOLDS[key]
        if all(c in df.columns and df[c].notna().any() for c in spec["requires"]):
            available.append(key)
    return available


def classify(value, kpi_key):
    """Returns (label, color_key) — 'Red'/'Amber'/'Green'/'No data'."""
    if pd.isna(value):
        return "No data", "muted"
    spec = config.KPI_THRESHOLDS[kpi_key]
    red_cut, green_cut = spec["red_cut"], spec["green_cut"]
    if spec["direction"] == "higher_is_better":
        if value < red_cut:
            return "Red", "red"
        if value >= green_cut:
            return "Green", "green"
        return "Amber", "amber"
    else:
        if value > red_cut:
            return "Red", "red"
        if value <= green_cut:
            return "Green", "green"
        return "Amber", "amber"


def compute_pd(zone: str) -> float:
    """Coarse 3-bucket fallback. Prefer compute_pd_from_rating() — this
    stays only for a missing/unrecognized rating."""
    return config.PD_BY_ZONE.get(zone, np.nan)


def compute_pd_from_rating(rating: str) -> float:
    """Per-rating PD from the uploaded rating cohort table
    (config.PD_BY_RATING) — the primary PD calibration, differentiating
    within a zone rather than collapsing it to one flat value."""
    pd_val = config.pd_by_rating(rating)
    return pd_val if pd_val == pd_val else np.nan  # NaN-safe passthrough


def compute_efc(df: pd.DataFrame, lgd_pct: float) -> pd.DataFrame:
    out = df.copy()
    out["PD"] = out["Rating"].apply(compute_pd_from_rating)
    out["EAD"] = out["Total Liabilities"]
    out["LGD"] = lgd_pct / 100.0
    out["EFC"] = out["PD"] * out["EAD"] * out["LGD"]
    return out


def recovery_rate_scenarios(sector: str):
    """Four points on the sector's actual GEMs recovery-rate distribution
    (config.SECTOR_RECOVERY_DATA), relabeled as government backstop
    intensity: lender recovery rate (RR) = government LGD directly here
    (not 1 - RR) — the lender recovers a lot precisely because the
    government stepped in to make it whole, so a high RR means a high
    government LGD, i.e. high backstop intensity.
      Low Backstop Intensity     = 10th percentile RR (least the
                                    government has had to absorb)
      25th Percentile            = the reported 25th percentile RR
      Average Backstop Intensity = the reported average RR
      High Backstop Intensity    = 90th percentile RR (most the
                                    government has had to absorb)
    Real distribution points, not an interpolation. Returns a list of
    (label, LGD fraction) tuples, ascending."""
    d = config.SECTOR_RECOVERY_DATA.get(sector, config.SECTOR_RECOVERY_DATA["Other"])
    return [
        ("Low Backstop Intensity", round(d["p10"], 4)),
        ("25th Percentile", round(d["p25"], 4)),
        ("Average Backstop Intensity", round(d["average"], 4)),
        ("High Backstop Intensity", round(d["p90"], 4)),
    ]



def historical_revenue_volatility(df: pd.DataFrame, entity: str):
    """Standard deviation of year-over-year revenue growth for one SOE,
    computed from its own panel data. Returns NaN if the SOE has fewer
    than 3 years of Revenue observations — callers should fall back to
    config.SECTOR_REVENUE_VOLATILITY in that case."""
    d = df[df["Entity"] == entity].sort_values("Year")
    revenue = d["Revenues"].dropna()
    if len(revenue) < 3:
        return np.nan
    growth = revenue.pct_change().dropna()
    if len(growth) < 2:
        return np.nan
    return float(growth.std())


def rating_notch_change(df: pd.DataFrame, entity: str):
    """Change in an SOE's Z-EM-derived rating from its earliest to latest
    available year, in notches (negative = deterioration). Returns
    (first_rating, last_rating, notch_change) — notch_change is None if
    fewer than 2 years of data or a rating fell outside the recognized
    scale."""
    d = df[df["Entity"] == entity].sort_values("Year")
    d = d.dropna(subset=["Rating"])
    if len(d) < 2:
        return None, None, None
    first_rating = d["Rating"].iloc[0]
    last_rating = d["Rating"].iloc[-1]
    first_idx = config.rating_index(first_rating)
    last_idx = config.rating_index(last_rating)
    if first_idx is None or last_idx is None:
        return first_rating, last_rating, None
    return first_rating, last_rating, last_idx - first_idx
