
import os
import geopandas as gpd
import folium
import branca.colormap as cm
import streamlit as st
from streamlit_folium import st_folium

# =========================
# Page config
# =========================
st.set_page_config(
    page_title="Green Access & Tract Scores",
    layout="wide"
)

# =========================
# Paths
# =========================
base_dir = r"D:\Desktop\musa\practicum\w8_web"

subway_fp = os.path.join(base_dir, "subway_stations.geojson")
service_fp = os.path.join(base_dir, "service_area_10min.geojson")
green_fp = os.path.join(base_dir, "accessible_green.geojson")
tracts_fp = os.path.join(base_dir, "tracts.geojson")
txt_fp = os.path.join(base_dir, "result_total.txt")

# =========================
# Field labels
# =========================
field_labels = {
    "tot_pop": "Total Population",
    "med_hh_income": "Median Household Income",
    "pov_rate": "Poverty Rate",
    "served_pop_est": "Population Served",
    "served_poor_pop": "Low-Income Population Served",
    "green_access": "Green Access Score",
    "green_access_pc": "Green Access per Capita",
    "served_share": "Share of Population Served"
}

metric_fields = list(field_labels.keys())

# reverse lookup
label_to_field = {v: k for k, v in field_labels.items()}

# fields that should display as percentages in tooltip
percent_fields = ["pov_rate", "green_access", "green_access_pc", "served_share"]

# =========================
# Load data
# =========================
@st.cache_data
def load_data():
    subway = gpd.read_file(subway_fp).to_crs(epsg=4326)
    service = gpd.read_file(service_fp).to_crs(epsg=4326)
    green = gpd.read_file(green_fp).to_crs(epsg=4326)
    tracts = gpd.read_file(tracts_fp).to_crs(epsg=4326)

    # keep mapping fields numeric
    for col in metric_fields:
        if col in tracts.columns:
            tracts[col] = tracts[col].astype(float)

    # create rounded display fields for tooltip
    for col in metric_fields:
        if col in tracts.columns:
            if col in percent_fields:
                tracts[f"{col}_display"] = (tracts[col] * 100).round(0).fillna(0).astype(int)
            else:
                tracts[f"{col}_display"] = tracts[col].round(0).fillna(0).astype(int)

    return subway, service, green, tracts

subway, service_area, green, tracts = load_data()

# =========================
# Center
# =========================
# use projected CRS to avoid centroid warning
tracts_proj = tracts.to_crs(epsg=3857)
center_geom = tracts_proj.unary_union.centroid
center_geom = gpd.GeoSeries([center_geom], crs=3857).to_crs(epsg=4326).iloc[0]
center = [center_geom.y, center_geom.x]

# =========================
# Read summary text
# =========================
summary_text = ""
if os.path.exists(txt_fp):
    with open(txt_fp, "r", encoding="utf-8") as f:
        summary_text = f.read()

# =========================
# Map 1: Green + Subway Service Area
# =========================
def make_map_1():
    m = folium.Map(location=center, zoom_start=11, tiles="CartoDB positron")

    # service area: semi-transparent blue, no border
    folium.GeoJson(
        service_area,
        name="10-min Service Area",
        style_function=lambda x: {
            "fillColor": "#4A90E2",
            "color": "#4A90E2",
            "weight": 0,
            "fillOpacity": 0.35
        }
    ).add_to(m)

    # accessible green: green polygons
    folium.GeoJson(
        green,
        name="Accessible Green Space",
        style_function=lambda x: {
            "fillColor": "#2E8B57",
            "color": "#2E8B57",
            "weight": 0,
            "fillOpacity": 0.75
        }
    ).add_to(m)

    # subway stations: black dots
    for _, row in subway.iterrows():
        geom = row.geometry
        if geom is not None and geom.geom_type == "Point":
            folium.CircleMarker(
                location=[geom.y, geom.x],
                radius=4,
                color="black",
                fill=True,
                fill_color="black",
                fill_opacity=1,
                weight=1
            ).add_to(m)

    return m

# =========================
# Map 2: Choropleth for tract scores
# =========================
def make_map_2(selected_field):
    data = tracts.copy()
    data = data[data[selected_field].notna()].copy()

    vmin = float(data[selected_field].min())
    vmax = float(data[selected_field].max())

    # avoid colormap failure if all values are the same
    if vmin == vmax:
        vmax = vmin + 1

    colormap = cm.linear.YlGnBu_09.scale(vmin, vmax)
    colormap.caption = field_labels[selected_field]

    m = folium.Map(location=center, zoom_start=11, tiles="CartoDB positron")

    def style_function(feature):
        props = feature["properties"]
        value = props.get(selected_field, None)
        served_value = props.get("served_pop_est", 0)

        if value is None:
            fill_color = "#cccccc"
        else:
            fill_color = colormap(value)

        # outline only for tracts with served_pop_est != 0
        if served_value is not None and served_value != 0:
            line_color = "black"
            line_weight = 1.8
        else:
            line_color = "transparent"
            line_weight = 0

        return {
            "fillColor": fill_color,
            "color": line_color,
            "weight": line_weight,
            "fillOpacity": 0.8
        }

    tooltip_fields = []
    tooltip_aliases = []

    if "GEOID" in data.columns:
        tooltip_fields.append("GEOID")
        tooltip_aliases.append("Tract ID:")

    display_field = f"{selected_field}_display"
    if display_field in data.columns:
        tooltip_fields.append(display_field)
        if selected_field in percent_fields:
            tooltip_aliases.append(field_labels[selected_field] + " (%):")
        else:
            tooltip_aliases.append(field_labels[selected_field] + ":")
    else:
        tooltip_fields.append(selected_field)
        tooltip_aliases.append(field_labels[selected_field] + ":")

    folium.GeoJson(
        data,
        name=field_labels[selected_field],
        style_function=style_function,
        tooltip=folium.GeoJsonTooltip(
            fields=tooltip_fields,
            aliases=tooltip_aliases,
            localize=True,
            sticky=False,
            labels=True
        ),
        highlight_function=lambda x: {
            "weight": 2.5,
            "color": "#333333",
            "fillOpacity": 0.95
        }
    ).add_to(m)

    colormap.add_to(m)
    return m

# =========================
# Title
# =========================
st.title("Green Access and Tract Score Viewer")

# =========================
# Top tabs
# =========================
tab1, tab2 = st.tabs(["Green Space & Subway Service Area", "Tract Scores"])

# -------------------------
# Tab 1
# -------------------------
with tab1:
    left_col, right_col = st.columns([3, 1])

    with left_col:
        st.subheader("Green Space and 10-Minute Subway Service Area")
        m1 = make_map_1()
        st_folium(m1, width=900, height=650)

    with right_col:
        st.subheader("Summary")
        if summary_text.strip():
            st.write(summary_text)
        else:
            st.info("No summary text found in result_total.txt")

# -------------------------
# Tab 2
# -------------------------
with tab2:
    left_col, right_col = st.columns([1, 4])

    with left_col:
        st.subheader("Metric")
        selected_label = st.selectbox(
            "Choose a tract metric",
            list(field_labels.values())
        )
        selected_field = label_to_field[selected_label]

    with right_col:
        st.subheader(selected_label)
        m2 = make_map_2(selected_field)
        st_folium(m2, width=1000, height=700)
