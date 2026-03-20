import xarray as xr
import pandas as pd
import plotly.graph_objs as go
import plotly.express as px

# Units for each pollutant; anything not listed defaults to µg/m³
UNITS: dict[str, str] = {
    "CO":        "mg/m³",
    "As(PM10)":  "ng/m³",
    "BaA(PM10)": "ng/m³",
    "BaP(PM10)": "ng/m³",
    "BbF(PM10)": "ng/m³",
    "BjF(PM10)": "ng/m³",
    "BkF(PM10)": "ng/m³",
    "DBahA(PM10)":"ng/m³",
    "Cd(PM10)":  "ng/m³",
    "Ni(PM10)":  "ng/m³",
    "IP(PM10)":  "ng/m³",
    "Hg(TGM)":   "ng/m³",
}
DEFAULT_UNIT = "µg/m³"


def get_unit(pollutant: str) -> str:
    return UNITS.get(pollutant, DEFAULT_UNIT)


def generate_plotly_plot(ds: xr.Dataset, kod_stacji: str, pollutant: str) -> str:
    """
    Generate an interactive Plotly time-series plot for a single station.

    Parameters
    ----------
    ds : xr.Dataset
        Dataset for the given pollutant (variables = station codes).
    kod_stacji : str
        Station code to plot.
    pollutant : str
        Pollutant name (used for axis labels and title).
    """
    unit = get_unit(pollutant)

    if kod_stacji not in ds.data_vars:
        return f"<p>Brak danych dla stacji {kod_stacji}</p>"

    # Extract only the needed variable — much faster than ds.to_dataframe()
    series = ds[kod_stacji].to_series().dropna()

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=series.index,
        y=series.values,
        mode="lines",
        line=dict(color="teal"),
        name=kod_stacji,
    ))
    fig.update_layout(
        title=f"{pollutant} ({unit}) – {kod_stacji}",
        xaxis_title="Data",
        yaxis_title=f"Stężenie ({unit})",
        height=400,
        margin=dict(l=40, r=40, t=60, b=40),
    )
    return fig.to_html(full_html=False, include_plotlyjs="cdn")


def generate_climatology_plot(ds: xr.Dataset, station_codes: list[str], pollutant: str) -> str | None:
    """
    Generate a day-of-year climatology plot averaged across all valid stations
    at a given location.

    Parameters
    ----------
    ds : xr.Dataset
        Dataset for the given pollutant.
    station_codes : list[str]
        Station codes belonging to the selected location.
    pollutant : str
        Pollutant name.

    Returns
    -------
    HTML string or None if no valid stations found.
    """
    valid_stations = [s for s in station_codes if s in ds.data_vars]
    if not valid_stations:
        return None

    # Stack only the needed variables into a single DataArray, then average
    da = ds[valid_stations].to_array(dim="station")          # (station, Data)
    station_mean = da.mean(dim="station")                    # (Data,)
    series = station_mean.to_series().dropna()

    doy_mean = series.groupby(series.index.dayofyear).mean()

    unit = get_unit(pollutant)
    fig = px.line(
        x=doy_mean.index,
        y=doy_mean.values,
        title=f"Średni roczny przebieg – {pollutant} ({unit})",
        labels={"x": "Dzień roku", "y": f"Stężenie ({unit})"},
    )
    # Return plot without bundling Plotly JS — loaded once from CDN in base.html
    return fig.to_html(full_html=False, include_plotlyjs=False)
