import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

EXP_DIR = "socc_review_files/xlg_window_test/"

# recursively search for results_rps*.csv files
all_csv_files = list(Path(EXP_DIR).rglob("results*.csv"))
RPS = 16000

MEMORY_COLUMNS = [
    "timestamp_unix", "process", "pid", "rss_mb", "vms_mb", 
    "num_threads", "num_fds", "cpu_percent"
]

mean_rss_vegeta = []
mean_cpu_vegeta = []
mean_rss_consumer = []
mean_cpu_consumer = []
for results_csv in all_csv_files:
    print(f"Processing {results_csv}...")
    rps = int(results_csv.stem.split("_")[-1].replace("rps", ""))
    if rps == RPS and "live" in str(results_csv):
        memory_csv = results_csv.parent / f"process_usage.csv"
        memory_df = pd.read_csv(memory_csv)
        mean_rss_vegeta.append(memory_df[memory_df['process'] == 'vegeta']['rss_mb'].mean())
        mean_cpu_vegeta.append(memory_df[memory_df['process'] == 'vegeta']['cpu_percent'].mean())
        mean_rss_consumer.append(memory_df[memory_df['process'] == 'consumer']['rss_mb'].mean())
        mean_cpu_consumer.append(memory_df[memory_df['process'] == 'consumer']['cpu_percent'].mean())



print(f"Overall mean rss_mb vegeta: {sum(mean_rss_vegeta)/len(mean_rss_vegeta) if mean_rss_vegeta else 0}")
print(f"Overall mean cpu_percent vegeta: {sum(mean_cpu_vegeta)/len(mean_cpu_vegeta) if mean_cpu_vegeta else 0}")
print(f"Overall mean rss_mb consumer: {sum(mean_rss_consumer)/len(mean_rss_consumer) if mean_rss_consumer else 0}")
print(f"Overall mean cpu_percent consumer: {sum(mean_cpu_consumer)/len(mean_cpu_consumer) if mean_cpu_consumer else 0}")

