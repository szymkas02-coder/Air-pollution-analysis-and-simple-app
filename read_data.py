import pandas as pd
import numpy as np
import glob
import os
import re


def read_data(name: str = "PM10_24g", resample_to_daily: bool = False) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Read air pollution data from GIOŚ Excel files and return merged time series + station averages.

    Parameters
    ----------
    name : str
        Dataset name matching the Excel filename suffix, e.g. "PM10_24g" or "CO_1g".
    resample_to_daily : bool
        If True, resample hourly data to daily means before further processing.
        Set to True for *_1g datasets; leave False for *_24g datasets.

    Returns
    -------
    df_merged : pd.DataFrame
        Daily time series with one column per station (indexed by canonical station code).
    df_avg : pd.DataFrame
        Per-station long-term mean joined with station metadata (coordinates, type, etc.).
    """
    root_folder = "./"
    pattern = os.path.join(root_folder, "[0-9][0-9][0-9][0-9]", f"[0-9][0-9][0-9][0-9]_{name}.xlsx")
    file_list = sorted(glob.glob(pattern))

    if not file_list:
        raise FileNotFoundError(f"No files found for pattern: {pattern}")

    df_list = []

    for path in file_list:
        try:
            print(f"Reading: {path}")

            # Extract year from path to decide how many header rows to skip
            match = re.search(r"(\d{4})", path)
            if not match:
                print(f"  Could not extract year from path, skipping: {path}")
                continue
            year = int(match.group(1))

            # Files up to 2015 have the header on row 1; later files have an extra title row
            skiprows = 0 if year <= 2015 else 1

            df = pd.read_excel(path, skiprows=skiprows, header=0, decimal=",")

            # Drop metadata rows that follow the header
            rows_to_drop = [0, 1] if year <= 2015 else [0, 1, 2, 3]
            df = df.drop(index=rows_to_drop, errors="ignore")

            # Normalise the date column and set as index
            df.rename(columns={df.columns[0]: "Data"}, inplace=True)
            df["Data"] = pd.to_datetime(df["Data"], errors="coerce")
            df.set_index("Data", inplace=True)

            df_list.append(df)

        except Exception as exc:
            print(f"  Error reading {path}: {exc}")

    if not df_list:
        raise RuntimeError(f"All files failed to load for '{name}'.")

    df_all = pd.concat(df_list, axis=0).sort_index()

    # Convert all columns to numeric, coercing unparseable values to NaN
    df_all = df_all.apply(pd.to_numeric, errors="coerce")

    # Optionally resample hourly data to daily means (required for *_1g files)
    if resample_to_daily:
        df_all = df_all.resample("D").mean()

    # ------------------------------------------------------------------
    # Load station metadata
    # ------------------------------------------------------------------
    df_meta = pd.read_excel("./meta.xlsx", decimal=",")
    df_meta.set_index("Nr", inplace=True, drop=True)
    df_meta.columns = df_meta.columns.str.strip().str.lower().str.replace(r"\s+", "_", regex=True)
    df_meta = df_meta.rename(columns={
        "stary_kod_stacji_(o_ile_inny_od_aktualnego)": "stary_kod",
        "wgs84_φ_n": "lat",
        "wgs84_λ_e": "lon",
    })

    # Build alias map: old station codes → canonical current code
    alias_map: dict[str, str] = {}
    for _, row in df_meta.iterrows():
        kod = row["kod_stacji"]
        if pd.notna(kod):
            alias_map[kod] = kod
        if pd.notna(row["stary_kod"]):
            for alias in str(row["stary_kod"]).split(","):
                alias = alias.strip()
                if alias:
                    alias_map[alias] = kod

    # Rename columns to canonical station codes
    df_renamed = df_all.rename(columns={col: alias_map.get(col, col) for col in df_all.columns})

    # Merge duplicate columns (same station under two names) by averaging
    df_merged = df_renamed.groupby(level=0, axis=1).mean(numeric_only=True)

    # ------------------------------------------------------------------
    # Compute per-station long-term mean and attach metadata
    # ------------------------------------------------------------------
    df_avg = df_merged.mean().reset_index()
    df_avg.columns = ["kod_stacji", "srednia"]
    df_avg = df_avg.merge(df_meta, on="kod_stacji", how="left")

    missing = df_avg[df_avg[["lat", "lon"]].isna().any(axis=1)]
    if not missing.empty:
        print("⚠️  Stations without coordinates (dropped):")
        print(missing[["kod_stacji"]].to_string(index=False))

    df_avg = df_avg.dropna(subset=["lat", "lon"])

    return df_merged, df_avg
