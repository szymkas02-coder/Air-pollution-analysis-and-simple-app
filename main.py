"""
main.py — Generate NetCDF files and interactive HTML maps for all GIOŚ air pollution datasets.

Outputs (written to the current working directory):
  - <name>_merged.nc   : daily time series per station (years > 2010)
  - <name>.html        : interactive Folium map with per-station long-term means

Run:
    python main.py
"""

import xarray as xr
from read_data import read_data
from get_map2 import get_map2


# ------------------------------------------------------------------
# Dataset definitions
# ------------------------------------------------------------------

# Daily (24h) datasets — no resampling needed
DATASETS_24H = [
    "Cd(PM10)_24g", "Pb(PM10)_24g", "As(PM10)_24g", "Ni(PM10)_24g",
    "BaA(PM10)_24g", "BaP(PM10)_24g", "BbF(PM10)_24g", "BjF(PM10)_24g",
    "BkF(PM10)_24g", "DBahA(PM10)_24g", "IP(PM10)_24g", "Jony_PM25_24g",
    "NO2_24g", "PM10_24g", "SO2_24g", "PM25_24g",
]

# Hourly (1h) datasets — resampled to daily means internally
DATASETS_1H = [
    "C6H6_1g", "CO_1g", "formaldehyd_1g", "Hg(TGM)_1g",
    "NO_1g", "O3_1g",
]


def process_dataset(name: str, resample_to_daily: bool) -> None:
    """Load one dataset, save as NetCDF, and generate the HTML map."""
    print(f"\n📊 Processing: {name}")

    df_merged, df_avg = read_data(name, resample_to_daily=resample_to_daily)

    # Keep only data after 2010 to limit NetCDF file size
    df_merged = df_merged[df_merged.index.year > 2010]

    # Save time series to NetCDF
    nc_name = name.replace("_1g", "_24g")   # normalise suffix so 1h files also end in _24g
    ds = df_merged.to_xarray()
    ds.to_netcdf(f"{nc_name}_merged.nc")
    print(f"  ✔ Saved: {nc_name}_merged.nc")

    # Generate interactive map
    map_name = nc_name.replace("_24g", "")
    get_map2(df_avg, name=map_name)


def main() -> None:
    for name in DATASETS_24H:
        process_dataset(name, resample_to_daily=False)

    for name in DATASETS_1H:
        process_dataset(name, resample_to_daily=True)


if __name__ == "__main__":
    main()
