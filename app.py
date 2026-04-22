
import streamlit as st
import folium
from streamlit_folium import st_folium

# =========================
# Page Config
# =========================

st.set_page_config(
    page_title="Subway Impact Viewer",
    layout="wide"
)

# =========================
# Title
# =========================

st.title("Subway Impact Viewer")
st.markdown(
    "Interactive analysis of subway service, accessibility, green space access, and priority investment areas."
)

# =========================
# Placeholder map function
# (temporary — will replace later)
# =========================

def placeholder_map(title):
    m = folium.Map(
        location=[39.95, -75.16],   # Philadelphia
        zoom_start=11,
        tiles="CartoDB positron"
    )

    folium.Marker(
        location=[39.95, -75.16],
        tooltip=title
    ).add_to(m)

    return m

# =========================
# Top Tabs
# =========================

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "Base Map (Only bus)",
    "Bus Service Metrics",
    "Subway Base Map",
    "Subway Service Metrics",
    "Priority Investment Map"
])

# =========================================================
# TAB 1 — Bus Base Map
# =========================================================

# =========================================================
# TAB 1 — Bus Base Map
# =========================================================

with tab1:
    import os
    import geopandas as gpd

    st.subheader("Base Map (Only bus)")

    # =========================
    # Relative path
    # =========================

    base_dir = os.path.join(
        os.path.dirname(__file__),
        "bus_basemap"
    )

    bus_buffer_fp = os.path.join(base_dir, "bus_buffer.geojson")
    bus_green_fp = os.path.join(base_dir, "bus_green.geojson")
    total_green_fp = os.path.join(base_dir, "total_green.geojson")
    bus_stop_fp = os.path.join(base_dir, "transport_clip.shp")
    txt_fp = os.path.join(base_dir, "result_total.txt")

    # =========================
    # Read files
    # =========================

    bus_buffer = gpd.read_file(bus_buffer_fp).to_crs(epsg=4326)
    bus_green = gpd.read_file(bus_green_fp).to_crs(epsg=4326)
    total_green = gpd.read_file(total_green_fp).to_crs(epsg=4326)
    bus_stop = gpd.read_file(bus_stop_fp).to_crs(epsg=4326)

    # =========================
    # Center
    # =========================

    center = [
        bus_stop.geometry.y.mean(),
        bus_stop.geometry.x.mean()
    ]

    # =========================
    # Read summary text
    # =========================

    summary_text = ""

    if os.path.exists(txt_fp):
        with open(txt_fp, "r", encoding="utf-8") as f:
            summary_text = f.read()

    # =========================
    # Layout
    # =========================

    left_col, right_col = st.columns([4, 1])

    with left_col:

        m = folium.Map(
            location=center,
            zoom_start=11,
            tiles="CartoDB positron"
        )

        # total green (light green)
        folium.GeoJson(
            total_green,
            style_function=lambda x: {
                "fillColor": "#CFECCF",
                "color": "#CFECCF",
                "weight": 0,
                "fillOpacity": 1
            }
        ).add_to(m)

        # bus buffer (light blue)
        folium.GeoJson(
            bus_buffer,
            style_function=lambda x: {
                "fillColor": "#BFE6F8",
                "color": "#BFE6F8",
                "weight": 0,
                "fillOpacity": 0.35
            }
        ).add_to(m)

        # accessible green (dark green)
        folium.GeoJson(
            bus_green,
            style_function=lambda x: {
                "fillColor": "#1F8A3B",
                "color": "#1F8A3B",
                "weight": 0,
                "fillOpacity": 0.85
            }
        ).add_to(m)

        # bus stops (black points)
        for _, row in bus_stop.iterrows():
            geom = row.geometry
            if geom.geom_type == "Point":
                folium.CircleMarker(
                    location=[geom.y, geom.x],
                    radius=1,
                    color="black",
                    fill=True,
                    fill_color="black",
                    fill_opacity=0.2,
                    weight=1,
                    tooltip="Bus Stop"
                ).add_to(m)

        st_folium(
            m,
            width=1000,
            height=700
        )

    with right_col:
        st.subheader("Summary")

        if summary_text.strip():
            st.write(summary_text)
        else:
            st.info("No summary text found.")


# =========================================================
# TAB 2 — Bus Service Metrics
# =========================================================

with tab2:
    import os
    import geopandas as gpd
    import branca.colormap as cm

    st.subheader("Bus Service Metrics")

    # =========================
    # Relative path
    # =========================

    base_dir = os.path.join(
        os.path.dirname(__file__),
        "bus_metrics"
    )

    tracts_fp = os.path.join(
        base_dir,
        "tracts_bus_subway.geojson"
    )

    txt_fp = os.path.join(
        base_dir,
        "result_total.txt"
    )

    # =========================
    # Read files
    # =========================

    gdf = gpd.read_file(tracts_fp).to_crs(epsg=4326)

    # =========================
    # Summary text
    # =========================

    summary_text = ""

    if os.path.exists(txt_fp):
        with open(txt_fp, "r", encoding="utf-8") as f:
            summary_text = f.read()

    # =========================
    # Field labels
    # =========================

    field_labels = {
        "bus_pop": "Population Served",
        "bus_green": "Accessible Green Space",
        "bus_poor_pop": "Low-Income Population Served",
        "bus_area_share": "Share of Tract Served",
        "bus_area_acres": "Service Area (Acres)"
    }

    label_to_field = {
        v: k for k, v in field_labels.items()
    }

    percent_fields = [
        "pov_rate",
        "bus_area_share"
    ]

    # =========================
    # Create display columns
    # =========================

    for col in list(field_labels.keys()) + ["tot_pop", "pov_rate"]:
        if col in gdf.columns:
            if col in percent_fields:
                gdf[f"{col}_display"] = (
                    gdf[col].fillna(0) * 100
                ).round(1)
            else:
                gdf[f"{col}_display"] = (
                    gdf[col].fillna(0)
                ).round(0)

    # =========================
    # Center
    # =========================

    center = [
        gdf.geometry.centroid.y.mean(),
        gdf.geometry.centroid.x.mean()
    ]

    # =========================
    # Layout
    # =========================

    left_col, middle_col, right_col = st.columns([1, 4, 1])

    # =====================================================
    # LEFT — selector
    # =====================================================

    with left_col:

        st.markdown("### Metric")

        selected_label = st.selectbox(
            "Choose a tract metric",
            list(field_labels.values())
        )

        selected_field = label_to_field[
            selected_label
        ]

    # =====================================================
    # MIDDLE — map
    # =====================================================

    with middle_col:

        st.subheader(selected_label)

        data = gdf.copy()

        data = data[
            data[selected_field].notna()
        ].copy()

        vmin = float(
            data[selected_field].min()
        )

        vmax = float(
            data[selected_field].max()
        )

        if vmin == vmax:
            vmax = vmin + 1

        colormap = cm.linear.YlGnBu_09.scale(
            vmin,
            vmax
        )

        colormap.caption = selected_label

        m = folium.Map(
            location=center,
            zoom_start=11,
            tiles="CartoDB positron"
        )

        # ---------------------------------
        # Style function
        # black outline only if
        # subway_area_acres != 0
        # ---------------------------------

        def style_function(feature):

            props = feature["properties"]

            value = props.get(
                selected_field,
                None
            )

            subway_area = props.get(
                "subway_area_acres",
                0
            )

            if value is None:
                fill_color = "#dddddd"
            else:
                fill_color = colormap(value)

            # black border only for
            # subway-served tracts
            if subway_area is not None and subway_area != 0:
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

        # ---------------------------------
        # Tooltip fields
        # ---------------------------------

        tooltip_fields = [
            "GEOID",
            "tot_pop_display",
            "pov_rate_display",
            f"{selected_field}_display"
        ]

        tooltip_aliases = [
            "Tract ID:",
            "Total Population:",
            "Poverty Rate (%):",
            f"{selected_label}:"
        ]

        folium.GeoJson(
            data,
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

        st_folium(
            m,
            width=1000,
            height=700
        )

    # =====================================================
    # RIGHT — summary
    # =====================================================

    with right_col:

        st.subheader("Summary")

        if summary_text.strip():
            st.write(summary_text)
        else:
            st.info(
                "No summary text found."
            )

# =========================================================
# TAB 3 — Subway Base Map
# =========================================================

with tab3:
    import os
    import geopandas as gpd

    st.subheader("Subway Base Map")

    # =========================
    # Relative path
    # =========================

    base_dir = os.path.join(
        os.path.dirname(__file__),
        "subway_basemap"
    )

    service_area_fp = os.path.join(
        base_dir,
        "service_area_10min.geojson"
    )

    accessible_green_fp = os.path.join(
        base_dir,
        "accessible_green.geojson"
    )

    total_green_fp = os.path.join(
        base_dir,
        "total_green.geojson"
    )

    subway_station_fp = os.path.join(
        base_dir,
        "subway_stations.geojson"
    )

    txt_fp = os.path.join(
        base_dir,
        "result_total.txt"
    )

    # =========================
    # Read files
    # =========================

    service_area = gpd.read_file(
        service_area_fp
    ).to_crs(epsg=4326)

    accessible_green = gpd.read_file(
        accessible_green_fp
    ).to_crs(epsg=4326)

    total_green = gpd.read_file(
        total_green_fp
    ).to_crs(epsg=4326)

    subway_station = gpd.read_file(
        subway_station_fp
    ).to_crs(epsg=4326)

    # =========================
    # Center
    # =========================

    center = [
        subway_station.geometry.y.mean(),
        subway_station.geometry.x.mean()
    ]

    # =========================
    # Read summary text
    # =========================

    summary_text = ""

    if os.path.exists(txt_fp):
        with open(txt_fp, "r", encoding="utf-8") as f:
            summary_text = f.read()

    # =========================
    # Layout
    # =========================

    left_col, right_col = st.columns([4, 1])

    # =====================================================
    # LEFT — map
    # =====================================================

    with left_col:

        m = folium.Map(
            location=center,
            zoom_start=11,
            tiles="CartoDB positron"
        )

        # ---------------------------------
        # total green (light green)
        # ---------------------------------

        folium.GeoJson(
            total_green,
            style_function=lambda x: {
                "fillColor": "#CFECCF",
                "color": "#CFECCF",
                "weight": 0,
                "fillOpacity": 0.45
            }
        ).add_to(m)

        # ---------------------------------
        # service area (light blue)
        # ---------------------------------

        folium.GeoJson(
            service_area,
            style_function=lambda x: {
                "fillColor": "#BFE6F8",
                "color": "#BFE6F8",
                "weight": 0,
                "fillOpacity": 0.35
            }
        ).add_to(m)

        # ---------------------------------
        # accessible green (dark green)
        # ---------------------------------

        folium.GeoJson(
            accessible_green,
            style_function=lambda x: {
                "fillColor": "#1F8A3B",
                "color": "#1F8A3B",
                "weight": 0,
                "fillOpacity": 0.85
            }
        ).add_to(m)

        # ---------------------------------
        # subway stations (black points)
        # ---------------------------------

        for _, row in subway_station.iterrows():
            geom = row.geometry

            if geom.geom_type == "Point":
                folium.CircleMarker(
                    location=[geom.y, geom.x],
                    radius=4,
                    color="black",
                    fill=True,
                    fill_color="black",
                    fill_opacity=1,
                    weight=1,
                    tooltip="Subway Station"
                ).add_to(m)

        st_folium(
            m,
            width=1000,
            height=700
        )

    # =====================================================
    # RIGHT — summary
    # =====================================================

    with right_col:

        st.subheader("Summary")

        if summary_text.strip():
            st.write(summary_text)
        else:
            st.info(
                "No summary text found."
            )



# =========================================================
# TAB 4 — Subway Service Metrics
# =========================================================

with tab4:
    import os
    import geopandas as gpd
    import branca.colormap as cm

    st.subheader("Subway Service Metrics")

    # =========================
    # Relative path
    # =========================

    base_dir = os.path.join(
        os.path.dirname(__file__),
        "subway_metrics"
    )

    tracts_fp = os.path.join(
        base_dir,
        "tracts_bus_subway.geojson"
    )

    # =========================
    # Read file
    # =========================

    gdf = gpd.read_file(tracts_fp).to_crs(epsg=4326)

    # =========================
    # Field labels
    # =========================

    field_labels = {
        "subway_pop": "Population Served",
        "subway_green": "Accessible Green Space",
        "subway_poor_pop": "Low-Income Population Served",
        "improve_pop": "Population Improvement",
        "improve_green": "Green Space Improvement"
    }

    label_to_field = {
        v: k for k, v in field_labels.items()
    }

    percent_fields = [
        "pov_rate"
    ]

    # =========================
    # Create display columns
    # =========================

    for col in list(field_labels.keys()) + ["tot_pop", "pov_rate"]:
        if col in gdf.columns:
            if col in percent_fields:
                gdf[f"{col}_display"] = (
                    gdf[col].fillna(0) * 100
                ).round(1)
            else:
                gdf[f"{col}_display"] = (
                    gdf[col].fillna(0)
                ).round(0)

    # =========================
    # Center
    # =========================

    center = [
        gdf.geometry.centroid.y.mean(),
        gdf.geometry.centroid.x.mean()
    ]

    # =========================
    # Layout
    # =========================

    left_col, right_col = st.columns([1, 4])

    # =====================================================
    # LEFT — selector
    # =====================================================

    with left_col:

        st.markdown("### Metric")

        selected_label = st.selectbox(
            "Choose a subway metric",
            list(field_labels.values())
        )

        selected_field = label_to_field[
            selected_label
        ]

    # =====================================================
    # RIGHT — map
    # =====================================================

    with right_col:

        st.subheader(selected_label)

        data = gdf.copy()

        data = data[
            data[selected_field].notna()
        ].copy()

        vmin = float(
            data[selected_field].min()
        )

        vmax = float(
            data[selected_field].max()
        )

        if vmin == vmax:
            vmax = vmin + 1

        colormap = cm.linear.YlGnBu_09.scale(
            vmin,
            vmax
        )

        colormap.caption = selected_label

        m = folium.Map(
            location=center,
            zoom_start=11,
            tiles="CartoDB positron"
        )

        # ---------------------------------
        # Style function
        # black outline only if
        # subway_area_acres != 0
        # ---------------------------------

        def style_function(feature):

            props = feature["properties"]

            value = props.get(
                selected_field,
                None
            )

            subway_area = props.get(
                "subway_area_acres",
                0
            )

            if value is None:
                fill_color = "#dddddd"
            else:
                fill_color = colormap(value)

            # black border only for
            # subway-served tracts
            if subway_area is not None and subway_area != 0:
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

        # ---------------------------------
        # Tooltip fields
        # ---------------------------------

        tooltip_fields = [
            "GEOID",
            "tot_pop_display",
            "pov_rate_display",
            f"{selected_field}_display"
        ]

        tooltip_aliases = [
            "Tract ID:",
            "Total Population:",
            "Poverty Rate (%):",
            f"{selected_label}:"
        ]

        folium.GeoJson(
            data,
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

        st_folium(
            m,
            width=1050,
            height=720
        )

# =========================================================
# TAB 5 — Priority Investment Map
# =========================================================

with tab5:
    import os
    import geopandas as gpd
    import branca.colormap as cm

    st.subheader("Priority Investment Map")

    # =========================
    # Relative path
    # =========================

    base_dir = os.path.join(
        os.path.dirname(__file__),
        "priority_map"
    )

    priority_fp = os.path.join(
        base_dir,
        "priority_tracts.geojson"
    )

    subway_station_fp = os.path.join(
        base_dir,
        "subway_stations.geojson"
    )

    # =========================
    # Read files
    # =========================

    gdf = gpd.read_file(
        priority_fp
    ).to_crs(epsg=4326)

    subway_station = gpd.read_file(
        subway_station_fp
    ).to_crs(epsg=4326)

    # =========================
    # Round display fields
    # =========================

    display_fields = [
        "priority_score_100",
        "score_poverty",
        "score_income",
        "score_subway_benefit"
    ]

    for col in display_fields:
        if col in gdf.columns:
            gdf[f"{col}_display"] = (
                gdf[col].fillna(0)
                .round(1)
            )

    # =========================
    # Center
    # =========================

    center = [
        gdf.geometry.centroid.y.mean(),
        gdf.geometry.centroid.x.mean()
    ]

    # =========================
    # Layout
    # =========================

    left_col, right_col = st.columns([1.3, 4])

    # =====================================================
    # LEFT — explanation
    # =====================================================

    with left_col:

        st.markdown("## How Priority Score is Calculated")

        st.markdown("""
Priority Score is used to identify which tracts should be prioritized first for future subway-related investment.

The score combines three dimensions:

**1. Poverty Need**  
Higher poverty rate → higher priority

**2. Income Need**  
Lower median household income → higher priority

**3. Subway Benefit**  
More residents served by subway & more green space accessibility → higher priority

Each variable is normalized using Min-Max scaling to a 0–1 range. Then the final score is converted to a 0–100 scale:

**Priority Score = Poverty + Income + Subway Benefit**

A higher score means the tract has both greater social need and stronger potential subway equity benefits.
""")

    # =====================================================
    # RIGHT — map
    # =====================================================

    with right_col:

        st.subheader("Priority Score Map")

        data = gdf.copy()

        selected_field = "priority_score_100"

        vmin = float(
            data[selected_field].min()
        )

        vmax = float(
            data[selected_field].max()
        )

        if vmin == vmax:
            vmax = vmin + 1

        colormap = cm.linear.YlGnBu_09.scale(
            vmin,
            vmax
        )

        colormap.caption = "Priority Score (0–100)"

        m = folium.Map(
            location=center,
            zoom_start=11,
            tiles="CartoDB positron"
        )

        # ---------------------------------
        # Priority tract polygons
        # ---------------------------------

        def style_function(feature):

            props = feature["properties"]

            value = props.get(
                selected_field,
                None
            )

            if value is None:
                fill_color = "#dddddd"
            else:
                fill_color = colormap(value)

            return {
                "fillColor": fill_color,
                "color": "black",
                "weight": 1.2,
                "fillOpacity": 0.82
            }

        tooltip_fields = [
            "GEOID",
            "score_poverty_display",
            "score_income_display",
            "score_subway_benefit_display"
        ]

        tooltip_aliases = [
            "Tract ID:",
            "Poverty Score:",
            "Income Score:",
            "Subway Benefit Score:"
        ]

        folium.GeoJson(
            data,
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

        # ---------------------------------
        # Subway stations
        # ---------------------------------

        for _, row in subway_station.iterrows():
            geom = row.geometry

            if geom.geom_type == "Point":
                folium.CircleMarker(
                    location=[geom.y, geom.x],
                    radius=4,
                    color="black",
                    fill=True,
                    fill_color="black",
                    fill_opacity=1,
                    weight=1,
                    tooltip="Subway Station"
                ).add_to(m)

        colormap.add_to(m)

        st_folium(
            m,
            width=1050,
            height=720
        )