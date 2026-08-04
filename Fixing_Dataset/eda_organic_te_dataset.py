"""
EDA + cleaning script for an Organic Thermoelectric Polymer dataset.

What this script does:
1. Reads your current CSV copy, even if the real header is on row 2 or later.
2. Cleans column names and removes empty rows/columns.
3. Forward-fills metadata columns that came from merged Excel cells.
4. Extracts numeric values from messy strings such as "12 mmol l-1", "180 °C", "6.3 ± 0.5 nm".
5. Creates analysis-ready columns for thermoelectric properties.
6. Recalculates power factor and ZT where possible.
7. Adds category flags: Molecular Design, Doping, Transport Decoupling, Morphology Control, Hybrid Composites.
8. Saves a cleaned CSV and EDA outputs.
9. Generates core EDA plots.

Run:
    python eda_organic_te_dataset.py --input your_dataset_copy.csv --output eda_outputs

Example:
    python eda_organic_te_dataset.py --input data/current_dataset.csv --output outputs/run_01
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


# -----------------------------
# 1. Basic helpers
# -----------------------------


def normalize_text(x):
    """Return clean text, while preserving missing values."""
    if pd.isna(x):
        return np.nan
    x = str(x)
    x = x.replace("\u2212", "-")
    x = x.replace("\u2013", "-")
    x = x.replace("\u2014", "-")
    x = x.replace("\u00a0", " ")
    x = re.sub(r"\s+", " ", x).strip()
    if x in ["", "nan", "NaN", "None", "-"]:
        return np.nan
    return x


def slugify_column(name: str) -> str:
    """Convert messy spreadsheet headers into stable snake_case names."""
    name = normalize_text(name)
    if pd.isna(name):
        name = "unnamed"
    name = str(name).lower()
    name = name.replace("σ", "sigma")
    name = name.replace("κ", "kappa")
    name = name.replace("μ", "u")
    name = name.replace("µ", "u")
    name = name.replace("°", "deg")
    name = re.sub(r"[^a-z0-9]+", "_", name)
    name = re.sub(r"_+", "_", name).strip("_")
    return name or "unnamed"


def deduplicate_columns(cols: List[str]) -> List[str]:
    """Make duplicated column names unique."""
    seen = {}
    out = []
    for col in cols:
        if col not in seen:
            seen[col] = 0
            out.append(col)
        else:
            seen[col] += 1
            out.append(f"{col}__{seen[col] + 1}")
    return out


def first_number(value) -> float:
    """Extract the first numeric value from a cell."""
    if pd.isna(value):
        return np.nan
    text = str(value).replace(",", "")
    text = text.replace("\u2212", "-")
    match = re.search(r"[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?", text)
    if not match:
        return np.nan
    try:
        return float(match.group(0))
    except ValueError:
        return np.nan


def extract_unit(value) -> str:
    """Extract a rough unit string after removing the first number."""
    if pd.isna(value):
        return np.nan
    text = str(value).strip()
    text = re.sub(r"[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?", "", text, count=1)
    text = text.replace("±", "")
    text = re.sub(r"\s+", " ", text).strip()
    return text if text else np.nan


def convert_temperature_to_K(raw_value, numeric_value) -> float:
    """Convert temperature-like cells to K when unit is visible."""
    if pd.isna(numeric_value):
        return np.nan
    text = "" if pd.isna(raw_value) else str(raw_value).lower()
    if "degc" in text or "°c" in text or "℃" in text or re.search(r"\bc\b", text):
        return numeric_value + 273.15
    return numeric_value


def convert_time_to_seconds(raw_value, numeric_value) -> float:
    """Convert time-like cells to seconds when unit is visible."""
    if pd.isna(numeric_value):
        return np.nan
    text = "" if pd.isna(raw_value) else str(raw_value).lower()
    if re.search(r"\bms\b", text):
        return numeric_value / 1000
    if re.search(r"\bmin\b|minute", text):
        return numeric_value * 60
    if re.search(r"\bh\b|hour", text):
        return numeric_value * 3600
    return numeric_value


def safe_mkdir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


# -----------------------------
# 2. Header detection and loading
# -----------------------------


def detect_header_row(csv_path: Path, max_scan_rows: int = 15) -> int:
    """
    Detect the actual header row.
    This is useful when row 1 contains things like "Dataset 3" and row 2 contains real headers.
    """
    preview = pd.read_csv(csv_path, header=None, nrows=max_scan_rows, dtype=str, encoding_errors="ignore")

    key_terms = [
        "datapoint",
        "polymer",
        "smiles",
        "dopant",
        "doping",
        "seebeck",
        "conductivity",
        "power",
        "zt",
        "thermal",
        "temperature",
        "molecular",
        "annealing",
        "film",
    ]

    best_row = 0
    best_score = -1
    for i in range(len(preview)):
        row_text = " ".join([str(x).lower() for x in preview.iloc[i].dropna().tolist()])
        keyword_score = sum(term in row_text for term in key_terms)
        non_empty_score = preview.iloc[i].notna().sum() / 100
        score = keyword_score + non_empty_score
        if score > best_score:
            best_score = score
            best_row = i
    return best_row


def read_dataset(csv_path: Path) -> Tuple[pd.DataFrame, int]:
    """Read CSV using automatic header detection."""
    header_row = detect_header_row(csv_path)
    df = pd.read_csv(csv_path, header=header_row, dtype=str, encoding_errors="ignore")

    df = df.dropna(axis=0, how="all")
    df = df.dropna(axis=1, how="all")

    df.columns = deduplicate_columns([slugify_column(c) for c in df.columns])

    for col in df.columns:
        df[col] = df[col].map(normalize_text)

    df = df.dropna(axis=0, how="all").reset_index(drop=True)
    return df, header_row


# -----------------------------
# 3. Flexible column matching
# -----------------------------


COLUMN_ALIASES: Dict[str, List[str]] = {
    "datapoint_id": ["datapoint_id", "data_point_id", "id"],
    "exact_polymer_name": ["exact_polymer_name", "polymer_name", "exact_name"],
    "polymer_family": ["polymer_family", "family"],
    "chemical_structure_image": ["chemical_structure_image", "chemical_structure"],
    "repeating_unit_formula": ["repeating_unit_formula", "repeat_unit_formula", "formula"],
    "smiles": ["smiles"],
    "repeat_unit_mw_g_mol": [
        "molecular_weight_of_the_repeating_unit_g_mol",
        "molecular_weight_repeating_unit_g_mol",
        "repeat_unit_molecular_weight",
    ],
    "polymer_mw_raw": [
        "molecular_weight_polymer_molecular_weight_repeat_unit",
        "polymer_molecular_weight_repeat_unit",
    ],
    "film_method_preparation": ["film_method_preparation", "film_method", "preparation_method"],
    "mw_kda": ["mw_weight_average_molecular_weight_kda", "mw_kda", "weight_average_molecular_weight_kda"],
    "pdi": ["pdi_polydispersity_index", "pdi", "polydispersity_index"],
    "mn_kda": ["mn_number_average_molecular_weight_kda", "mn_kda", "number_average_molecular_weight_kda"],
    "dopant": ["dopant"],
    "doping_level_raw": ["doping_level_solution_concentration", "doping_level", "solution_concentration"],
    "carrier_type": ["carrier_type"],
    "dopant_solvent": ["dopant_solvent"],
    "polymer_solvent": ["polymer_solvent"],
    "doping_method": ["doping_method"],
    "annealing_temperature_raw": ["annealing_temperature"],
    "annealing_condition": ["annealing_condition"],
    "annealing_time_raw": ["annealing_time"],
    "annealing_atmosphere": ["annealing_atmosphere"],
    "film_thickness_raw": ["film_thickness_nm", "film_thickness"],
    "substrate_type": ["substrate_type"],
    "measurement_temperature_raw": ["measurement_temperature_k", "measurement_temperature"],
    "orientation_alignment": ["orientation_or_alignment", "orientation_alignment", "alignment"],
    "sample_form": ["sample_form"],
    "thermal_conductivity_raw": ["thermal_conductivity_w_m_1_k_1", "thermal_conductivity"],
    "doping_time_raw": ["doping_time_s", "doping_time"],
    "post_treatment": ["post_treatment"],
    "smiles_inchi": ["smiles_inchi", "inchi"],
    "doping_oxidation_level_raw": [
        "doping_or_oxidation_level_mmol_l_1",
        "doping_or_oxidation_level",
        "oxidation_level",
    ],
    "electrical_conductivity_raw": [
        "electrical_conductivity_sigma_s_cm_1",
        "electrical_conductivity_s_cm_1",
        "electrical_conductivity",
        "sigma_s_cm_1",
    ],
    "seebeck_raw": [
        "seebeck_coefficient_s_uv_k_1",
        "seebeck_coefficient_uv_k_1",
        "seebeck_coefficient",
    ],
    "power_factor_raw": [
        "power_factor_extracted_pf_uw_m_1_k_2",
        "power_factor_uw_m_1_k_2",
        "power_factor",
        "pf",
    ],
    "zt_raw": ["zt"],
    "temperature_raw": ["temperature_k", "temperature"],
    "doping_temperature_raw": ["doping_temperature_k", "doping_temperature"],
}


def find_col(df: pd.DataFrame, canonical_name: str) -> Optional[str]:
    """Find the real dataframe column that best matches a canonical field."""
    aliases = COLUMN_ALIASES.get(canonical_name, [canonical_name])
    cols = list(df.columns)

    for alias in aliases:
        if alias in cols:
            return alias

    for alias in aliases:
        for col in cols:
            if alias in col:
                return col

    return None


def make_standard_columns(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Create canonical columns while preserving original columns."""
    out = df.copy()
    mapping_rows = []

    for canonical in COLUMN_ALIASES:
        real_col = find_col(out, canonical)
        mapping_rows.append({"canonical_column": canonical, "matched_input_column": real_col})
        if real_col is not None and canonical not in out.columns:
            out[canonical] = out[real_col]

    mapping = pd.DataFrame(mapping_rows)
    return out, mapping


# -----------------------------
# 4. Cleaning and feature engineering
# -----------------------------


def forward_fill_metadata(df: pd.DataFrame) -> pd.DataFrame:
    """Forward-fill columns that are usually repeated through merged cells in Excel."""
    out = df.copy()

    ffill_candidates = [
        "datapoint_id",
        "exact_polymer_name",
        "polymer_family",
        "repeating_unit_formula",
        "smiles",
        "repeat_unit_mw_g_mol",
        "polymer_mw_raw",
        "film_method_preparation",
        "mw_kda",
        "pdi",
        "mn_kda",
        "dopant",
        "doping_level_raw",
        "carrier_type",
        "dopant_solvent",
        "polymer_solvent",
        "doping_method",
        "annealing_temperature_raw",
        "annealing_condition",
        "annealing_time_raw",
        "annealing_atmosphere",
        "film_thickness_raw",
        "substrate_type",
        "measurement_temperature_raw",
        "orientation_alignment",
        "sample_form",
        "thermal_conductivity_raw",
        "doping_time_raw",
        "post_treatment",
    ]

    for col in ffill_candidates:
        if col in out.columns:
            out[col] = out[col].ffill()

    return out


def add_numeric_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Extract numeric values and useful units from common materials columns."""
    out = df.copy()

    numeric_specs = {
        "repeat_unit_mw_g_mol": "repeat_unit_mw_g_mol_value",
        "polymer_mw_raw": "polymer_mw_value",
        "mw_kda": "mw_kda_value",
        "pdi": "pdi_value",
        "mn_kda": "mn_kda_value",
        "doping_level_raw": "doping_level_value",
        "annealing_temperature_raw": "annealing_temperature_value",
        "annealing_time_raw": "annealing_time_value",
        "film_thickness_raw": "film_thickness_nm_value",
        "measurement_temperature_raw": "measurement_temperature_value",
        "thermal_conductivity_raw": "thermal_conductivity_W_mK",
        "doping_time_raw": "doping_time_value",
        "doping_oxidation_level_raw": "doping_oxidation_level_mmol_L",
        "electrical_conductivity_raw": "electrical_conductivity_S_cm",
        "seebeck_raw": "seebeck_uV_K",
        "power_factor_raw": "power_factor_reported_uW_mK2",
        "zt_raw": "ZT_reported",
        "temperature_raw": "temperature_value",
        "doping_temperature_raw": "doping_temperature_value",
    }

    for raw_col, new_col in numeric_specs.items():
        if raw_col in out.columns:
            out[new_col] = out[raw_col].map(first_number)
            out[f"{new_col}_unit_raw"] = out[raw_col].map(extract_unit)

    if "annealing_temperature_value" in out.columns and "annealing_temperature_raw" in out.columns:
        out["annealing_temperature_K"] = [
            convert_temperature_to_K(raw, val)
            for raw, val in zip(out["annealing_temperature_raw"], out["annealing_temperature_value"])
        ]

    if "measurement_temperature_value" in out.columns and "measurement_temperature_raw" in out.columns:
        out["measurement_temperature_K_clean"] = [
            convert_temperature_to_K(raw, val)
            for raw, val in zip(out["measurement_temperature_raw"], out["measurement_temperature_value"])
        ]

    if "temperature_value" in out.columns and "temperature_raw" in out.columns:
        out["temperature_K_clean"] = [
            convert_temperature_to_K(raw, val)
            for raw, val in zip(out["temperature_raw"], out["temperature_value"])
        ]

    if "doping_temperature_value" in out.columns and "doping_temperature_raw" in out.columns:
        out["doping_temperature_K_clean"] = [
            convert_temperature_to_K(raw, val)
            for raw, val in zip(out["doping_temperature_raw"], out["doping_temperature_value"])
        ]

    if "doping_time_value" in out.columns and "doping_time_raw" in out.columns:
        out["doping_time_s_clean"] = [
            convert_time_to_seconds(raw, val)
            for raw, val in zip(out["doping_time_raw"], out["doping_time_value"])
        ]

    if "annealing_time_value" in out.columns and "annealing_time_raw" in out.columns:
        out["annealing_time_s_clean"] = [
            convert_time_to_seconds(raw, val)
            for raw, val in zip(out["annealing_time_raw"], out["annealing_time_value"])
        ]

    return out


def add_validation_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Recalculate PF and ZT where possible and compare with reported values."""
    out = df.copy()

    required_pf = ["electrical_conductivity_S_cm", "seebeck_uV_K"]
    if all(col in out.columns for col in required_pf):
        # If sigma is S/cm and Seebeck is uV/K:
        # PF in uW m-1 K-2 = sigma * S^2 / 10000
        out["power_factor_calculated_uW_mK2"] = (
            out["electrical_conductivity_S_cm"] * (out["seebeck_uV_K"] ** 2) / 10000
        )

    if "power_factor_reported_uW_mK2" in out.columns and "power_factor_calculated_uW_mK2" in out.columns:
        denom = out["power_factor_reported_uW_mK2"].replace(0, np.nan).abs()
        out["power_factor_error_percent"] = (
            (out["power_factor_calculated_uW_mK2"] - out["power_factor_reported_uW_mK2"]).abs() / denom * 100
        )

    # Prefer measurement temperature. If not available, use temperature column.
    temp_col = None
    if "measurement_temperature_K_clean" in out.columns:
        temp_col = "measurement_temperature_K_clean"
    elif "temperature_K_clean" in out.columns:
        temp_col = "temperature_K_clean"

    pf_for_zt_col = None
    if "power_factor_reported_uW_mK2" in out.columns:
        pf_for_zt_col = "power_factor_reported_uW_mK2"
    elif "power_factor_calculated_uW_mK2" in out.columns:
        pf_for_zt_col = "power_factor_calculated_uW_mK2"

    if temp_col and pf_for_zt_col and "thermal_conductivity_W_mK" in out.columns:
        # ZT = PF(W m-1 K-2) * T / kappa
        # reported PF is in uW m-1 K-2, so multiply by 1e-6
        kappa = out["thermal_conductivity_W_mK"].replace(0, np.nan)
        out["ZT_calculated"] = (out[pf_for_zt_col] * 1e-6 * out[temp_col]) / kappa

    if "ZT_reported" in out.columns and "ZT_calculated" in out.columns:
        denom = out["ZT_reported"].replace(0, np.nan).abs()
        out["ZT_error_percent"] = (out["ZT_calculated"] - out["ZT_reported"]).abs() / denom * 100

    def validation_status(row):
        pf_err = row.get("power_factor_error_percent", np.nan)
        zt_err = row.get("ZT_error_percent", np.nan)

        errors = [x for x in [pf_err, zt_err] if pd.notna(x)]
        if not errors:
            return "not_checkable"
        if max(errors) <= 5:
            return "pass"
        if max(errors) <= 20:
            return "warning"
        return "fail"

    out["validation_status"] = out.apply(validation_status, axis=1)
    return out


def add_category_flags(df: pd.DataFrame) -> pd.DataFrame:
    """Add the five project-level category labels as row-level flags."""
    out = df.copy()

    def has_any(row, cols):
        return int(any(col in out.columns and pd.notna(row.get(col)) for col in cols))

    molecular_cols = [
        "exact_polymer_name",
        "polymer_family",
        "repeating_unit_formula",
        "smiles",
        "mw_kda_value",
        "mn_kda_value",
        "pdi_value",
    ]
    doping_cols = [
        "dopant",
        "doping_level_value",
        "doping_oxidation_level_mmol_L",
        "doping_method",
        "dopant_solvent",
        "carrier_type",
    ]
    transport_cols = [
        "electrical_conductivity_S_cm",
        "seebeck_uV_K",
        "power_factor_reported_uW_mK2",
        "power_factor_calculated_uW_mK2",
        "ZT_reported",
        "thermal_conductivity_W_mK",
    ]
    morphology_cols = [
        "film_method_preparation",
        "polymer_solvent",
        "annealing_temperature_K",
        "annealing_time_s_clean",
        "annealing_atmosphere",
        "film_thickness_nm_value",
        "substrate_type",
        "orientation_alignment",
        "sample_form",
        "post_treatment",
    ]

    out["molecular_design_flag"] = out.apply(lambda r: has_any(r, molecular_cols), axis=1)
    out["doping_flag"] = out.apply(lambda r: has_any(r, doping_cols), axis=1)
    out["transport_decoupling_flag"] = out.apply(lambda r: has_any(r, transport_cols), axis=1)
    out["morphology_control_flag"] = out.apply(lambda r: has_any(r, morphology_cols), axis=1)

    hybrid_keywords = re.compile(
        r"composite|hybrid|cnt|carbon nanotube|graphene|rgo|mxene|nanowire|bi2te3|telluride|filler|blend",
        flags=re.IGNORECASE,
    )

    text_cols = [
        col
        for col in [
            "exact_polymer_name",
            "polymer_family",
            "sample_form",
            "post_treatment",
            "film_method_preparation",
        ]
        if col in out.columns
    ]

    if text_cols:
        joined_text = out[text_cols].fillna("").astype(str).agg(" ".join, axis=1)
        out["hybrid_composites_flag"] = joined_text.map(lambda x: int(bool(hybrid_keywords.search(x))))
    else:
        out["hybrid_composites_flag"] = 0

    category_names = [
        ("molecular_design_flag", "Molecular Design"),
        ("doping_flag", "Doping"),
        ("transport_decoupling_flag", "Transport Decoupling"),
        ("morphology_control_flag", "Morphology Control"),
        ("hybrid_composites_flag", "Hybrid Composites"),
    ]

    def joined_categories(row):
        vals = [name for flag, name in category_names if row.get(flag, 0) == 1]
        return "; ".join(vals)

    def primary_strategy(row):
        # Transport is a measured outcome, so strategy is usually based on design/doping/processing.
        if row.get("hybrid_composites_flag", 0) == 1:
            return "Hybrid Composites"
        if row.get("doping_flag", 0) == 1:
            return "Doping"
        if row.get("morphology_control_flag", 0) == 1:
            return "Morphology Control"
        if row.get("molecular_design_flag", 0) == 1:
            return "Molecular Design"
        if row.get("transport_decoupling_flag", 0) == 1:
            return "Transport Decoupling"
        return np.nan

    out["category_labels"] = out.apply(joined_categories, axis=1)
    out["primary_strategy"] = out.apply(primary_strategy, axis=1)

    return out


def add_row_ids(df: pd.DataFrame) -> pd.DataFrame:
    """Add stable row IDs for the cleaned dataset."""
    out = df.copy()
    out.insert(0, "clean_row_id", [f"OTE-{i:06d}" for i in range(1, len(out) + 1)])
    return out


# -----------------------------
# 5. EDA tables
# -----------------------------


def make_missingness_report(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    n = len(df)
    for col in df.columns:
        missing = df[col].isna().sum()
        rows.append(
            {
                "column": col,
                "missing_count": int(missing),
                "missing_percent": round(missing / n * 100, 2) if n else 0,
                "non_missing_count": int(n - missing),
                "dtype": str(df[col].dtype),
            }
        )
    return pd.DataFrame(rows).sort_values("missing_percent", ascending=False)


def make_numeric_summary(df: pd.DataFrame) -> pd.DataFrame:
    numeric_df = df.select_dtypes(include=[np.number])
    if numeric_df.empty:
        return pd.DataFrame()
    summary = numeric_df.describe().T.reset_index().rename(columns={"index": "column"})
    summary["missing_count"] = numeric_df.isna().sum().values
    return summary


def make_category_counts(df: pd.DataFrame) -> pd.DataFrame:
    flags = [
        "molecular_design_flag",
        "doping_flag",
        "transport_decoupling_flag",
        "morphology_control_flag",
        "hybrid_composites_flag",
    ]
    rows = []
    for flag in flags:
        if flag in df.columns:
            rows.append({"category_flag": flag, "rows_with_flag": int(df[flag].sum()), "total_rows": len(df)})
    return pd.DataFrame(rows)


def top_table(df: pd.DataFrame, value_col: str, n: int = 20) -> pd.DataFrame:
    if value_col not in df.columns:
        return pd.DataFrame()

    display_cols = [
        "clean_row_id",
        "exact_polymer_name",
        "polymer_family",
        "dopant",
        "doping_method",
        "doping_level_value",
        "electrical_conductivity_S_cm",
        "seebeck_uV_K",
        "power_factor_reported_uW_mK2",
        "power_factor_calculated_uW_mK2",
        "ZT_reported",
        "thermal_conductivity_W_mK",
        "validation_status",
    ]
    display_cols = [c for c in display_cols if c in df.columns]
    return df.dropna(subset=[value_col]).sort_values(value_col, ascending=False)[display_cols].head(n)


def grouped_median(df: pd.DataFrame, group_col: str, value_col: str, min_count: int = 3) -> pd.DataFrame:
    if group_col not in df.columns or value_col not in df.columns:
        return pd.DataFrame()

    temp = df[[group_col, value_col]].dropna()
    if temp.empty:
        return pd.DataFrame()

    out = (
        temp.groupby(group_col)[value_col]
        .agg(["count", "median", "mean", "max"])
        .reset_index()
        .query("count >= @min_count")
        .sort_values("median", ascending=False)
    )
    return out


def potential_duplicates(df: pd.DataFrame) -> pd.DataFrame:
    subset_candidates = [
        "exact_polymer_name",
        "dopant",
        "doping_level_value",
        "temperature_K_clean",
        "electrical_conductivity_S_cm",
        "seebeck_uV_K",
        "power_factor_reported_uW_mK2",
    ]
    subset = [c for c in subset_candidates if c in df.columns]
    if not subset:
        return pd.DataFrame()
    dup_mask = df.duplicated(subset=subset, keep=False)
    return df.loc[dup_mask, ["clean_row_id"] + subset].sort_values(subset)


# -----------------------------
# 6. EDA plots
# -----------------------------


def save_missingness_plot(missingness: pd.DataFrame, output_dir: Path) -> None:
    if missingness.empty:
        return
    top = missingness.head(30).sort_values("missing_percent", ascending=True)
    fig, ax = plt.subplots(figsize=(10, 8))
    ax.barh(top["column"], top["missing_percent"])
    ax.set_xlabel("Missing values (%)")
    ax.set_ylabel("Column")
    ax.set_title("Top missing columns")
    fig.tight_layout()
    fig.savefig(output_dir / "missingness_top30.png", dpi=200)
    plt.close(fig)


def save_histogram(df: pd.DataFrame, col: str, output_dir: Path, filename: str, title: str) -> None:
    if col not in df.columns:
        return
    data = df[col].dropna()
    if len(data) < 3:
        return
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.hist(data, bins=30)
    ax.set_xlabel(col)
    ax.set_ylabel("Count")
    ax.set_title(title)
    fig.tight_layout()
    fig.savefig(output_dir / filename, dpi=200)
    plt.close(fig)


def save_boxplot(df: pd.DataFrame, group_col: str, value_col: str, output_dir: Path, filename: str, min_count: int = 3, top_n: int = 12) -> None:
    if group_col not in df.columns or value_col not in df.columns:
        return

    temp = df[[group_col, value_col]].dropna().copy()
    if temp.empty:
        return

    counts = temp[group_col].value_counts()
    valid_groups = counts[counts >= min_count].head(top_n).index.tolist()
    temp = temp[temp[group_col].isin(valid_groups)]
    if temp[group_col].nunique() < 2:
        return

    data = [temp.loc[temp[group_col] == g, value_col].values for g in valid_groups]

    fig, ax = plt.subplots(figsize=(max(9, len(valid_groups) * 0.8), 6))
    ax.boxplot(data, labels=valid_groups, showfliers=True)
    ax.set_xlabel(group_col)
    ax.set_ylabel(value_col)
    ax.set_title(f"{value_col} by {group_col}")
    ax.tick_params(axis="x", rotation=45)
    fig.tight_layout()
    fig.savefig(output_dir / filename, dpi=200)
    plt.close(fig)


def save_scatter(df: pd.DataFrame, x_col: str, y_col: str, output_dir: Path, filename: str, title: str) -> None:
    if x_col not in df.columns or y_col not in df.columns:
        return
    temp = df[[x_col, y_col]].dropna()
    if len(temp) < 3:
        return
    fig, ax = plt.subplots(figsize=(8, 6))
    ax.scatter(temp[x_col], temp[y_col], alpha=0.7)
    ax.set_xlabel(x_col)
    ax.set_ylabel(y_col)
    ax.set_title(title)
    fig.tight_layout()
    fig.savefig(output_dir / filename, dpi=200)
    plt.close(fig)


def save_pf_vs_doping(df: pd.DataFrame, output_dir: Path) -> None:
    value_col = "power_factor_reported_uW_mK2"
    if value_col not in df.columns and "power_factor_calculated_uW_mK2" in df.columns:
        value_col = "power_factor_calculated_uW_mK2"

    required = ["doping_level_value", value_col]
    if not all(c in df.columns for c in required):
        return

    temp = df[required + [c for c in ["exact_polymer_name", "dopant"] if c in df.columns]].dropna(subset=required)
    if len(temp) < 3:
        return

    fig, ax = plt.subplots(figsize=(8, 6))
    ax.scatter(temp["doping_level_value"], temp[value_col], alpha=0.7)
    ax.set_xlabel("Doping level value")
    ax.set_ylabel(value_col)
    ax.set_title("Power factor vs doping level")
    fig.tight_layout()
    fig.savefig(output_dir / "pf_vs_doping_level.png", dpi=200)
    plt.close(fig)


def make_plots(df: pd.DataFrame, missingness: pd.DataFrame, output_dir: Path) -> None:
    save_missingness_plot(missingness, output_dir)

    save_histogram(
        df,
        "power_factor_reported_uW_mK2",
        output_dir,
        "pf_reported_distribution.png",
        "Reported power factor distribution",
    )
    save_histogram(
        df,
        "ZT_reported",
        output_dir,
        "zt_reported_distribution.png",
        "Reported ZT distribution",
    )

    save_boxplot(
        df,
        "polymer_family",
        "power_factor_reported_uW_mK2",
        output_dir,
        "pf_by_polymer_family_boxplot.png",
    )
    save_boxplot(
        df,
        "dopant",
        "power_factor_reported_uW_mK2",
        output_dir,
        "pf_by_dopant_boxplot.png",
    )
    save_boxplot(
        df,
        "doping_method",
        "power_factor_reported_uW_mK2",
        output_dir,
        "pf_by_doping_method_boxplot.png",
    )

    save_scatter(
        df,
        "electrical_conductivity_S_cm",
        "seebeck_uV_K",
        output_dir,
        "seebeck_vs_conductivity.png",
        "Seebeck coefficient vs electrical conductivity",
    )
    save_scatter(
        df,
        "thermal_conductivity_W_mK",
        "ZT_reported",
        output_dir,
        "zt_vs_thermal_conductivity.png",
        "ZT vs thermal conductivity",
    )
    save_pf_vs_doping(df, output_dir)


# -----------------------------
# 7. Main pipeline
# -----------------------------


def run_pipeline(input_csv: Path, output_dir: Path) -> None:
    safe_mkdir(output_dir)
    plots_dir = output_dir / "figures"
    tables_dir = output_dir / "tables"
    safe_mkdir(plots_dir)
    safe_mkdir(tables_dir)

    print(f"Reading: {input_csv}")
    raw_df, header_row = read_dataset(input_csv)
    print(f"Detected header row: {header_row + 1}")
    print(f"Raw shape after loading: {raw_df.shape}")

    df, column_mapping = make_standard_columns(raw_df)
    df = forward_fill_metadata(df)
    df = add_numeric_columns(df)
    df = add_validation_columns(df)
    df = add_category_flags(df)
    df = add_row_ids(df)

    # Save cleaned dataset.
    cleaned_path = output_dir / "organic_te_cleaned_dataset.csv"
    df.to_csv(cleaned_path, index=False)

    # Save column mapping.
    column_mapping.to_csv(tables_dir / "column_mapping_used.csv", index=False)

    # EDA tables.
    missingness = make_missingness_report(df)
    numeric_summary = make_numeric_summary(df)
    category_counts = make_category_counts(df)
    duplicates = potential_duplicates(df)

    missingness.to_csv(tables_dir / "missingness_report.csv", index=False)
    numeric_summary.to_csv(tables_dir / "numeric_summary.csv", index=False)
    category_counts.to_csv(tables_dir / "category_flag_counts.csv", index=False)
    duplicates.to_csv(tables_dir / "potential_duplicates.csv", index=False)

    top_table(df, "power_factor_reported_uW_mK2", 20).to_csv(tables_dir / "top20_by_reported_power_factor.csv", index=False)
    top_table(df, "power_factor_calculated_uW_mK2", 20).to_csv(tables_dir / "top20_by_calculated_power_factor.csv", index=False)
    top_table(df, "ZT_reported", 20).to_csv(tables_dir / "top20_by_reported_ZT.csv", index=False)

    grouped_median(df, "polymer_family", "power_factor_reported_uW_mK2").to_csv(
        tables_dir / "median_pf_by_polymer_family.csv", index=False
    )
    grouped_median(df, "dopant", "power_factor_reported_uW_mK2").to_csv(
        tables_dir / "median_pf_by_dopant.csv", index=False
    )
    grouped_median(df, "doping_method", "power_factor_reported_uW_mK2").to_csv(
        tables_dir / "median_pf_by_doping_method.csv", index=False
    )

    # Plots.
    make_plots(df, missingness, plots_dir)

    # Text report.
    report_path = output_dir / "eda_report.txt"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("Organic Thermoelectric Polymer Dataset EDA Report\n")
        f.write("=================================================\n\n")
        f.write(f"Input file: {input_csv}\n")
        f.write(f"Detected header row: {header_row + 1}\n")
        f.write(f"Rows: {len(df)}\n")
        f.write(f"Columns: {len(df.columns)}\n\n")

        f.write("Category flag counts:\n")
        f.write(category_counts.to_string(index=False))
        f.write("\n\n")

        f.write("Validation status counts:\n")
        if "validation_status" in df.columns:
            f.write(df["validation_status"].value_counts(dropna=False).to_string())
        f.write("\n\n")

        f.write("Top 15 missing columns:\n")
        f.write(missingness.head(15).to_string(index=False))
        f.write("\n\n")

        if "power_factor_reported_uW_mK2" in df.columns:
            f.write("Reported PF summary:\n")
            f.write(df["power_factor_reported_uW_mK2"].describe().to_string())
            f.write("\n\n")

        if "ZT_reported" in df.columns:
            f.write("Reported ZT summary:\n")
            f.write(df["ZT_reported"].describe().to_string())
            f.write("\n\n")

        f.write("Main outputs:\n")
        f.write(f"- Cleaned dataset: {cleaned_path}\n")
        f.write(f"- Tables folder: {tables_dir}\n")
        f.write(f"- Figures folder: {plots_dir}\n")

    print("Done.")
    print(f"Cleaned CSV: {cleaned_path}")
    print(f"EDA report: {report_path}")
    print(f"Tables: {tables_dir}")
    print(f"Figures: {plots_dir}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Clean and run EDA on an organic thermoelectric polymer CSV dataset.")
    parser.add_argument("--input", required=True, type=Path, help="Path to your current CSV copy.")
    parser.add_argument("--output", default=Path("eda_outputs"), type=Path, help="Output folder.")
    args = parser.parse_args()

    run_pipeline(args.input, args.output)
