NYC Motor Vehicle Collisions Analytics

Rather than reading massive raw CSV files directly into memory—which crashes dashboards at scale—this project utilizes a modern decoupling pattern:

Extraction & Feature Engineering (load_data.py): Cleans dirty records, filters out uninformative categorical data (e.g., "UNKNOWN"), and engineers dynamic time features (YEAR, MONTH, CRASH HOUR).

Storage Layer (Delta Lake / Parquet): Persists data locally or on cloud storage using columnar Parquet files, structurally partitioned by [YEAR, BOROUGH] for ultra-fast disk-seek times.

Presentation Layer (present_data_visualization.py): A lightweight, lightning-fast Streamlit dashboard powered by Plotly that reads directly from the optimized data layout without dragging down system resources.

📊 Data Source & Schema
Data Catalog: Data.gov NYC Collisions  - https://catalog.data.gov/dataset/motor-vehicle-collisions-crashes?from_hint=eyJzb3J0IjoicG9wdWxhcml0eSJ9

Direct Raw CSV Feed: City of New York API - https://data.cityofnewyork.us/api/views/h9gi-nx95/rows.csv?accessType=DOWNLOAD

How to run it?
#Extract raw data and build the optimized Delta Lake partitions
python load_data.py

#Launch the analytical web dashboard
python -m streamlit run present_data_visualization.py


