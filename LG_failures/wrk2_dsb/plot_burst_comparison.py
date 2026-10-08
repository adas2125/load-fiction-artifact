import math
import re
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
from utils import EXP_STYLES

# Hardcoded constants (replace to your specific run directory)
RUN_DIR = Path("output/burst_compare_01")
TARGET_RUNS = [
    ("conn40", "40 Connections"),
    ("conn100", "100 Connections")
]
OUTPUT_FILE_NAME = "latency_percentiles" # Removed extension to save both formats

def percentile_to_axis(p):
    if p <= 0:
        return 0.0
    if p >= 1:
        return 6.0
    return min(-math.log10(1.0 - p), 6.0)

# Paper style settings for consistent figure appearance
plt.rcParams.update({
    'font.size': 10,
    'axes.labelsize': 10,
    'xtick.labelsize': 9,
    'ytick.labelsize': 9,
    'legend.fontsize': 9,
    'font.family': 'serif',
    'pdf.fonttype': 42, # Forces Type 1 fonts (Required by ACM)
    'ps.fonttype': 42
})

# 3.33 inches is the exact width of a single column in the ACM sigconf template
fig, ax = plt.subplots(figsize=(3.33, 2.3))
hdr_pattern = re.compile(r"^\s*(?P<val>\d+(?:\.\d+)?)\s+(?P<pct>\d+(?:\.\d+)?)\s+")

# Plot Latency Distributions
for folder_name, label in TARGET_RUNS:
    hdr_file = RUN_DIR / folder_name / "hdr_latency.txt"
    print(f"Processing {hdr_file} for {label}...")

    style = EXP_STYLES.get(folder_name, {
        "label": folder_name, 
        "color": "black", 
        "linestyle": "-"
    })
        
    # Extract latency rows
    rows = []
    with hdr_file.open() as f:
        for line in f:
            match = hdr_pattern.match(line)
            if match:
                rows.append((float(match.group("val")), float(match.group("pct"))))
                
    df = pd.DataFrame(rows, columns=["latency", "percentile"]).drop_duplicates()
    df["axis_val"] = df["percentile"].apply(percentile_to_axis)

    # Plot using the dictionary values
    ax.step(df["axis_val"], df["latency"], 
            where="post", 
            linewidth=1.2, 
            color=style["color"], 
            linestyle=style["linestyle"], 
            label=f"{style['label']}")

# Format the plot (Title removed for LaTeX \caption inclusion)
ax.set_xlabel("Percentile")
ax.set_ylabel("Latency (ms)")
ax.set_xticks([0, 1, 2, 3, 6])
ax.set_xticklabels(["0%", "90%", "99%", "99.9%", "Max"])
ax.grid(True, linestyle=":", alpha=0.7)
ax.set_ylim(bottom=0)

# Legend
ax.legend(
    loc="lower center", 
    bbox_to_anchor=(0.5, 1.02), 
    ncol=2, 
    frameon=False
)

output_base = RUN_DIR / OUTPUT_FILE_NAME
output_base.parent.mkdir(parents=True, exist_ok=True)

png_output = output_base.with_suffix('.png')
fig.savefig(png_output, format='png', dpi=300, bbox_inches="tight")
plt.close(fig)
print(f"Plot successfully saved to {png_output}")
