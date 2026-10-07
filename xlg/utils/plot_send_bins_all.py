# Make sure that bin files are already converted to CSV before running this script
# can do so with vegeta if files were created using vegeta

import argparse
import base64
import csv
from datetime import datetime
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
from scipy.stats import t
import json

CSV_COLUMNS = [
    "timestamp_ns", "status", "latency_ns", "bytes_out", 
    "bytes_in", "error", "body", "attack", "seq", 
    "method", "url", "headers",
]

THRESHOLD = 0.15

EXPERIMENT_DIRS = ["06_30_26_exp_server/", "HotelReservation_results"]

CONDITIONS = [
    "NORMAL",
    "SUT_FASTER",
    "SUT_DEGRADED",
    "healthy",
    "reference"
]

def load_send_rate(path, start_time_rel_s, end_time_rel_s):
    df = pd.read_csv(path, header=None, names=CSV_COLUMNS, usecols=["timestamp_ns"])
    df["timestamp_ns"] = pd.to_numeric(df["timestamp_ns"], errors="raise")
    df = df.sort_values("timestamp_ns").reset_index(drop=True)

    start_ns = df["timestamp_ns"].iloc[0]
    df["relative_s"] = (df["timestamp_ns"] - start_ns) / 1_000_000_000.0
    max_bin = int(df["relative_s"].max())

    df["time_bin"] = df["relative_s"].astype(int)
    bins = pd.DataFrame({"time_bin": range(max_bin + 1)})

    counts = df.groupby("time_bin").size().reset_index(name="rate_req_s")

    rates = bins.merge(counts, on="time_bin", how="left").fillna({"rate_req_s": 0})
    rates["time_s"] = rates["time_bin"]
    
    return rates[(rates["time_s"] >= start_time_rel_s) & (rates["time_s"] <= end_time_rel_s)]

def load_arrival_rate(path, start_time_rel_s, end_time_rel_s):
    "loads the arrivedAt timestamp"
    rows = []
    with path.open(newline="") as f:
        for row in csv.reader(f):
            assert len(row) == len(CSV_COLUMNS), f"expected {len(CSV_COLUMNS)} columns in {path}: {row}"
            assert row[1] == "200", f"unexpected non-200 status in {path}: {row[1]}"
            body = json.loads(base64.b64decode(row[6]))
            rows.append(
                datetime.fromisoformat(body["arrived_at"].replace("Z", "+00:00")).timestamp() * 1000.0
            )
    assert rows, f"expected at least one row in {path}"
    
    first_arrival_ms = min(arrived_ms for arrived_ms in rows)

    arrivals_relative_s = []
    for arrived_ms in rows:
        elapsed_s = (arrived_ms - first_arrival_ms) / 1000.0
        arrivals_relative_s.append(elapsed_s)
        
    df = pd.DataFrame({"relative_s": arrivals_relative_s})
    max_bin = int(df["relative_s"].max())

    df["time_bin"] = df["relative_s"].astype(int)
    bins = pd.DataFrame({"time_bin": range(max_bin + 1)})

    counts = df.groupby("time_bin").size().reset_index(name="rate_req_s")

    rates = bins.merge(counts, on="time_bin", how="left").fillna({"rate_req_s": 0})
    rates["time_s"] = rates["time_bin"]

    return rates[(rates["time_s"] >= start_time_rel_s) & (rates["time_s"] <= end_time_rel_s)]

if __name__ == "__main__":
    # # recursively search for results_rps*.csv files
    # all_csv_files = []
    # for exp_dir in EXPERIMENT_DIRS:
    #     all_csv_files.extend(Path(exp_dir).rglob("results_rps*.csv"))

    # run_rates = []
    # for results_csv in all_csv_files:
    #     try:
    #         rps = int(results_csv.stem.split("_")[-1].replace("rps", ""))
    #         # check if one of the conditions is in the path
    #         if not any(cond in str(results_csv) for cond in CONDITIONS):
    #             continue
            
    #         print(f"Processing {results_csv}")
    #         binned_rates = load_send_rate(results_csv)[:-1]
    #         max_send_deviation = (rps - binned_rates["rate_req_s"].min()) / rps
    #         run_rates.append(max_send_deviation)
    #     except Exception as e:
    #         rps = 12000
    #         binned_rates = load_send_rate(results_csv)[:-1]
    #         max_send_deviation = (rps - binned_rates["rate_req_s"].min()) / rps
    #         run_rates.append(max_send_deviation)

    # values = pd.Series(run_rates, dtype=float).dropna()
    # n = len(values)

    # mean = values.mean()
    # std = values.std(ddof=1)
    # margin = t.ppf(0.975, df=n - 1) * std / n**0.5

    # print(f"Runs: {n}")
    # print(f"Mean deviation: {mean:.2%}")
    # print(f"95% CI for mean: [{mean - margin:.2%}, "
    #     f"{mean + margin:.2%}]")
    # print(f"p95 deviation: {values.quantile(0.95):.2%}")

    vegeta_csv_files = []
    vegeta_csv_files.extend(Path("phase-smooth-data").rglob("results.csv"))

    run_rates_vegeta = {"cpu_0_55": {}, "cpu_0_7": {f"run_{i}": [] for i in range(1, 11)}}
    for vegeta_csv in vegeta_csv_files:
        print(f"Processing {vegeta_csv}")
        rps = 12000
        binned_rates = load_send_rate(vegeta_csv, start_time_rel_s=0, end_time_rel_s=15)[:-1]
        max_send_deviation = (rps - binned_rates["rate_req_s"].min()) / rps

        run_name = vegeta_csv.parent.name
        if "rps_12000_0-7" in str(vegeta_csv):
            run_rates_vegeta["cpu_0_7"].setdefault(run_name, []).append(max_send_deviation)
        elif "rps_12000_0-55" in str(vegeta_csv):
            run_rates_vegeta["cpu_0_55"].setdefault(run_name, []).append(max_send_deviation)

    # print("Vegeta run rates:")
    # for key, runs in run_rates_vegeta.items():
    #     sorted_runs = dict(
    #         sorted(runs.items(), key=lambda item: int(item[0].split("_")[-1]))
    #     )
    #     print(f"{key}: {sorted_runs}")

    for key in run_rates_vegeta:
        print(f"Processing key: {key}")
        max_dev = max([max(v) for v in run_rates_vegeta[key].values() if v])
        min_dev = min([min(v) for v in run_rates_vegeta[key].values() if v])

        if "cpu_0_7" in key:
            print(f"min deviation: {min_dev:.2%}")
        elif "cpu_0_55" in key:
            print(f"max deviation: {max_dev:.2%}")

        values = pd.Series([value for run_values in run_rates_vegeta[key].values() for value in run_values], dtype=float).dropna()
        n = len(values)

        mean = values.mean()
        std = values.std(ddof=1)
        margin = t.ppf(0.975, df=n - 1) * std / n**0.5

        print(f"Runs: {n}")
        print(f"Mean deviation: {mean:.2%}")
        print(f"95% CI for mean: [{mean - margin:.2%}, "
            f"{mean + margin:.2%}]")

    # Calculate the same thing for arrivals
    run_arrivals_vegeta = {"cpu_0_55": {}, "cpu_0_7": {f"run_{i}": [] for i in range(1, 11)}}
    for vegeta_csv in vegeta_csv_files:
        print(f"Processing {vegeta_csv}")
        rps = 12000
        binned_arrivals = load_arrival_rate(vegeta_csv, start_time_rel_s=0, end_time_rel_s=15)[:-1]
        max_arrival_deviation = (rps - binned_arrivals["rate_req_s"].min()) / rps
        run_name = vegeta_csv.parent.name
        if "rps_12000_0-7" in str(vegeta_csv):
            run_arrivals_vegeta["cpu_0_7"].setdefault(run_name, []).append(max_arrival_deviation)
        elif "rps_12000_0-55" in str(vegeta_csv):
            run_arrivals_vegeta["cpu_0_55"].setdefault(run_name, []).append(max_arrival_deviation)

    # print("Vegeta run arrivals:")
    # for key, runs in run_arrivals_vegeta.items():
    #     sorted_runs = dict(
    #         sorted(runs.items(), key=lambda item: int(item[0].split("_")[-1]))
    #     )
    #     print(f"{key}: {sorted_runs}")

    for key in run_arrivals_vegeta:
        print(f"Processing key: {key}")
        max_dev = max([max(v) for v in run_arrivals_vegeta[key].values() if v])
        min_dev = min([min(v) for v in run_arrivals_vegeta[key].values() if v])

        if "cpu_0_7" in key:
            print(f"min arrival deviation: {min_dev:.2%}")
        elif "cpu_0_55" in key:
            print(f"max arrival deviation: {max_dev:.2%}")  
        
        values = pd.Series([value for run_values in run_arrivals_vegeta[key].values() for value in run_values], dtype=float).dropna()
        n = len(values)

        mean = values.mean()
        std = values.std(ddof=1)
        margin = t.ppf(0.975, df=n - 1) * std / n**0.5

        print(f"Runs: {n}")
        print(f"Mean deviation: {mean:.2%}")
        print(f"95% CI for mean: [{mean - margin:.2%}, "
            f"{mean + margin:.2%}]")

    for key in run_rates_vegeta:
        values = pd.Series([value for run_values in run_rates_vegeta[key].values() for value in run_values], dtype=float).dropna()
        print(f"Number of violations (send rate) for key {key}: {(values > THRESHOLD).sum()}")

    for key in run_arrivals_vegeta:
        values = pd.Series([value for run_values in run_arrivals_vegeta[key].values() for value in run_values], dtype=float).dropna()
        print(f"Number of violations (arrival) for key {key}: {(values > THRESHOLD).sum()}")