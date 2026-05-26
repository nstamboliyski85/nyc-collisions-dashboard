import streamlit as st
import deltalake as dl
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import os

# Set browser tab configurations
st.set_page_config(page_title="NYC Collision Analytics Hub", layout="wide")

st.title("📊 NYC Motor Vehicle Collisions Executive Hub")
st.markdown("Direct ingestion layer consuming optimized transactional Parquet data from the local Delta Lake platform.")

# 1. Establish data pathways mirroring your ETL script
base_fldr = os.path.dirname(__file__)
deltalake_path = os.path.join(base_fldr, 'deltalake', 'Motor_Vehicle_Collisions_-_Crashes')

@st.cache_data(ttl=600)
def load_delta_lake_data(path):
    dt = dl.DeltaTable(path)
    return dt.to_pandas(columns=[
        'YEAR', 'MONTH', 'CRASH HOUR', 'BOROUGH', 
        'NUMBER OF PERSONS INJURED', 'NUMBER OF PERSONS KILLED',
        'VEHICLE TYPE CODE 1', 'VEHICLE TYPE CODE 2',             
        'CONTRIBUTING FACTOR VEHICLE 1', 'CONTRIBUTING FACTOR VEHICLE 2' 
    ])

try:
    df = load_delta_lake_data(deltalake_path)
    
    # 2. Sidebar Filters Configuration
    st.sidebar.header("🔍 Global Query Parameters")
    
    # Extract unique filter items dynamically and inject the "All" choice at the top
    unique_years = sorted(df['YEAR'].unique().tolist(), reverse=True)
    available_years = ["All"] + unique_years
    selected_year = st.sidebar.selectbox("Select Reporting Year", options=available_years)
    
    # Sidebar Controls for Categorical Analysis
    st.sidebar.markdown("---")
    st.sidebar.header("📊 Categorical Parameters")
    top_n = st.sidebar.slider("Select Top 'N' Categories to Display", min_value=5, max_value=25, value=10)
    
    # Slicing Logic for "All" option vs a specific year choice
    if selected_year == "All":
        filtered_df = df
    else:
        filtered_df = df[df['YEAR'] == selected_year]
    
    # 3. High-Level Performance Metrics (KPI Boxes)
    total_crashes = len(filtered_df)
    total_injured = filtered_df['NUMBER OF PERSONS INJURED'].sum()
    total_killed = filtered_df['NUMBER OF PERSONS KILLED'].sum()
    
    kpi_col1, kpi_col2, kpi_col3 = st.columns(3)
    with kpi_col1:
        st.metric(label="💥 Total Logged Collisions", value=f"{total_crashes:,}")
    with kpi_col2:
        st.metric(label="🤕 Total Persons Injured", value=f"{total_injured:,}")
    with kpi_col3:
        st.metric(label="🚨 Total Fatalities Recorded", value=f"{total_killed:,}")
        
    st.markdown("---")
    
    # 4. Core Visualizations Grid
    chart_col1, chart_col2 = st.columns(2)
    
    with chart_col1:
        st.subheader("🏙️ Volume Distribution by Geographic Borough")
        borough_counts = filtered_df['BOROUGH'].value_counts().reset_index()
        borough_counts.columns = ['Borough', 'Accident Count']
        
        fig_borough = px.bar(
            borough_counts, 
            x='Accident Count', 
            y='Borough', 
            orientation='h',
            text_auto=',',
            color='Accident Count',
            color_continuous_scale='Reds'
        )
        fig_borough.update_layout(yaxis={'categoryorder':'total ascending'}, showlegend=False)
        st.plotly_chart(fig_borough, width='stretch')
        
    with chart_col2:
        st.subheader("⏰ Diurnal Collision Trends (Hourly Risk Profile)")
        hourly_clean = filtered_df[filtered_df['CRASH HOUR'] != -1]
        hourly_counts = hourly_clean['CRASH HOUR'].value_counts().sort_index().reset_index()
        hourly_counts.columns = ['Hour of Day', 'Total Incidents']
        
        fig_hour = px.line(
            hourly_counts, 
            x='Hour of Day', 
            y='Total Incidents',
            markers=True,
            labels={'Hour of Day': 'Hour (24h Clock)'}
        )
        fig_hour.update_traces(line_color='#d62728', line_width=3)
        fig_hour.update_layout(xaxis=dict(tickmode='linear', tick0=0, dtick=2))
        st.plotly_chart(fig_hour, width='stretch')
        
    st.markdown("---")
    
    # 5. Seasonality Heatmap Row
    st.subheader("📅 Monthly Incident Multi-Year Heatmap Grid")
    
    heatmap_data = df.groupby(['YEAR', 'MONTH']).size().unstack(fill_value=0)
    month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    heatmap_data.columns = month_names[:len(heatmap_data.columns)]
    
    fig_heat = px.imshow(
        heatmap_data,
        labels=dict(x="Month of Year", y="Historical Year", color="Crash Volume"),
        x=heatmap_data.columns,
        y=heatmap_data.index,
        color_continuous_scale='YlOrRd',
        aspect="auto"
    )
    st.plotly_chart(fig_heat, width='stretch')

    st.markdown("---")
    
    # 6. Deep-Dive Categorical Analysis Row
    st.header("🚗 Deep-Dive Categorical Segmentations")
    cat_col1, cat_col2 = st.columns(2)
    
    with cat_col1:
        st.subheader(f"🛞 Top {top_n} Vehicles Involved in Collisions")
        vehicles_combined = pd.concat([
            filtered_df['VEHICLE TYPE CODE 1'], 
            filtered_df['VEHICLE TYPE CODE 2']
        ]).reset_index(drop=True)
        
        vehicles_clean = vehicles_combined[~vehicles_combined.isin(['UNKNOWN', 'unspecified', 'Unspecified', ''])]
        top_vehicles = vehicles_clean.value_counts().head(top_n).reset_index()
        top_vehicles.columns = ['Vehicle Type', 'Total Involvements']
        
        fig_vehicle = px.bar(
            top_vehicles,
            x='Total Involvements',
            y='Vehicle Type',
            orientation='h',
            text_auto=',',
            color='Total Involvements',
            color_continuous_scale='Blues'
        )
        fig_vehicle.update_layout(yaxis={'categoryorder':'total ascending'}, showlegend=False, coloraxis_showscale=False)
        st.plotly_chart(fig_vehicle, width='stretch')
        
    with cat_col2:
        st.subheader(f"⚠️ Top {top_n} Primary Contributing Factors")
        factors_combined = pd.concat([
            filtered_df['CONTRIBUTING FACTOR VEHICLE 1'], 
            filtered_df['CONTRIBUTING FACTOR VEHICLE 2']
        ]).reset_index(drop=True)
        
        factors_clean = factors_combined[~factors_combined.isin(['Unspecified', 'UNKNOWN', 'unspecified', 'Other Electronic Device', ''])]
        top_factors = factors_clean.value_counts().head(top_n).reset_index()
        top_factors.columns = ['Contributing Factor', 'Incidents Caused']
        
        fig_factor = px.bar(
            top_factors,
            x='Incidents Caused',
            y='Contributing Factor',
            orientation='h',
            text_auto=',',
            color='Incidents Caused',
            color_continuous_scale='Oranges'
        )
        fig_factor.update_layout(yaxis={'categoryorder':'total ascending'}, showlegend=False, coloraxis_showscale=False)
        st.plotly_chart(fig_factor, width='stretch')

    st.markdown("---")

    # 7. Macro Timeline Tracking Row (New Addition)
    st.subheader("📈 Historical Progression: Total Accidents Segmented by Year")
    
    # We aggregate directly from the un-sliced master dataset 'df' 
    # to show the complete history regardless of the sidebar filter
    yearly_totals = df['YEAR'].value_counts().sort_index().reset_index()
    yearly_totals.columns = ['Year', 'Total Collisions']
    
    # Cast Year to string type so Plotly treats it as distinct labels instead of continuous integers
    yearly_totals['Year'] = yearly_totals['Year'].astype(str)
    
    fig_year_trend = px.bar(
        yearly_totals,
        x='Year',
        y='Total Collisions',
        text_auto=',',
        color='Total Collisions',
        color_continuous_scale='Purples',
        labels={'Total Collisions': 'Total Volume', 'Year': 'Data Lake Calendar Year'}
    )
    fig_year_trend.update_layout(showlegend=False, coloraxis_showscale=False)
    st.plotly_chart(fig_year_trend, width='stretch')

except Exception as data_err:
    st.error("Failed to connect to backend Delta Table storage instance.")
    st.exception(data_err)