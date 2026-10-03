import argparse
import re
from pathlib import Path
import matplotlib.pyplot as plt

def parse_server_log(path: Path) -> tuple[list[float], list[float]]:
    t_vals, y_vals = [], []
    
    with path.open("r", encoding="utf-8") as log:
        for line in log:
            t_match = re.search(r"\bt=\s*([0-9.]+)s\b", line)
            if not t_match:
                continue

            fields = dict(re.findall(r"\b([A-Za-z_][A-Za-z0-9_/]*)=([^\s]+)", line))
            
            if "cumulative_arrivals" in fields:
                t_vals.append(float(t_match.group(1)))
                y_vals.append(float(fields["cumulative_arrivals"]))

    return t_vals, y_vals

def plot(t: list[float], y: list[float], output: Path, ideal_rate: float) -> None:
    fig, ax = plt.subplots(figsize=(10, 5.5))
    
    ax.plot(t, y, color="#2563eb", lw=2.2, label="Cumulative arrivals")
    ax.scatter(t, y, color="#1d4ed8", s=10, alpha=0.75)
    
    if ideal_rate > 0:
        ideal = [ideal_rate * t_i for t_i in t]
        ax.plot(t, ideal, "k--", lw=1.8, label=f"Ideal rate ({ideal_rate:g}/s)")

    ax.set(xlabel="Elapsed time at SUT (s)", ylabel="Cumulative arrivals")
    ax.grid(True, ls="--", alpha=0.35)
    ax.legend(loc="upper left")
    
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, bbox_inches="tight", dpi=150)
    print(f"Wrote {output}")

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Plot cumulative request arrivals.")
    parser.add_argument("log", nargs="?", type=Path, default=Path("server.log"), help="Log to parse")
    parser.add_argument("-o", "--output", type=Path, default=Path("cumulative_arrivals.png"))
    parser.add_argument("--ideal-rate", type=float, default=2000.0, help="0 to disable")
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_args()
    t, y = parse_server_log(args.log)
    plot(t, y, args.output, args.ideal_rate)
    