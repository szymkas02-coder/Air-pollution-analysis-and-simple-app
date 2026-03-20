from flask import Flask, render_template, request, jsonify
from methods import generate_plotly_plot, generate_climatology_plot
import os
import xarray as xr

app = Flask(__name__)

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")

# ---------------------------------------------------------------------------
# Pollutant → map file mapping
# ---------------------------------------------------------------------------
MAPS: dict[str, str] = {
    "Cd(PM10)":   "Cd(PM10).html",
    "Pb(PM10)":   "Pb(PM10).html",
    "As(PM10)":   "As(PM10).html",
    "Ni(PM10)":   "Ni(PM10).html",
    "BaA(PM10)":  "BaA(PM10).html",
    "BaP(PM10)":  "BaP(PM10).html",
    "BbF(PM10)":  "BbF(PM10).html",
    "BjF(PM10)":  "BjF(PM10).html",
    "BkF(PM10)":  "BkF(PM10).html",
    "DBahA(PM10)":"DBahA_(PM10).html",
    "IP(PM10)":   "IP(PM10).html",
    "Jony_PM25":  "Jony_PM25.html",
    "NO2":        "NO2.html",
    "PM10":       "PM10.html",
    "SO2":        "SO2.html",
    "PM25":       "PM25.html",
    "C6H6":       "C6H6.html",
    "CO":         "CO.html",
    "formaldehyd":"formaldehyd.html",
    "Hg(TGM)":   "HG(TGM).html",
    "NO":         "NO.html",
    "O3":         "O3.html",
}

# ---------------------------------------------------------------------------
# Load all NetCDF datasets once at startup
# ---------------------------------------------------------------------------
DATASETS: dict[str, xr.Dataset] = {}

for pollutant in MAPS:
    nc_path = os.path.join(DATA_DIR, f"{pollutant}_24g_merged.nc")
    if os.path.exists(nc_path):
        try:
            DATASETS[pollutant] = xr.open_dataset(nc_path)
            print(f"Loaded: {pollutant}")
        except Exception as exc:
            print(f"Failed to load {nc_path}: {exc}")

# ---------------------------------------------------------------------------
# Station metadata (loaded once)
# ---------------------------------------------------------------------------
_meta_path = os.path.join(DATA_DIR, "metadata.nc")
meta = xr.open_dataset(_meta_path).to_dataframe().reset_index()
meta = meta[["kod_stacji", "miejscowość"]].drop_duplicates()

ALL_LOCATIONS: list[str] = sorted(meta["miejscowość"].dropna().unique())


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route("/", methods=["GET", "POST"])
def index():
    selected = request.form.get("pollutant", "PM10")
    map_file = MAPS.get(selected, "PM10.html")
    return render_template(
        "index.html",
        selected=selected,
        map_file=map_file,
        options=list(MAPS.keys()),
    )


@app.route("/plot", methods=["GET"])
def plot():
    pollutant = request.args.get("pollutant", "PM10")
    ds = DATASETS.get(pollutant)
    stations = list(ds.data_vars) if ds is not None else []

    selected_station = request.args.get("station", stations[0] if stations else None)

    if not stations or not selected_station:
        return "Brak dostępnych stacji lub danych.", 404

    # Pass the dataset directly — generate_plotly_plot extracts only the needed variable
    plot_html = generate_plotly_plot(ds, selected_station, pollutant)

    return render_template(
        "plot.html",
        plot_html=plot_html,
        selected_pollutant=pollutant,
        selected_station=selected_station,
        all_pollutants=list(MAPS.keys()),
        stations=stations,
    )


@app.route("/location_overview", methods=["GET"])
def location_overview():
    location = request.args.get("location", ALL_LOCATIONS[0] if ALL_LOCATIONS else "")
    station_codes = meta[meta["miejscowość"] == location]["kod_stacji"].tolist()

    # Render the page skeleton immediately; plots are loaded via AJAX (/api/climatology)
    return render_template(
        "location_overview.html",
        location=location,
        all_locations=ALL_LOCATIONS,
        station_codes=station_codes,
        all_pollutants=list(DATASETS.keys()),
    )


@app.route("/api/climatology", methods=["GET"])
def api_climatology():
    """
    AJAX endpoint — returns a single climatology plot as HTML.
    Called by location_overview.html once per pollutant, in parallel.
    This avoids blocking the initial page render with a long server-side loop.
    """
    pollutant = request.args.get("pollutant")
    station_codes = request.args.getlist("station_codes")

    if not pollutant or pollutant not in DATASETS:
        return jsonify({"html": None})

    try:
        html = generate_climatology_plot(DATASETS[pollutant], station_codes, pollutant)
    except Exception as exc:
        print(f"Climatology error ({pollutant}): {exc}")
        html = None

    return jsonify({"html": html})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
