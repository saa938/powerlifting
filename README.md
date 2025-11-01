# Lifter Progression Dashboard (OpenPowerlifting data)

This project provides a simple Streamlit dashboard to visualize lifter progression over time using OpenPowerlifting CSV exports.

Features:
- Ingest and preprocess OpenPowerlifting CSV (date parsing, name normalization, kg/lb conversions)
- Fuzzy search/autocomplete for lifter names
- Select lifts to plot: squat, bench, deadlift, total
- Toggle equipment (raw/equipped) and units (kg/lb)
- Interactive Plotly time-series chart with meet/tooltips

Quick start

1. Create a virtual environment and install dependencies:

```cmd
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

2. Run the Streamlit app:

```cmd
streamlit run app.py
```

Notes
- The ingestion code attempts to detect common column names used in OpenPowerlifting CSVs. If your CSV uses different column names, you may need to map them manually in `data_ingest.py`.
- For large CSVs, the script caches a processed parquet file in `data/processed.parquet`.

Where to get data
- The OpenPowerlifting CSV exports are documented at https://openpowerlifting.gitlab.io/opl-csv/ and the official site is https://www.openpowerlifting.org/
