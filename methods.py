import xarray as xr
import pandas as pd
import plotly.graph_objs as go

def generate_plotly_plot(df, kod_stacji: str, pollutant) -> str:

    UNITS = {
        "CO": "mg/m³",
        "As(PM10)": "ng/m³",
        "BaA(PM10)": "ng/m³",
        "BaP(PM10)": "ng/m³",
        "BbF(PM10)": "ng/m³",
        "BjF(PM10)": "ng/m³",
        "BkF(PM10)": "ng/m³",
        "DBahA(PM10)": "ng/m³",
        "Cd(PM10)": "ng/m³",
        "Ni(PM10)": "ng/m³",
        "IP(PM10)": "ng/m³",
        "Hg(TGM)": "ng/m³",
        "default": "µg/m³"
    }

    unit = UNITS.get(pollutant, UNITS["default"])

    if kod_stacji not in df.columns:
        return f"<p>Brak danych dla stacji {kod_stacji}</p>"

    series = df[kod_stacji].dropna()

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=series.index,
        y=series.values,
        mode='lines',
        line=dict(color='teal'),
        name=kod_stacji
    ))

    fig.update_layout(
        title = f"Średni roczny przebieg – {pollutant} ({unit})",
        xaxis_title="Data",
        yaxis_title=f"Stężenie ({unit})",
        height=400,
        margin=dict(l=40, r=40, t=60, b=40)
    )

    return fig.to_html(full_html=False)

def load_station_metadata(metadata_file):
    ds = xr.open_dataset(metadata_file)
    df = ds.to_dataframe().reset_index()
    return df[['kod_stacji', 'miejscowość']].drop_duplicates()

def get_stations_for_location(location, metadata_file):
    df = load_station_metadata(metadata_file)
    return df[df['miejscowość'] == location]['kod_stacji'].tolist()

def generate_climatology_plot(ds, station_codes, pollutant):

    available_stations = list(ds.data_vars)
    valid_stations = [s for s in station_codes if s in available_stations]

    if not valid_stations:
        return None

    ds_sel = ds[valid_stations]
    df = ds_sel.to_dataframe().reset_index()
    df_long = df.melt(id_vars=['Data'], var_name='station', value_name='value')
    df_long['day_of_year'] = df_long['Data'].dt.dayofyear
    mean_daily = df_long.groupby('day_of_year')['value'].mean().reset_index()

    UNITS = {
        "CO": "mg/m³",
        "As(PM10)": "ng/m³",
        "BaA(PM10)": "ng/m³",
        "BaP(PM10)": "ng/m³",
        "BbF(PM10)": "ng/m³",
        "BjF(PM10)": "ng/m³",
        "BkF(PM10)": "ng/m³",
        "DBahA(PM10)": "ng/m³",
        "Cd(PM10)": "ng/m³",
        "Ni(PM10)": "ng/m³",
        "IP(PM10)": "ng/m³",
        "Hg(TGM)": "ng/m³",
        "default": "µg/m³"
    }
    unit = UNITS.get(pollutant, UNITS["default"])
    title = f"Średni roczny przebieg – {pollutant} ({unit})"

    import plotly.express as px
    fig = px.line(mean_daily, x='day_of_year', y='value',
                  title=title,
                  labels={"day_of_year": "Dzień roku", "value": f"Stężenie ({unit})"})

    return fig.to_html(full_html=False)





