"""
Shock transmission engine. Shocks hit specific balance-sheet and income-
statement lines (not the Z-EM score directly) and are then rolled forward
through a simplified law of motion so effects compound across years. Every
simplifying assumption is documented inline and surfaced in the UI —
this is a policy-triage tool, not a precise multi-year forecast.

Transmission channels (see SOE_shock_framework.pdf, Section 3, extended
to FX/rate/revenue/arrears/refinancing per the boss-commissioned brief):
  - Fuel:      ΔEBIT = -phi * OpEx * fuel_shock * (1 - tariff_passthrough)
  - FX (opex): ΔEBIT = -(fx_cost_share*OpEx - fx_revenue_share*Revenue) * fx_shock
  - Revenue:   ΔEBIT = revenue_elasticity * revenue_shock_pct * Revenue, where
               revenue_shock_pct = revenue_shock_std_devs * the SOE's own
               historical revenue-growth volatility (sector fallback if the
               SOE has under 3 years of data) — the standard DSA/DSF
               convention (default -1 std dev), not a flat percentage.
  - Rate:      ΔInterest = floating_debt_share * TotalLiabilities * rate_shock_bps/10000
  - Refinancing: ΔInterest += near_term_maturity_share * TotalLiabilities *
               refinancing_spread_bps/10000 — a maturity-wall shock, distinct
               from the floating-rate shock: this is rollover risk (the cost
               of refinancing debt coming due soon at a stressed spread), not
               the repricing of already-floating debt.
  - FX (debt): ΔEquity = -fx_debt_share * TotalLiabilities * fx_shock (revaluation)
  - Arrears:   ΔCurrentAssets = -arrears_pct_of_revenue * Revenue (receivables write-down proxy)

All shock magnitudes (fuel_shock_pct, fx_shock_pct, rate_shock_bps,
arrears_pct_of_revenue, refinancing_spread_bps) can be negative — a
favorable shock (cheaper fuel, currency appreciation, a rate cut, arrears
clearing) runs the same formulas in reverse. Slider ranges enforcing this
live on the Shock Scenarios page.

Simplifications flagged for future calibration:
  - Tax Expense and Current Liabilities held flat across the horizon.
  - Net Income approximated as EBIT - Interest - Tax (holding Tax flat).
  - Losses are assumed debt-financed (Total Liabilities absorbs the
    financing gap) rather than modeling a cash/overdraft distinction.
  - Shocks apply at full magnitude for `shock_duration_years`, then EBIT/
    Interest revert to unshocked levels — but balance-sheet levels
    (debt, retained earnings, equity) that built up during the shock
    persist forward, which is what makes this "dynamic" rather than a
    one-off recomputation.
"""

import numpy as np
import pandas as pd

import config
from calculations import classify_zem_from_values, compute_pd, compute_pd_from_rating


def run_scenario(base_row: pd.Series, params: dict, horizon_years: int) -> pd.DataFrame:
    """Project one SOE forward under a deterministic shock scenario.
    base_row: a row from the ingested data (post compute_zem_components),
    for a single SOE-year — the starting point for the projection.
    params: dict matching config.DEFAULT_SHOCK_PARAMS keys.
    Returns a DataFrame with one row per projection year (0 = base year,
    unshocked, through horizon_years), including recomputed Z-EM.
    """
    duration = params["shock_duration_years"]

    # Mutable state carried year to year
    state = {
        "EBIT": base_row["Operating Profits (EBIT)"],
        "Interest": base_row["Interest Expense"],
        "Tax": base_row["Tax Expense"],
        "RetainedEarnings": base_row["Retained Earnings"],
        "Equity": base_row["Equity"],
        "TotalLiabilities": base_row["Total Liabilities"],
        "TotalAssets": base_row["Total Assets"],
        "CurrentAssets": base_row["Current Assets"],
        "CurrentLiabilities": base_row["Current Liabilities"],
        "Depreciation": base_row["Depreciation"],
        "Revenue": base_row["Revenues"],
        "OpEx": base_row["Operating Expense"],
    }

    rows = []
    # Year 0: unshocked baseline
    rows.append(_snapshot(base_row["Entity"], base_row.get("Sector", ""), int(base_row["Year"]), 0, state))

    for t in range(1, horizon_years + 1):
        active = t <= duration

        if active:
            d_ebit_fuel = -params["fuel_cost_share"] * state["OpEx"] * params["fuel_shock_pct"] * (1 - params["tariff_passthrough"])
            d_ebit_fx = -(params["fx_cost_share"] * state["OpEx"] - params["fx_revenue_share"] * state["Revenue"]) * params["fx_shock_pct"]
            d_ebit_revenue = params["revenue_elasticity"] * params.get("revenue_shock_pct", 0.0) * state["Revenue"]
            d_interest_rate = params["floating_debt_share"] * state["TotalLiabilities"] * (params["rate_shock_bps"] / 10000.0)
            d_interest_refi = params.get("near_term_maturity_share", 0.0) * state["TotalLiabilities"] * (params.get("refinancing_spread_bps", 0.0) / 10000.0)
            d_interest = d_interest_rate + d_interest_refi
            d_equity_fx_reval = -params["fx_debt_share"] * state["TotalLiabilities"] * params["fx_shock_pct"]
            d_current_assets_arrears = -params["arrears_pct_of_revenue"] * state["Revenue"]
        else:
            d_ebit_fuel = d_ebit_fx = d_ebit_revenue = 0.0
            d_interest = d_equity_fx_reval = d_current_assets_arrears = 0.0

        ebit_t = base_row["Operating Profits (EBIT)"] + d_ebit_fuel + d_ebit_fx + d_ebit_revenue
        interest_t = base_row["Interest Expense"] + d_interest
        # NI carries forward the SOE's ACTUAL reported Net Income, plus only
        # the shock's incremental effect — not a recomputation from
        # EBIT-Interest-Tax, which ignores other income/expense/tax-timing
        # items real statements have and drifted under zero shock as a
        # result. Under true zero shock (all deltas 0), NI_t = actual base
        # Net Income exactly, every year.
        d_ebit_total = d_ebit_fuel + d_ebit_fx + d_ebit_revenue
        net_income_t = base_row["Net Income"] + d_ebit_total - d_interest

        financing_gap = max(0.0, -net_income_t)

        state["RetainedEarnings"] = state["RetainedEarnings"] + net_income_t
        state["Equity"] = state["Equity"] + net_income_t + d_equity_fx_reval
        state["TotalLiabilities"] = state["TotalLiabilities"] + financing_gap - d_equity_fx_reval
        state["CurrentAssets"] = state["CurrentAssets"] + d_current_assets_arrears
        state["TotalAssets"] = state["TotalAssets"] + net_income_t + d_current_assets_arrears
        state["EBIT"] = ebit_t
        state["Interest"] = interest_t

        rows.append(_snapshot(base_row["Entity"], base_row.get("Sector", ""), int(base_row["Year"]) + t, t, state))

    return pd.DataFrame(rows)


def _snapshot(entity, sector, calendar_year, t, state) -> dict:
    working_capital = state["CurrentAssets"] - state["CurrentLiabilities"]
    x1, x2, x3, x4, z, zone = classify_zem_from_values(
        working_capital=working_capital,
        total_assets=state["TotalAssets"],
        retained_earnings=state["RetainedEarnings"],
        ebit=state["EBIT"],
        equity=state["Equity"],
        total_liabilities=state["TotalLiabilities"],
    )
    return {
        "Entity": entity,
        "Sector": sector,
        "Calendar Year": calendar_year,
        "Projection Year": t,
        "EBIT": state["EBIT"],
        "Interest Expense": state["Interest"],
        "Retained Earnings": state["RetainedEarnings"],
        "Equity": state["Equity"],
        "Total Liabilities": state["TotalLiabilities"],
        "Total Assets": state["TotalAssets"],
        "Current Assets": state["CurrentAssets"],
        "Current Liabilities": state["CurrentLiabilities"],
        "X1": x1, "X2": x2, "X3": x3, "X4": x4,
        "Z_EM": z, "Zone": zone, "Rating": config.z_rating(z),
    }


def kpi_impact_table(scenario_df: pd.DataFrame) -> pd.DataFrame:
    """Year-0 vs final-year comparison of Z-EM components, for the
    shock x KPI heatmap / tornado chart."""
    base = scenario_df.iloc[0]
    final = scenario_df.iloc[-1]
    rows = []
    for comp in config.ZEM_COEFFICIENTS:
        rows.append({
            "Component": config.ZEM_LABELS[comp],
            "Base value": base[comp],
            "Final value": final[comp],
            "Change": final[comp] - base[comp],
            "Weighted contribution to ΔZ": (final[comp] - base[comp]) * config.ZEM_COEFFICIENTS[comp],
        })
    return pd.DataFrame(rows)


def gdp_path(base_gdp: float, growth_rate: float, horizon_years: int) -> list:
    """Simple compounding GDP projection for the EFC/GDP path chart."""
    return [base_gdp * ((1 + growth_rate) ** t) for t in range(horizon_years + 1)]


def run_monte_carlo(base_row: pd.Series, params: dict, n_sims: int, fuel_std: float,
                     fx_std: float, correlation: float, horizon_years: int,
                     lgd_pct: float, seed: int = 42) -> pd.DataFrame:
    """Draw correlated fuel/FX shock magnitudes and run the scenario for each
    draw. Returns a LONG-format DataFrame — one row per (simulation, year) —
    so callers can either take the final year (for a distribution/histogram)
    or group by year (for a percentile path over time)."""
    rng = np.random.default_rng(seed)

    mean = [params["fuel_shock_pct"], params["fx_shock_pct"]]
    cov = [
        [fuel_std ** 2, correlation * fuel_std * fx_std],
        [correlation * fuel_std * fx_std, fx_std ** 2],
    ]
    draws = rng.multivariate_normal(mean, cov, size=n_sims)

    all_rows = []
    for i in range(n_sims):
        sim_params = dict(params)
        sim_params["fuel_shock_pct"] = draws[i, 0]
        sim_params["fx_shock_pct"] = draws[i, 1]

        scenario = run_scenario(base_row, sim_params, horizon_years)
        scenario["sim"] = i
        scenario["fuel_shock_pct"] = draws[i, 0]
        scenario["fx_shock_pct"] = draws[i, 1]
        scenario["PD"] = scenario["Rating"].apply(compute_pd_from_rating)
        scenario["EAD"] = scenario["Total Liabilities"]
        scenario["LGD"] = lgd_pct / 100.0
        scenario["EFC"] = scenario["PD"] * scenario["EAD"] * scenario["LGD"]
        all_rows.append(scenario)

    return pd.concat(all_rows, ignore_index=True)


def mc_percentile_path(mc_long: pd.DataFrame, value_col: str,
                        percentiles=(0.05, 0.25, 0.50, 0.75, 0.95)) -> pd.DataFrame:
    """Collapse a long-format Monte Carlo DataFrame (from run_monte_carlo)
    into a per-year percentile path for the given value column."""
    grouped = mc_long.groupby("Projection Year")[value_col]
    out = grouped.quantile(list(percentiles)).unstack()
    out.columns = [f"p{int(p*100)}" for p in percentiles]
    out = out.reset_index()
    # attach calendar year for x-axis labeling
    cal_years = mc_long.groupby("Projection Year")["Calendar Year"].first()
    out["Calendar Year"] = out["Projection Year"].map(cal_years)
    return out


def describe_active_shocks(params: dict) -> str:
    """Compact, human-readable summary of only the non-zero shock
    magnitude channels in `params` — for annotating charts so a saved or
    downloaded chart is interpretable on its own, and so runs (fuel alone
    vs FX alone vs combined) are distinguishable when compared side by
    side. Exposure/structural parameters (fuel cost share, tariff
    pass-through, FX shares, etc.) are not shock magnitudes and are left
    out — only the channels that actually move something show up here."""
    parts = []
    if params.get("fuel_shock_pct", 0) != 0:
        parts.append(f"Fuel {params['fuel_shock_pct']*100:+.0f}%")
    if params.get("fx_shock_pct", 0) != 0:
        parts.append(f"FX {params['fx_shock_pct']*100:+.0f}%")
    if params.get("rate_shock_bps", 0) != 0:
        parts.append(f"Rate {params['rate_shock_bps']:+.0f}bps")
    if params.get("revenue_shock_pct", 0) != 0:
        std_devs = params.get("revenue_shock_std_devs")
        if std_devs is not None and std_devs != 0:
            parts.append(f"Revenue {std_devs:+.1f}\u03c3")
        else:
            parts.append(f"Revenue {params['revenue_shock_pct']*100:+.0f}%")
    if params.get("refinancing_spread_bps", 0) != 0 and params.get("near_term_maturity_share", 0) > 0:
        parts.append(f"Refi {params['refinancing_spread_bps']:+.0f}bps")
    if params.get("arrears_pct_of_revenue", 0) != 0:
        parts.append(f"Arrears {params['arrears_pct_of_revenue']*100:+.0f}%/yr")

    if not parts:
        return "No shock applied (baseline)"

    duration = params.get("shock_duration_years")
    summary = ", ".join(parts)
    if duration:
        summary += f" — active {duration}yr"
    return summary
