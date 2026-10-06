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

    DIR = "sut_arrivals/cpu_0_55/"

    arrival_rates_k6 = []  # Collect all rates for aggregation
    for run_id in range(1, 11):
        print(f"Processing run {run_id} with start_time={START_TIME} and end_time={END_TIME}")
        csv_path = Path(DIR) / f"arrivals_{run_id}" / "arrivals.csv"
        if csv_path.exists():
            max_dev = get_arrival_rates(csv_path, start_time=START_TIME, end_time=END_TIME)
            arrival_rates_k6.append(max_dev)

    values_k6 = pd.Series(arrival_rates_k6, dtype=float).dropna()
    n_k6 = len(values_k6)

    mean_k6 = values_k6.mean()
    std_k6 = values_k6.std(ddof=1)
    margin_k6 = t.ppf(0.975, df=n_k6 - 1) * std_k6 / n_k6**0.5

    print(f"K6 runs: {n_k6}")
    print(f"Mean deviation: {mean_k6:.2%}")
    print(f"95% CI for mean: [{mean_k6 - margin_k6:.2%}, "
        f"{mean_k6 + margin_k6:.2%}]")
    print(f"p95 deviation: {values_k6.quantile(0.95):.2%}")
    