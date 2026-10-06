# Make sure that bin files are already converted to CSV before running this script
# can do so with vegeta if files were created using vegeta

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

CSV_COLUMNS = [
    "timestamp_ns", "status", "latency_ns", "bytes_out", 
    "bytes_in", "error", "body", "attack", "seq", 
    "method", "url", "headers",
]

def load_send_rate(path):
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
    
    return rates

if __name__ == "__main__":

    EXP_DIR = "socc_review_files/xlg_window_test/"

    # recursively search for results_rps*.csv files
    all_csv_files = list(Path(EXP_DIR).rglob("results_rps*.csv"))

    run_rates = []

    for results_csv in all_csv_files:
        print(f"Processing {results_csv}...")
        rps = int(results_csv.stem.split("_")[-1].replace("rps", ""))
        if "live" in str(results_csv):
            binned_rates = load_send_rate(results_csv)[:-1]
            max_send_deviation = (rps - binned_rates["rate_req_s"].min()) / rps
            run_rates.append(max_send_deviation)

    print(run_rates)

    print(f"Mean: {sum(run_rates) / len(run_rates) if run_rates else 0}")
    print(f"STD: {pd.Series(run_rates).std() if run_rates else 0}")
