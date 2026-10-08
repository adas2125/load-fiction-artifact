#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from xlg_eval_common import (
    read_rate,
    retained_windows,
    round_count,
    run_dirs,
    write_json,
)

CAP_OFFSETS_MS = {
    "mild": 6.0,
    "mod": 4.0,
    "severe": 2.0,
}
DEFAULT_CPU_JOBS = {
    "mild": 32,
    "mod": 64,
    "severe": 128,
}
CPU_JOBS_BY_RATE = {
    1000: {
        "mild": 36,
        "mod": 40,
        "severe": 44,
    },
    2000: {
        "mild": 56,
        "mod": 64,
        "severe": 72,
    },
    3000: {
        "mild": 128,
        "mod": 144,
        "severe": 160,
    },
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compute Stage B fault injection settings.")
    parser.add_argument("--stage-b-dir", type=Path, required=True)
    parser.add_argument("--trim-s", type=float, default=5.0)
    return parser.parse_args()


def baseline_mean_total_latency_ms(run_list: list[Path], trim_s: float) -> float:
    total = 0.0
    count = 0
    for run_dir in run_list:
        latencies = retained_windows(run_dir, trim_s=trim_s)["avg_total_latency_ms"]
        total += float(latencies.sum())
        count += int(latencies.count())
    if count == 0:
        raise ValueError("Stage B healthy runs produced no total-latency windows")
    return total / count


def caps_from_latency(rate: int, baseline_latency_ms: float) -> dict[str, int]:
    return {
        severity: round_count(rate * (baseline_latency_ms + offset_ms) / 1000.0)
        for severity, offset_ms in CAP_OFFSETS_MS.items()
    }

def connection_caps_from_latency(rate: int, baseline_latency_ms: float, max_network_delay_ms: float = 25.0) -> dict[str, int]:
    """Hard-coded for now; keeping for simplicity.Assumes max network delay different to baseline is 25 ms."""
    MILD = 0.7
    MOD = 0.5
    SEVERE = 0.3

    output_dict = {}
    baseline_demand = rate * baseline_latency_ms / 1000
    slow_demand = rate * (baseline_latency_ms + max_network_delay_ms) / 1000
    for severity, factor in [("mild", MILD), ("mod", MOD), ("severe", SEVERE)]:
        cap = baseline_demand + factor * (slow_demand - baseline_demand)
        output_dict[severity] = round_count(cap)

    return output_dict


def cpu_jobs_for_rate(rate: int) -> dict[str, int]:
    return CPU_JOBS_BY_RATE.get(rate, DEFAULT_CPU_JOBS).copy()


def main() -> None:
    args = parse_args()
    stage_dir = args.stage_b_dir
    output = stage_dir / "stage_b_reference.json"

    # get the healthy runs for Stage B
    healthy_runs = run_dirs(stage_dir / "baseline_healthy")

    # obtain the rate
    rate = read_rate(stage_dir)
    baseline_latency_ms = baseline_mean_total_latency_ms(healthy_runs, trim_s=args.trim_s)
    caps = caps_from_latency(rate, baseline_latency_ms)
    connection_caps = connection_caps_from_latency(rate, baseline_latency_ms)
    cpu_jobs = cpu_jobs_for_rate(rate)
    print(f"baseline latency: {baseline_latency_ms:.2f} ms, caps: {caps}, rate: {rate} rps, CPU jobs: {cpu_jobs}")

    payload = {
        "rate": rate,
        "severity": {
            "connections": connection_caps,
            "cpu": cpu_jobs,
            "workers": caps.copy(),
        },
    }
    write_json(output, payload)
    print(f"Wrote {output}")


if __name__ == "__main__":
    main()
