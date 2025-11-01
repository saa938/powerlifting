"""Streamlit app to visualize lifter progression over time.

Run with: streamlit run app.py
"""
from __future__ import annotations

import streamlit as st
import plotly.express as px
import pandas as pd

from data_ingest import load_and_process, fuzzy_search_names


DEFAULT_SAMPLE = "data/sample.csv"


@st.cache_data
def load_data(csv_path: str | None = None, csv_url: str | None = None) -> pd.DataFrame:
    return load_and_process(csv_path=csv_path, csv_url=csv_url, cache_path="data/processed.parquet")


def make_time_series(df: pd.DataFrame, lifter: str, lifts: list[str], unit: str) -> px.Figure:
    # filter for lifter
    sub = df[df["Name"] == lifter].dropna(subset=["MeetDate"]) if lifter else df.dropna(subset=["MeetDate"])
    if sub.empty:
        fig = px.line(title="No data for selected lifter")
        return fig

    # prepare series
    rows = []
    for _, r in sub.sort_values("MeetDate").iterrows():
        for lift in lifts:
            col = f"{lift}{'Kg' if unit=='kg' else 'Lb'}"
            if pd.notna(r.get(col)):
                rows.append({
                    "MeetDate": r["MeetDate"],
                    "Lift": lift,
                    "Weight": r.get(col),
                    "Meet": r.get("Meet", ""),
                    "Age": r.get("Age", ""),
                    "BodyweightKg": r.get("BodyweightKg", ""),
                    "Federation": r.get("Federation", ""),
                })

    if not rows:
        fig = px.line(title="No lift values available for chosen lifts/units")
        return fig

    plot_df = pd.DataFrame(rows)
    fig = px.line(plot_df, x="MeetDate", y="Weight", color="Lift", markers=True,
                  hover_data={"Meet": True, "Age": True, "BodyweightKg": True, "Federation": True})
    fig.update_layout(title=f"{lifter} — progression", xaxis_title="Date", yaxis_title=("kg" if unit=="kg" else "lb"))
    return fig


def main():
    st.set_page_config(page_title="Lifter Progression", layout="wide")
    st.title("Lifter Progression Dashboard")

    with st.sidebar:
        st.header("Data source")
        csv_url = st.text_input("OpenPowerlifting CSV URL (leave blank to use sample)", "")
        csv_path = st.text_input("Or local CSV path (optional)", "")
        if st.button("Load data"):
            st.experimental_rerun()

    csv_path = csv_path.strip() or None
    csv_url = csv_url.strip() or None

    # load data (will use cache)
    if csv_path is None and csv_url is None:
        csv_path = DEFAULT_SAMPLE

    with st.spinner("Loading and processing data..."):
        df = load_data(csv_path=csv_path, csv_url=csv_url)

    st.sidebar.markdown(f"**Rows:** {len(df):,}")

    # name search
    st.sidebar.header("Search lifter")
    query = st.sidebar.text_input("Name (fuzzy)")
    matches = []
    if query:
        matches = fuzzy_search_names(df, query, limit=12)
        st.sidebar.write("Top matches:")
        for name, score in matches:
            st.sidebar.write(f"{name} — {score}")

    name_options = df["Name"].dropna().unique().tolist()
    selected_name = st.sidebar.selectbox("Or pick from list", options=[""] + sorted(name_options), index=0)
    if query and matches:
        # prefer top match
        selected_name = matches[0][0]

    st.sidebar.header("Plot options")
    lift_checks = {
        "Squat": st.sidebar.checkbox("Squat", value=True),
        "Bench": st.sidebar.checkbox("Bench", value=True),
        "Deadlift": st.sidebar.checkbox("Deadlift", value=True),
        "Total": st.sidebar.checkbox("Total", value=False),
    }
    lifts = [k for k, v in lift_checks.items() if v]
    unit = st.sidebar.radio("Units", options=["kg", "lb"], index=0)
    equipment = st.sidebar.selectbox("Equipment filter", options=["All", "Raw", "Equipped"])

    # filter equipment naively
    display_df = df.copy()
    if equipment != "All":
        mask = display_df["Equipment"].str.lower().fillna("")
        if equipment == "Raw":
            display_df = display_df[mask == "raw" ] if "raw" in mask.unique() else display_df[mask.str.contains("raw")]
        else:
            display_df = display_df[~mask.str.contains("raw")] if len(mask)>0 else display_df

    st.header("Progression chart")
    if not selected_name:
        st.info("Please select a lifter from the sidebar or enter a fuzzy query.")
        return

    fig = make_time_series(display_df, selected_name, lifts, unit)
    st.plotly_chart(fig, use_container_width=True)

    st.sidebar.markdown("---")
    st.sidebar.markdown("Data preprocessing is performed using `data_ingest.py`. For large datasets, provide a CSV URL and the script will cache a processed parquet in `data/processed.parquet`.")


if __name__ == "__main__":
    main()
