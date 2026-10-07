import pandas as pd
import matplotlib.pyplot as plt
from scipy.stats import t
from pathlib import Path

# globals for the directories
DURATION_SECONDS = 60

def get_arrival_rates(csv_path, rps=3000, start_time=20, end_time=50):
    """Helper function to extract and average the arrival rates for a given experiment directory."""
    df = pd.read_csv(csv_path)

    # converting Timestamp to datetime and sorting just in case
    df["Timestamp"] = pd.to_datetime(df["Timestamp"])
    df = df.sort_values("Timestamp")

    start_second = df["Timestamp"].min()  # no .floor("s")

    df_rate = (
        df.set_index("Timestamp")
        .resample("1s", origin=start_second)
        .size()
        .reset_index(name="Arrivals_Per_Second")
    )

    df_rate["Relative_Seconds"] = (
        df_rate["Timestamp"] - start_second
    ).dt.total_seconds()

    df_rate = df_rate[
        (df_rate["Relative_Seconds"] >= start_time)
        & (df_rate["Relative_Seconds"] < end_time)
    ]
    
    max_arrival_deviation = (rps - df_rate["Arrivals_Per_Second"].min()) / rps

    return max_arrival_deviation


if __name__ == "__main__":
    # plotting the aggregate rates across 10 runs, trimming the startup period
    START_TIME = 20
    END_TIME = 50

    DIRS = ["sut_arrivals/cpu_0_55/", "sut_arrivals/cpu_0_7"]

    arrival_rates_k6 = {DIR: [] for DIR in DIRS}  # Collect all rates for aggregation
    for run_id in range(1, 11):
        print(f"Processing run {run_id} with start_time={START_TIME} and end_time={END_TIME}")
        for DIR in DIRS:
            csv_path = Path(DIR) / f"arrivals_{run_id}" / "arrivals.csv"
            if csv_path.exists():
                max_dev = get_arrival_rates(csv_path, start_time=START_TIME, end_time=END_TIME)
                arrival_rates_k6[DIR].append(max_dev)

    for DIR in DIRS:
        print(f"Results for {DIR}:")
        values_k6 = pd.Series(arrival_rates_k6[DIR], dtype=float).dropna()

        if DIR == "sut_arrivals/cpu_0_55/":
            max_dev = values_k6.max()
            print(f"Max deviation: {max_dev:.2%}")
        elif DIR == "sut_arrivals/cpu_0_7":
            min_dev = values_k6.min()
            print(f"Min deviation: {min_dev:.2%}")
