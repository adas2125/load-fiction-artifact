# Make sure that bin files are already converted to CSV before running this script
# can do so with vegeta if files were created using vegeta

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
from scipy.stats import t

CSV_COLUMNS = [
    "timestamp_ns", "status", "latency_ns", "bytes_out", 
    "bytes_in", "error", "body", "attack", "seq", 
    "method", "url", "headers",
]

EXPERIMENT_DIRS = ["06_30_26_exp_server/", "HotelReservation_results"]

CONDITIONS = [
    "NORMAL",
    "SUT_FASTER",
    "SUT_DEGRADED",
    "healthy",
    "reference"
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
    # recursively search for results_rps*.csv files
    all_csv_files = []
    for exp_dir in EXPERIMENT_DIRS:
        all_csv_files.extend(Path(exp_dir).rglob("results_rps*.csv"))
    
    vegeta_csv_files = []
    vegeta_csv_files.extend(Path("phase-smooth-data").rglob("results.csv"))

    run_rates = []
    for results_csv in all_csv_files:
        try:
            rps = int(results_csv.stem.split("_")[-1].replace("rps", ""))
            # check if one of the conditions is in the path
            if not any(cond in str(results_csv) for cond in CONDITIONS):
                continue
            
            print(f"Processing {results_csv}")
            binned_rates = load_send_rate(results_csv)[:-1]
            max_send_deviation = (rps - binned_rates["rate_req_s"].min()) / rps
            run_rates.append(max_send_deviation)
        except Exception as e:
            rps = 12000
            binned_rates = load_send_rate(results_csv)[:-1]
            max_send_deviation = (rps - binned_rates["rate_req_s"].min()) / rps
            run_rates.append(max_send_deviation)

    values = pd.Series(run_rates, dtype=float).dropna()
    n = len(values)

    mean = values.mean()
    std = values.std(ddof=1)
    margin = t.ppf(0.975, df=n - 1) * std / n**0.5

    print(f"Runs: {n}")
    print(f"Mean deviation: {mean:.2%}")
    print(f"95% CI for mean: [{mean - margin:.2%}, "
        f"{mean + margin:.2%}]")
    print(f"p95 deviation: {values.quantile(0.95):.2%}")
    
    run_rates_vegeta = []
    for vegeta_csv in vegeta_csv_files:
        rps = 12000
        binned_rates = load_send_rate(vegeta_csv)[:-1]
        max_send_deviation = (rps - binned_rates["rate_req_s"].min()) / rps
        run_rates_vegeta.append(max_send_deviation)
    
    values_vegeta = pd.Series(run_rates_vegeta, dtype=float).dropna()
    n_vegeta = len(values_vegeta)

    mean_vegeta = values_vegeta.mean()
    std_vegeta = values_vegeta.std(ddof=1)
    margin_vegeta = t.ppf(0.975, df=n_vegeta - 1) * std_vegeta / n_vegeta**0.5

    print(f"Vegeta runs: {n_vegeta}")
    print(f"Mean deviation: {mean_vegeta:.2%}")
    print(f"95% CI for mean: [{mean_vegeta - margin_vegeta:.2%}, "
        f"{mean_vegeta + margin_vegeta:.2%}]")
    print(f"p95 deviation: {values_vegeta.quantile(0.95):.2%}")
