import folium
from folium import plugins
from branca.colormap import linear as cm_linear

def get_map2(df_avg, name="mapa_stacje", with_heatmap=True):
    name = name + ".html"

    # Kolory wg średniej
    vmin = df_avg['srednia'].min()
    vmax = df_avg['srednia'].max()
    colormap = cm_linear.YlOrRd_09.scale(vmin, vmax)

    # Mapa
    m = folium.Map(location=[52.0, 19.0], zoom_start=6, control_scale=True)

    # Grupy typów stacji
    groups = {}
    for typ in df_avg['typ_stacji'].dropna().unique():
        groups[typ] = folium.FeatureGroup(name=f"Typ: {typ}", show=True)
        groups[typ].add_to(m)

    # Dodanie punktów
    for _, row in df_avg.iterrows():
        color = colormap(row['srednia'])
        popup_text = f"""
        <b>Kod stacji:</b> {row['kod_stacji']}<br>
        <b>Nazwa stacji:</b> {row['nazwa_stacji']}<br>
        <b>Data uruchomienia:</b> {row['data_uruchomienia']}<br>
        <b>Data zamknięcia:</b> {row['data_zamknięcia']}<br>
        <b>Typ stacji:</b> {row['typ_stacji']}<br>
        <b>Typ obszaru:</b> {row['typ_obszaru']}<br>
        <b>Rodzaj stacji:</b> {row['rodzaj_stacji']}<br>
        <b>Województwo:</b> {row['województwo']}<br>
        <b>Miejscowość:</b> {row['miejscowość']}<br>
        <b>Adres:</b> {row['adres']}<br>
        <b>Średnia:</b> {row['srednia']:.2f}
        """

        marker = folium.CircleMarker(
            location=[row['lat'], row['lon']],
            radius=10,
            color=color,
            fill=True,
            fill_opacity=0.8,
            popup=folium.Popup(popup_text, max_width=300),
            tooltip=f"{row['nazwa_stacji']} ({row['kod_stacji']})<br>Średnia: {row['srednia']:.2f}",
        )

        group = groups.get(row['typ_stacji'])
        if group:
            marker.add_to(group)
        else:
            marker.add_to(m)

    # Legenda
    colormap.caption = 'Średnie zanieczyszczenie'
    colormap.add_to(m)

    # Kontrola warstw
    folium.LayerControl(collapsed=False).add_to(m)

    # Zapis
    m.save(name)
    print(f"✔️ Zapisano mapę: {name}")
