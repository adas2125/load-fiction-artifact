import matplotlib.pyplot as plt
import matplotlib.cm as cm
import pandas as pd
from pathlib import Path
from utils import EXP_STYLES

# defining constants, adjust to your experiment setup
INPUT_DIR = Path("output/burst_compare_01")
EXPECTED_RPS = 400
OUTPUT_FILE_NAME = "combined_arrival_rates_trimmed"  # Updated name
TRIM_START_S, TRIM_END_S = 5.0, 5.0

exp_name_to_label = {
    "conn40": "40 Connections",
    "conn100": "100 Connections"
}

# styling the plot
plt.rcParams.update({
    'font.size': 10,
    'axes.labelsize': 10,
    'xtick.labelsize': 9,
    'ytick.labelsize': 9,
    'legend.fontsize': 8, 
    'font.family': 'serif',
    'pdf.fonttype': 42, # Forces Type 1 fonts (Required by ACM)
    'ps.fonttype': 42
})

fig, ax = plt.subplots(figsize=(3.33, 2.3), layout="constrained")
experiments = list(INPUT_DIR.glob("conn*/arrival_counts.csv"))
colors = cm.get_cmap('tab10', len(experiments))

# Loop through the experiments and plot on the shared axis
for i, exp in enumerate(experiments):
    exp_name = exp.parent.name  # e.g., 'conn1', 'conn2'
    c = colors(i)               

    print(f"Processing {exp}...")
    
    # Load and prep arrival data
    df = pd.read_csv(exp)
    df["absolute_time"] = pd.to_datetime(df["timestamp"], utc=True)
    df["time_s"] = (df["absolute_time"] - df["absolute_time"].min()).dt.total_seconds()

    # Determine experiment boundaries based on raw data spans
    max_arrival_s = df["time_s"].max()

    # Filter out the first 5s and last 5s for arrivals
    df = df[(df["time_s"] >= TRIM_START_S) & (df["time_s"] <= (max_arrival_s - TRIM_END_S))].copy()
    df["time_s"] = df["time_s"] - TRIM_START_S

    # Calculate metrics on the trimmed windows
    df["arrival_rate"] = df["arrivals_interval"] / df["time_s"].diff()

    style = EXP_STYLES.get(exp.parent.name, {
        "label": exp,
        "color": "black", 
        "linestyle": "-"
    })
    ax.step(df["time_s"], df["arrival_rate"], where="post", color=style["color"], 
            linewidth=1.2, linestyle=style["linestyle"], label=f"{style['label']}")


# Format Axis
ax.set_xlabel("Time (s)")
ax.set_ylabel("Rate (req/s)")
ax.grid(True, linestyle=":", alpha=0.7)

# Ensure the Y-axis starts at 0, letting matplotlib auto-scale the ceiling for spikes
ax.set_ylim(bottom=0)

# Push the legend above the plot horizontally
ax.legend(
    loc="lower center", 
    bbox_to_anchor=(0.5, 1.02), 
    ncol=2, 
    frameon=False
)

output_base = INPUT_DIR / OUTPUT_FILE_NAME
output_base.parent.mkdir(parents=True, exist_ok=True)
png_output = output_base.with_suffix('.png')
fig.savefig(png_output, format='png', dpi=300, bbox_inches='tight', pad_inches=0.00)
print(f"Saved trimmed rates plot to {png_output}")
