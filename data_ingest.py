"""Utilities to ingest and preprocess OpenPowerlifting CSV exports.

The code is defensive about column names: it will try to locate likely columns
for names, dates, lifts, equipment, federation, age, and bodyweight.
"""
from __future__ import annotations

import os
import re
from typing import Optional

import pandas as pd
import requests
from rapidfuzz import process, fuzz

KG_TO_LB = 2.20462


def _find_column(df: pd.DataFrame, patterns: list[str]) -> Optional[str]:
    cols = list(df.columns)
    lowered = [c.lower() for c in cols]
    for p in patterns:
        for i, c in enumerate(lowered):
            if p in c:
                return cols[i]
    return None


def normalize_name(name: str) -> str:
    if pd.isna(name):
        return ""
    s = str(name).strip().lower()
    # remove punctuation
    s = re.sub(r"[^a-z0-9\s]", "", s)
    s = re.sub(r"\s+", " ", s)
    return s


def download_csv(url: str, out_path: str) -> str:
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    r = requests.get(url, stream=True)
    r.raise_for_status()
    with open(out_path, "wb") as f:
        for chunk in r.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)
    return out_path


def load_and_process(csv_path: Optional[str] = None, csv_url: Optional[str] = None, cache_path: str = "data/processed.parquet", nrows: Optional[int] = None) -> pd.DataFrame:
    """Load CSV (either local path or remote URL), process columns, and return DataFrame.

    The function will cache processed data to `cache_path` to speed up reloads.
    """
    os.makedirs(os.path.dirname(cache_path) or ".", exist_ok=True)
    if os.path.exists(cache_path) and csv_path is None:
        try:
            return pd.read_parquet(cache_path)
        except Exception:
            pass

    if csv_path is None and csv_url is not None:
        csv_path = "data/raw.csv"
        download_csv(csv_url, csv_path)

    if csv_path is None:
        raise ValueError("Either csv_path or csv_url must be provided")

    df = pd.read_csv(csv_path, low_memory=False, nrows=nrows)

    # find name column
    name_col = _find_column(df, ["name", "lifter"]) or "name"
    if name_col not in df.columns:
        name_col = df.columns[0]

    # date column
    date_col = _find_column(df, ["date", "meetdate"]) or None
    if date_col:
        df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
    else:
        # try to infer
        for c in df.columns:
            if "date" in c.lower():
                date_col = c
                df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
                break

    # common lift column patterns (kg)
    squat_col = _find_column(df, ["squatkг", "squat", "best3sq", "best3sqkg", "best3sqkg"]) or _find_column(df, ["sq", "squat"]) or None
    bench_col = _find_column(df, ["bench", "best3bn", "best3bnkg"]) or None
    dead_col = _find_column(df, ["dead", "deadlift", "best3dl", "best3dlkg"]) or None
    total_col = _find_column(df, ["totalkg", "total"]) or None

    # fallback: any column containing 'kg' and squat/bench/dl keywords
    if not squat_col:
        for c in df.columns:
            if "squat" in c.lower():
                squat_col = c
                break
    if not bench_col:
        for c in df.columns:
            if "bench" in c.lower():
                bench_col = c
                break
    if not dead_col:
        for c in df.columns:
            if "dead" in c.lower() or "dl" in c.lower():
                dead_col = c
                break
    if not total_col:
        for c in df.columns:
            if c.lower().startswith("total"):
                total_col = c
                break

    # create standardized columns (kg)
    df = df.copy()
    df["Name"] = df[name_col].astype(str)
    df["NameNormalized"] = df["Name"].apply(normalize_name)

    if date_col:
        df["MeetDate"] = pd.to_datetime(df[date_col], errors="coerce")
    else:
        df["MeetDate"] = pd.NaT

    def col_to_numeric(col):
        if col and col in df.columns:
            return pd.to_numeric(df[col], errors="coerce")
        return pd.Series([pd.NA] * len(df))

    df["SquatKg"] = col_to_numeric(squat_col)
    df["BenchKg"] = col_to_numeric(bench_col)
    df["DeadliftKg"] = col_to_numeric(dead_col)
    df["TotalKg"] = col_to_numeric(total_col)

    # convert to lbs
    df["SquatLb"] = (df["SquatKg"].astype(float) * KG_TO_LB).round(2)
    df["BenchLb"] = (df["BenchKg"].astype(float) * KG_TO_LB).round(2)
    df["DeadliftLb"] = (df["DeadliftKg"].astype(float) * KG_TO_LB).round(2)
    df["TotalLb"] = (df["TotalKg"].astype(float) * KG_TO_LB).round(2)

    # equipment detection
    equip_col = _find_column(df, ["equipment", "gear"]) or None
    if equip_col and equip_col in df.columns:
        df["Equipment"] = df[equip_col].astype(str)
    else:
        df["Equipment"] = ""

    # federation / meet name / bodyweight / age
    fed_col = _find_column(df, ["federation", "fed"]) or None
    if fed_col and fed_col in df.columns:
        df["Federation"] = df[fed_col].astype(str)
    else:
        df["Federation"] = ""

    bw_col = _find_column(df, ["bodyweight", "weight", "bodywt"]) or None
    if bw_col and bw_col in df.columns:
        df["BodyweightKg"] = pd.to_numeric(df[bw_col], errors="coerce")
        df["BodyweightLb"] = (df["BodyweightKg"].astype(float) * KG_TO_LB).round(2)
    else:
        df["BodyweightKg"] = pd.NA
        df["BodyweightLb"] = pd.NA

    age_col = _find_column(df, ["age"]) or None
    if age_col and age_col in df.columns:
        df["Age"] = pd.to_numeric(df[age_col], errors="coerce")
    else:
        df["Age"] = pd.NA

    # cache processed
    try:
        df.to_parquet(cache_path, index=False)
    except Exception:
        pass

    return df


def fuzzy_search_names(df: pd.DataFrame, query: str, limit: int = 10) -> list[tuple[str, int]]:
    """Return a list of (name, score) for closest matches to query.

    Uses rapidfuzz to quickly find best matches among unique names.
    """
    names = df["Name"].dropna().unique().tolist()
    results = process.extract(query, names, scorer=fuzz.WRatio, limit=limit)
    # each result is (name, score, idx)
    return [(r[0], int(r[1])) for r in results]


if __name__ == "__main__":
    print("data_ingest module - import and call load_and_process(csv_path=...) to preprocess data")
