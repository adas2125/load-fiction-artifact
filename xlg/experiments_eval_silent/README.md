# XLG Inspector Silent Failures Evaluation
This directory contains scripts needed to reproduce the silent failure evaluation setup for XLG.
This evaluation framework is very similar to the one present in experiments_eval/, but with a 
few differences in how simulated network delay is handled on the path, so the failures appear
silent to aggregate-based baselines.

## ExpServer New Evaluation
Run the paired ExpServer evaluation from `xlg/`:

```bash
NETEM_IFACE=<iface> experiments_eval_silent/run_expserver_new_pipeline.sh
```

That wrapper runs paired Stage A and Stage B evaluations at `1000`, `2000`, and `3000` RPS, pins non-CPU-contention Vegeta attacks to the default evaluation CPU set, pins CPU-contention attacks and stress jobs to a constrained rate-specific CPU set, and writes results under:

```text
ExpServer_new_results/
  rps_1000/
    stage_a/
    stage_b_baseline/
      baseline_healthy/
      conditions/
      controls/
      evaluation/
  rps_2000/
  rps_3000/
```

The default ExpServer CPU set for Stage A, Stage B baseline, controls, and non-CPU-contention conditions is `0-7`. CPU-contention runs keep the constrained rate-specific sets `1000 -> 0-1`, `2000 -> 0-3`, and `3000 -> 0-7`, and both Vegeta and CPU stress jobs are pinned to that same set. This may need to be changed if CPU bottlenecks are not apparent.

The CPU-contention jobs generated in `stage_b_reference.json` are also rate-specific:

```text
1000: mild=36, mod=40, severe=44
2000: mild=56, mod=64, severe=72
3000: mild=128, mod=144, severe=160
```

The wrapper defaults to `STAGE_A_DURATION=20s`, `STAGE_B_BASELINE_DURATION=30s`, and `STAGE_B_CONDITIONS_DURATION=30s`. It also defaults `NORMAL_NETWORK_DELAY=5ms`, `DEGRADED_NETWORK_DELAY=15ms`, `FASTER_NETWORK_DELAY=0ms`, `STAGE_B_SEVERITIES="mild mod severe"`, `NUM_EVAL_RUNS=1`, `NUM_CONTROL_RUNS=3`, and `CPU_CONTENTION_START_DELAY=5s`.

## Outputs
Stage A count analysis (same as that in `experiments_eval`):
Stage A threshold analysis (same as that in `experiments_eval`):
Stage B conditions create:
- `NORMAL`
- `SUT_DEGRADED` with client-side network delay `15ms` via the wrapper (`10ms` when running the conditions script directly)
- `SUT_FASTER` with client-side netem delay set to `0ms`
- `CPU_CONTENTION/mild`, `CPU_CONTENTION/mod`, `CPU_CONTENTION/severe`
- `FEW_WORKERS/mild`, `FEW_WORKERS/mod`, `FEW_WORKERS/severe` with fixed Stage B worker caps and the staged network-delay schedule
- `FEW_CONNECTIONS/mild`, `FEW_CONNECTIONS/mod`, `FEW_CONNECTIONS/severe` with fixed Stage B connection caps and the same staged network-delay schedule

Stage B controls create:
- `controls/PATH_SCHEDULE_CONTROL` with the staged network-delay schedule and no bottleneck
- `controls/CPU_CONTROL` with fixed normal network delay and no CPU jobs

Controls are saved for inspection but excluded from evaluation
Stage B evaluation (same as `experiments_eval`)

## Notes
For `FEW_WORKERS`, `FEW_CONNECTIONS`, and `PATH_SCHEDULE_CONTROL`, Stage B applies this client-side network-delay schedule during the Vegeta run: `0-5s=5ms`, `5-9s=8ms`, `9-13s=0ms`, `13-17s=10ms`, `17-20s=0ms`, `20-24s=30ms`, `24-30s=0ms`. The attack is not paused or restarted while the delay changes.

Run-level prediction replays retained windows through the online diagnosis state machine. The replay starts in `NORMAL` after trimming, uses Stage A rho center for the baseline band, advances one window at a time, and latches the first terminal diagnosis. `FEW_CONNECTIONS` uses high rho with elevated connection p25, and `CPU_CONTENTION` uses high rho with elevated scheduler EMD and scheduler median; both require three consecutive matching windows. `FEW_WORKERS` requires three consecutive windows near the worker cap with scheduler or negative-pacer evidence in at least one. No whole-run aggregate override is used.
