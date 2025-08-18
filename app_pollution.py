from flask import Flask, render_template, request
from methods import generate_plotly_plot, load_station_metadata, get_stations_for_location
from methods import generate_climatology_plot
import os
import xarray as xr

app = Flask(__name__)

DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')

# List of pollutants and their corresponding HTML map files
# The keys are the pollutant names, and the values are the corresponding HTML files
MAPS = {
    "Cd(PM10)": "Cd(PM10).html",
    "Pb(PM10)": "Pb(PM10).html",
    "As(PM10)": "As(PM10).html",
    "Ni(PM10)": "Ni(PM10).html",
    "BaA(PM10)": "BaA(PM10).html",
    "BaP(PM10)": "BaP(PM10).html",
    "BbF(PM10)": "BbF(PM10).html",
    "BjF(PM10)": "BjF(PM10).html",
    "BkF(PM10)": "BkF(PM10).html",
    "DBahA(PM10)": "DBahA_(PM10).html",
    "IP(PM10)": "IP(PM10).html",
    "Jony_PM25": "Jony_PM25.html",
    "NO2": "NO2.html",
    "PM10": "PM10.html",
    "SO2": "SO2.html",
    "PM25": "PM25.html",
    "C6H6": "C6H6.html",
    "CO": "CO.html",
    "formaldehyd": "formaldehyd.html",
    "Hg(TGM)": "HG(TGM).html",
    "NO": "NO.html",
    "O3": "O3.html"
}

# GlobaL dictionary to hold the datasets
DATASETS = {}

# load datasets from netCDF files
for pollutant in MAPS.keys():
    nc_file = os.path.join(DATA_DIR, f"{pollutant}_24g_merged.nc")
    if os.path.exists(nc_file):
        try:
            DATASETS[pollutant] = xr.open_dataset(nc_file)
            print(f"Wczytano {pollutant}")
        except Exception as e:
            print(f"❌ Błąd otwarcia {nc_file}: {e}")

metadata_file = os.path.join(DATA_DIR, 'metadata.nc')
meta = xr.open_dataset(metadata_file)
meta = meta.to_dataframe().reset_index()
meta = meta[['kod_stacji', 'miejscowość']].drop_duplicates()

def get_nc_filepath(pollutant):
    return os.path.join(DATA_DIR, f"{pollutant}_24g_merged.nc")

def get_stations_list(nc_file):
    try:
        ds = xr.open_dataset(nc_file)
        return list(ds.data_vars)
    except Exception as e:
        print(f"❌ Błąd odczytu {nc_file}: {e}")
        return []

@app.route('/', methods=['GET', 'POST'])
def index():
    selected = request.form.get('pollutant', 'PM10')
    map_file = MAPS.get(selected, 'PM10.html')

    return render_template(
        'index.html',
        selected=selected,
        map_file=map_file,
        options=MAPS.keys()
    )

@app.route('/plot', methods=['GET', 'POST'])
def plot():
    pollutant = request.values.get('pollutant', 'PM10')

    nc_file = DATASETS.get(pollutant)
    stations = list(nc_file.data_vars) if nc_file is not None else []


    selected_station = request.values.get('station', stations[0] if stations else None)

    if not stations or not selected_station:
        return "Brak dostępnych stacji lub danych.", 404

    plot_html = generate_plotly_plot(nc_file.to_dataframe(), selected_station, pollutant)

    return render_template("plot.html",
                           plot_html=plot_html,
                           selected_pollutant=pollutant,
                           selected_station=selected_station,
                           all_pollutants=list(MAPS.keys()),
                           stations=stations)

@app.route('/location_overview', methods=['GET', 'POST'])
def location_overview():
    all_locations = sorted(meta['miejscowość'].dropna().unique())

    location = request.values.get('location', all_locations[0])
    station_codes = meta[meta['miejscowość'] == location]['kod_stacji'].tolist()

    plots = {}
    any_plot_generated = False

    for pollutant in DATASETS.keys():
        nc_file = DATASETS.get(pollutant)
        try:
            html = generate_climatology_plot(nc_file, station_codes, pollutant)
            if html:
                plots[pollutant] = html
                any_plot_generated = True
        except Exception:
            pass

    return render_template("location_overview.html",
                           location=location,
                           all_locations=all_locations,
                           plots=plots,
                           any_plot_generated=any_plot_generated)

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)
