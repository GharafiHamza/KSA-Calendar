import streamlit as st
import folium
import geopandas as gpd
import pandas as pd
from streamlit_folium import folium_static
import os
from datetime import datetime, timedelta
import shapely
import random

# Add a title for better UI
st.title("Saudi Arabia EEZ Satellite Coverage Map")

# Define base directory for files
base_dir = r'C:\Users\ghara\Projects\pre-post_processing\maps\KSA-Calendar'

# Define satellite configurations (file path and revisit frequency in days)
satellite_configs = [
    {'file': os.path.join(base_dir, 'S1A_12day_reference_coverage_plan.geojson'), 'name': 'Sentinel-1A', 'revisit_frequency': 12},
    {'file': os.path.join(base_dir, 'S1C_12day_reference_coverage_plan.geojson'), 'name': 'Sentinel-1C', 'revisit_frequency': 12},
    {'file': os.path.join(base_dir, 'S2A_10day_reference_coverage_plan.geojson'), 'name': 'Sentinel-2A', 'revisit_frequency': 10},
    {'file': os.path.join(base_dir, 'S2B_10day_reference_coverage_plan.geojson'), 'name': 'Sentinel-2B', 'revisit_frequency': 10},
    {'file': os.path.join(base_dir, 'S2C_10day_reference_coverage_plan.geojson'), 'name': 'Sentinel-2C', 'revisit_frequency': 10},
]

# AOI and Landsat files
aoi_file = os.path.join(base_dir, 'saudi_arabia_eez.geojson')
landsat8_file = os.path.join(base_dir, 'landsat8_august.geojson')
landsat9_file = os.path.join(base_dir, 'landsat9_august.geojson')

# Define fixed colors for Sentinel and Landsat satellites
colors = {
    'Sentinel-1A': 'blue',
    'Sentinel-1C': 'red',
    'Sentinel-2A': 'green',
    'Sentinel-2B': 'purple',
    'Sentinel-2C': 'orange',
    'LANDSAT-8': 'cyan',
    'LANDSAT-9': 'magenta'
}

# List of colors for random assignment to other satellites
random_colors = [
    'darkgreen', 'brown', 'darkblue', 'darkred', 'pink', 'gray', 'black',
    'lightblue', 'lightgreen', 'lightred', 'beige', 'darkpurple', 'cadetblue'
]

# Function to get a random color, ensuring no duplicates for new satellites
used_colors = set(colors.values())
def get_random_color():
    available_colors = [c for c in random_colors if c not in used_colors]
    if not available_colors:
        return 'gray'  # Fallback if all colors are used
    color = random.choice(available_colors)
    used_colors.add(color)
    return color

# Load daily GeoJSON files (e.g., august_01.geojson)
def load_daily_satellite_data(selected_date, base_dir):
    date_str = selected_date.strftime('%d')
    daily_file = os.path.join(base_dir, 'KSA_comercial_coverage', f'august_{date_str}.geojson')
    if os.path.exists(daily_file):
        try:
            gdf = gpd.read_file(daily_file, engine='pyogrio')
            # Ensure CRS is EPSG:4326
            if gdf.crs is None or gdf.crs != 'EPSG:4326':
                gdf = gdf.set_crs('EPSG:4326', allow_override=True)
            # Fix invalid geometries
            gdf['geometry'] = gdf['geometry'].apply(lambda geom: shapely.make_valid(geom) if not geom.is_valid else geom)
            # Extract date from 'Date' or 'Start' column
            if 'Date' in gdf.columns:
                gdf['acquisition_date'] = pd.to_datetime(gdf['Date'], errors='coerce')
            elif 'Start' in gdf.columns:
                gdf['acquisition_date'] = pd.to_datetime(gdf['Start'], errors='coerce')
            else:
                st.warning(f"No date column found in {daily_file}. Assuming date matches selected date.")
                gdf['acquisition_date'] = pd.to_datetime(selected_date)
            gdf['satellite'] = gdf['Satellite'].fillna('Unknown')
            return gdf
        except Exception as e:
            st.warning(f"Error loading {daily_file}: {str(e)}")
            return None
    else:
        st.warning(f"Daily file {daily_file} not found.")
        return None

# Load satellite data (Sentinel-1A/1C, Sentinel-2A/2B/2C)
def load_satellite_data(configs):
    all_gdfs = []
    for config in configs:
        file = config['file']
        satellite_name = config['name']
        if os.path.exists(file):
            try:
                gdf = gpd.read_file(file, engine='pyogrio')
                if gdf.crs is None or gdf.crs != 'EPSG:4326':
                    gdf = gdf.set_crs('EPSG:4326', allow_override=True)
                gdf['geometry'] = gdf['geometry'].apply(lambda geom: shapely.make_valid(geom) if not geom.is_valid else geom)
                gdf['acquisition_date'] = pd.to_datetime(gdf['acquisition_date'], errors='coerce')
                gdf['satellite'] = satellite_name
                gdf['revisit_frequency'] = config['revisit_frequency']
                all_gdfs.append(gdf)
            except Exception as e:
                st.warning(f"Error loading {file}: {str(e)}")
        else:
            st.warning(f"File {file} not found.")
    if not all_gdfs:
        st.error("No valid satellite GeoJSON files loaded.")
        return None
    return gpd.GeoDataFrame(pd.concat(all_gdfs, ignore_index=True))

# Load AOI data
def load_aoi_data(aoi_file):
    if os.path.exists(aoi_file):
        try:
            aoi_gdf = gpd.read_file(aoi_file, engine='pyogrio')
            if aoi_gdf.crs is None or aoi_gdf.crs != 'EPSG:4326':
                aoi_gdf = aoi_gdf.set_crs('EPSG:4326', allow_override=True)
            aoi_gdf['geometry'] = aoi_gdf['geometry'].apply(lambda geom: shapely.make_valid(geom) if not geom.is_valid else geom)
            return aoi_gdf
        except Exception as e:
            st.error(f"Error loading AOI file {aoi_file}: {str(e)}")
            return None
    else:
        st.error(f"AOI file {aoi_file} not found.")
        return None

# Load Landsat data
def load_landsat_data(landsat8_file, landsat9_file):
    all_landsat_gdfs = []
    for file, satellite_name in [(landsat8_file, 'LANDSAT-8'), (landsat9_file, 'LANDSAT-9')]:
        if os.path.exists(file):
            try:
                gdf = gpd.read_file(file, engine='pyogrio')
                if gdf.crs is None or gdf.crs != 'EPSG:4326':
                    gdf = gdf.set_crs('EPSG:4326', allow_override=True)
                gdf['geometry'] = gdf['geometry'].apply(lambda geom: shapely.make_valid(geom) if not geom.is_valid else geom)
                possible_date_columns = ['acquisition_date', 'Name', 'Description', 'date']
                date_column = None
                for col in possible_date_columns:
                    if col in gdf.columns:
                        date_column = col
                        break
                if date_column:
                    gdf['acquisition_date'] = pd.to_datetime(gdf[date_column], errors='coerce')
                    if gdf['acquisition_date'].dropna().empty:
                        st.warning(f"No valid dates parsed in {file}. Assuming all polygons are valid for August.")
                else:
                    st.warning(f"No date column found in {file}. Assuming all polygons are valid for August.")
                    gdf['acquisition_date'] = pd.NaT
                gdf['satellite'] = satellite_name
                all_landsat_gdfs.append(gdf)
            except Exception as e:
                st.error(f"Error loading {file}: {str(e)}")
        else:
            st.error(f"Landsat file {file} not found.")
    if not all_landsat_gdfs:
        st.error("No valid Landsat GeoJSON files loaded.")
        return None
    return gpd.GeoDataFrame(pd.concat(all_landsat_gdfs, ignore_index=True))

# Load data
aoi_data = load_aoi_data(aoi_file)
if aoi_data is None:
    st.stop()

# Calculate original AOI area (in square kilometers)
original_area = aoi_data.to_crs(epsg=32637).geometry.area.sum() / 1_000_000  # UTM for accuracy

# Date picker
selected_date = st.date_input(
    "Select Date",
    value=datetime(2025, 8, 1).date(),
    min_value=datetime(2025, 8, 1).date(),
    max_value=datetime(2025, 8, 31).date()
)

# Load daily satellite data
daily_data = load_daily_satellite_data(selected_date, base_dir)

# Load Sentinel data
sentinel_data = load_satellite_data(satellite_configs)

# Load Landsat data
landsat_data = load_landsat_data(landsat8_file, landsat9_file)

# Create Folium map
m = folium.Map(location=[22.45276, 40.48313], zoom_start=6)

# Dictionary to store colors for daily satellites
daily_satellite_colors = {}

# Add Sentinel polygons
if sentinel_data is not None:
    modified_aoi = aoi_data.copy()  # Initialize here to avoid reinitialization
    for satellite in sentinel_data['satellite'].unique():
        feature_group = folium.FeatureGroup(name=satellite, show=True)
        sat_data = sentinel_data[sentinel_data['satellite'] == satellite]
        revisit_frequency = sat_data['revisit_frequency'].iloc[0]
        reference_date = sat_data['acquisition_date'].min().date()
        selected_date_dt = pd.to_datetime(selected_date).date()
        delta_days = (selected_date_dt - reference_date).days
        cycle_offset = delta_days % revisit_frequency
        target_date = reference_date + timedelta(days=int(cycle_offset))
        filtered_data = sat_data[sat_data['acquisition_date'].dt.date == target_date]
        if not filtered_data.empty:
            try:
                sat_union = filtered_data.geometry.unary_union
                modified_aoi['geometry'] = modified_aoi['geometry'].difference(sat_union)
                modified_aoi['geometry'] = modified_aoi['geometry'].apply(lambda geom: shapely.make_valid(geom) if not geom.is_valid else geom)
            except Exception as e:
                st.warning(f"Error computing union for {satellite} on {target_date}: {str(e)}")
        for _, row in filtered_data.iterrows():
            if row['geometry'].is_valid and not row['geometry'].is_empty:
                folium.GeoJson(
                    row['geometry'],
                    style_function=lambda x, color=colors[satellite]: {
                        'fillColor': color,
                        'color': color,
                        'weight': 2,
                        'fillOpacity': 0.5
                    },
                    popup=folium.Popup(
                        f"{satellite}<br>Date: {row['acquisition_date'].strftime('%Y-%m-%d')}<br>"
                        f"Time: {row['begin']} to {row['end']}"
                    )
                ).add_to(feature_group)
        feature_group.add_to(m)

# Add Landsat polygons if in August
if landsat_data is not None and selected_date.month == 8:
    landsat_feature_group = folium.FeatureGroup(name='Landsat', show=True)
    filtered_landsat = landsat_data[landsat_data['acquisition_date'].dt.date == selected_date]
    if filtered_landsat.empty and not landsat_data['acquisition_date'].isna().all():
        st.warning(f"No Landsat coverage found for {selected_date}.")
    else:
        filtered_landsat = landsat_data if landsat_data['acquisition_date'].isna().all() else filtered_landsat
        if not filtered_landsat.empty:
            try:
                landsat_union = filtered_landsat.geometry.unary_union
                modified_aoi['geometry'] = modified_aoi['geometry'].difference(landsat_union)
                modified_aoi['geometry'] = modified_aoi['geometry'].apply(lambda geom: shapely.make_valid(geom) if not geom.is_valid else geom)
            except Exception as e:
                st.warning(f"Error computing union for Landsat on {selected_date}: {str(e)}")
        for _, row in filtered_landsat.iterrows():
            if row['geometry'].is_valid and not row['geometry'].is_empty:
                folium.GeoJson(
                    row['geometry'],
                    style_function=lambda x, sat=row['satellite']: {
                        'fillColor': colors[sat],
                        'color': colors[sat],
                        'weight': 2,
                        'fillOpacity': 0.5
                    },
                    popup=folium.Popup(
                        f"{row['satellite']}<br>Date: {row['acquisition_date'].strftime('%Y-%m-%d') if pd.notna(row['acquisition_date']) else 'Unknown'}"
                    )
                ).add_to(landsat_feature_group)
        landsat_feature_group.add_to(m)

# Add daily satellite polygons (e.g., SAOCOM-1A, SAOCOM-1B)
if daily_data is not None:
    for satellite in daily_data['satellite'].unique():
        # Assign random color for non-Sentinel/Landsat satellites
        if satellite not in colors:
            daily_satellite_colors[satellite] = get_random_color()
        feature_group = folium.FeatureGroup(name=satellite, show=True)
        sat_data = daily_data[daily_data['satellite'] == satellite]
        filtered_data = sat_data[sat_data['acquisition_date'].dt.date == selected_date]
        if not filtered_data.empty:
            try:
                sat_union = filtered_data.geometry.unary_union
                modified_aoi['geometry'] = modified_aoi['geometry'].difference(sat_union)
                modified_aoi['geometry'] = modified_aoi['geometry'].apply(lambda geom: shapely.make_valid(geom) if not geom.is_valid else geom)
            except Exception as e:
                st.warning(f"Error computing union for {satellite} on {selected_date}: {str(e)}")
        for _, row in filtered_data.iterrows():
            if row['geometry'].is_valid and not row['geometry'].is_empty:
                # Handle Start and End as Timestamp or string
                start_time = 'Unknown'
                end_time = 'Unknown'
                if 'Start' in row and pd.notna(row['Start']):
                    if isinstance(row['Start'], str):
                        try:
                            start_time = row['Start'].split('T')[1].split('.')[0] if 'T' in row['Start'] else pd.to_datetime(row['Start']).strftime('%H:%M:%S')
                        except:
                            start_time = 'Invalid'
                    else:
                        start_time = pd.to_datetime(row['Start']).strftime('%H:%M:%S')
                if 'End' in row and pd.notna(row['End']):
                    if isinstance(row['End'], str):
                        try:
                            end_time = row['End'].split('T')[1].split('.')[0] if 'T' in row['End'] else pd.to_datetime(row['End']).strftime('%H:%M:%S')
                        except:
                            end_time = 'Invalid'
                    else:
                        end_time = pd.to_datetime(row['End']).strftime('%H:%M:%S')
                folium.GeoJson(
                    row['geometry'],
                    style_function=lambda x, color=daily_satellite_colors.get(satellite, colors.get(satellite, 'gray')): {
                        'fillColor': color,
                        'color': color,
                        'weight': 2,
                        'fillOpacity': 0.5
                    },
                    popup=folium.Popup(
                        f"{satellite}<br>Date: {row['acquisition_date'].strftime('%Y-%m-%d')}<br>"
                        f"Time: {start_time} to {end_time}"
                    )
                ).add_to(feature_group)
        feature_group.add_to(m)

# Add modified AOI to the map
aoi_feature_group = folium.FeatureGroup(name='AOI (Saudi Arabia EEZ)', show=True)
for _, row in modified_aoi.iterrows():
    if not row['geometry'].is_empty and row['geometry'].is_valid:
        folium.GeoJson(
            row['geometry'],
            style_function=lambda x: {
                'fillColor': 'yellow',
                'color': 'black',
                'weight': 2,
                'fillOpacity': 0.3
            },
            popup=folium.Popup("Saudi Arabia EEZ")
        ).add_to(aoi_feature_group)
aoi_feature_group.add_to(m)

# Add layer control
folium.LayerControl(collapsed=False).add_to(m)

# Calculate modified AOI area (in square kilometers)
modified_area = modified_aoi.to_crs(epsg=32637).geometry.area.sum() / 1_000_000

# Calculate covered percentage
if original_area > 0:
    covered_percentage = (1 - modified_area / original_area) * 100
else:
    covered_percentage = 0.0
    st.warning("Original AOI area is zero or invalid, cannot compute coverage percentage.")

# Center the map in the browser
# st.markdown(
#     """
#     <style>
#     div[data-testid="stFoliumMap"] {
#         display: block;
#         margin: 0 auto;
#         width: 1000px;
#         height: 600px;
#     }
#     .stApp {
#         max-width: 1000px;
#         margin: 0 auto;
#         padding: 0;
#         display: flex;
#         justify-content: center;
#         flex-direction: column;
#         align-items: center;
#     }
#     </style>
#     """,
#     unsafe_allow_html=True
# )

# Wrap map in a centered div
st.markdown('<div style="display: flex; justify-content: center; width: 100%; margin: 0 auto;">', unsafe_allow_html=True)
folium_static(m, width=1000, height=600)
st.markdown('</div>', unsafe_allow_html=True)

# Display covered percentage
st.metric("AOI Coverage", f"{covered_percentage:.2f}%")

# Save modified AOI button
if st.button("Save Modified AOI"):
    output_file = os.path.join(base_dir, f"aoi_{selected_date.strftime('%Y-%m-%d')}.geojson")
    try:
        modified_aoi.to_file(output_file, driver='GeoJSON')
        st.success(f"Modified AOI saved as {output_file}")
    except Exception as e:
        st.error(f"Error saving AOI: {str(e)}")