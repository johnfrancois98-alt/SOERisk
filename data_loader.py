"""
Data ingestion layer. Accepts an uploaded Excel/CSV file in the long-format
schema (one row per SOE per year), validates required columns, and coerces
numeric fields. Missing optional (shock-module) columns are reported but do
not block ingestion.
"""

import io

import pandas as pd

import config

NUMERIC_COLUMNS = [
    "Year", "Revenues", "Total Expense", "Operating Expense",
    "Operating Profits (EBIT)", "Net Income", "Current Assets", "Total Assets",
    "Current Liabilities", "Total Liabilities", "Equity", "Retained Earnings",
    "Interest Expense", "Tax Expense", "EBITDA", "Government Grants",
    "Depreciation",
]


def load_uploaded_file(uploaded_file) -> pd.DataFrame:
    """Read an uploaded Streamlit file object (xlsx or csv) into a DataFrame."""
    name = uploaded_file.name.lower()
    if name.endswith(".csv"):
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file)
    return df


def validate_schema(df: pd.DataFrame) -> dict:
    """Check df against config.REQUIRED_COLUMNS and OPTIONAL_SHOCK_COLUMNS.
    Returns a dict: {'missing_required': [...], 'missing_optional': [...],
    'ok': bool}."""
    present = set(df.columns)

    # 'Sector' is required for cross-SOE sector comparisons but may be
    # absent in an initial upload — treat it as required-but-fixable.
    missing_required = [c for c in config.REQUIRED_COLUMNS if c not in present]
    missing_optional = [c for c in config.OPTIONAL_SHOCK_COLUMNS if c not in present]

    return {
        "missing_required": missing_required,
        "missing_optional": missing_optional,
        "ok": len(missing_required) == 0,
    }


def coerce_numeric(df: pd.DataFrame) -> pd.DataFrame:
    """Force numeric columns to numeric dtype, coercing errors to NaN so a
    single bad cell doesn't break the whole pipeline. Reports offending
    rows separately via `numeric_issues`."""
    out = df.copy()
    for col in NUMERIC_COLUMNS:
        if col in out.columns:
            out[col] = pd.to_numeric(out[col], errors="coerce")
    return out


def numeric_issues(df: pd.DataFrame) -> pd.DataFrame:
    """Return rows where a required numeric column failed to coerce
    (i.e. is NaN in the coerced frame but was not NaN/blank originally
    would require the pre-coercion frame; here we just flag any NaN in
    a required numeric column post-coercion for the user to review)."""
    required_numeric = [c for c in NUMERIC_COLUMNS if c in config.REQUIRED_COLUMNS]
    mask = df[required_numeric].isna().any(axis=1)
    return df.loc[mask, ["Entity", "Year"] + required_numeric] if "Entity" in df.columns else df.loc[mask]


# ---------------------------------------------------------------------------
# Sample dataset (SOE A - Energy, SOE B - Transport) for demo/testing
# ---------------------------------------------------------------------------
def sample_dataset() -> pd.DataFrame:
    csv_text = """Entity,Year,Sector,Revenues,Total Expense,Operating Expense,Operating Profits (EBIT),Net Income,Current Assets,Total Assets,Current Liabilities,Total Liabilities,Equity,Retained Earnings,Interest Expense,Tax Expense,EBITDA,Net Profit After Tax,Government Grants,Depreciation,Currency,Units
SOE A,2020,Energy,30271510431,53261812296,51429979206,-21364584285,-22990301865,31648484897,50564692838,50455671036,64327611746,-13762918908,-8469714137,610868478,302715104,-17842468772,-22990301865,15517321949,6173944775,FCFA,Absolute
SOE A,2021,Energy,34557778288,35886836510,35383283013,-825504725,-1329058222,40810007803,62442063419,63145445773,74822227996,-12380164577,-31460016002,290098143,305653942,2182341518,-1329058222,18229134502,3007846243,FCFA,Absolute
SOE A,2022,Energy,34693268082,39854246066,39142772316,-4449504234,-5160977984,40967799947,70293954181,72470060858,88609037352,-18315083171,-32789074224,123264449,346932680,242479036,-5160977984,1505559000,4691984270,FCFA,Absolute
SOE A,2023,Energy,38235261289,31844487779,32418714872,6399879771,6813438922,45129531424,83684082230,92937887980,111759665933,-28075583703,-37953021814,479444638,382665412,11102470602,6813438922,14511101888,4702590831,FCFA,Absolute
SOE A,2024,Energy,38423772477,46534568933,48269970712,-7092104070,-8057641089,47374294289,90303140285,109262403808,129137545242,-38834404957,-44766460736,587161828,384237725,-2496980951,-8057641089,11809921723,4595123119,FCFA,Absolute
SOE B,2020,Transport,4107284286,6795173873,6053698168,-3054238134,-1678623608,34299848286,165798922850,5025485902,144569370510,21229542844,-2509855635,741475705,41072843,396194336,-1678623608,16958124859,3450432470,FCFA,Absolute
SOE B,2021,Transport,5304148268,11111429504,8231264230,-2927115962,-1765501072,38696504564,175363451931,5791781654,158003236483,17360215448,-4188479243,827315468,53041483,3189216918,-1765501072,14854298535,6116332880,FCFA,Absolute
SOE B,2022,Transport,5674095665,8320013000,7254070000,-1579974257,-1533261234,43874758647,178578576195,6394854275,163178640327,15399935868,-5953980315,1009193455,56740957,3678092806,-1533261234,14427280189,5258067063,FCFA,Absolute
SOE B,2023,Transport,6134488908,8169292820,7732659414,-1598170506,-2034803912,48170728769,190991805260,7576528787,167373741454,23618063806,-7487241549,1567059813,61344889,3884462312,-2034803912,24680212039,6677479120,FCFA,Absolute
SOE B,2024,Transport,6279189030,10131040111,6703248655,-394835232,-1781721271,53533758953,191813708958,9116087247,170731784701,21081924257,-9522045461,2124729222,62791890,4325681000,-1781721271,23925793761,4720516232,FCFA,Absolute
"""
    return pd.read_csv(io.StringIO(csv_text))


# ---------------------------------------------------------------------------
# Blank template — headers only, for the Home page download button
# ---------------------------------------------------------------------------
TEMPLATE_CSV = ",".join(config.REQUIRED_COLUMNS) + "\n"
