# XLG Inspector Two-Stage Experiment

This evaluation pipeline was used against DeathStarBench microservice SUTs: 
  - HotelReservation (deployed w/ Docker)
  - SocialNetwork (deployed w/ Docker swarm across 4 nodes)
Before running, generate a `targets.txt` file that follows the mixed workloads provided by DeathStarBench.
Collection scripts live in `experiments_eval`, analysis scripts live in `scripts_eval`, and outputs go under `experiments_eval/output`.

## Requirements
- The XLG-modified `vegeta` binary
- Start the SUT server on a separate VM before running the scripts.
- Set `NETEM_IFACE` for every collection run.
- Install `tc` on the LG VM and run with sudo access for client-side netem.
- Python needs `pandas`, `numpy`, `scipy`, and `matplotlib`.

Defaults:
- run duration: Stage A `10s`; Stage B baseline and conditions `30s`
- XLG trim: first `5s` plus the final window
- window size: `1s`
- normal client-side network delay: `5ms`
- degraded client-side network delay: `10ms`
- faster client-side network delay: netem delay set to `0ms`
- CPU contention: background `yes` processes; mild/mod/severe jobs come from `cpu_jobs.json`: `120/130/140` at 1000 RPS, `80/90/100` at 2000 RPS, and `40/50/60` at 3000 RPS
  - This can be changed depending on the VM and how it reacts to these background jobs
- Worker and connection bottlenecks: caps come from Stage B baseline latency plus mild/mod/severe offsets of `6ms/4ms/2ms`; Stage B ramps network delay on top of normal delay during these runs

## Full Pipeline
Run everything in order from `xlg/`:

```bash
NETEM_IFACE=<iface> \
BASELINE_RPS=3000 \
TARGET_RPS=3000 \
experiments_eval/run_full_pipeline.sh
```

`BASELINE_RPS` is used for Stage A calibration. `TARGET_RPS` is used for the Stage B healthy baseline, Stage B fault settings, and Stage B condition/fault runs.

That runs:
1. Stage A healthy collection
2. Stage A count analysis
3. Stage A threshold analysis
4. Stage B baseline collection
5. Stage B fault-setting analysis
6. Stage B condition collection
7. Stage B evaluation

It creates paired timestamped directories:

```text
experiments_eval/output/stage_a_fixed/run_<timestamp>/
experiments_eval/output/stage_b_variable/run_<timestamp>/
```
## Outputs
Stage A count analysis creates:
- `stage_a_counts.json`
- `rate`
- `rho_center_fixed`, `epsilon_fixed`

Stage A threshold analysis creates:
- `stage_a_thresholds.json`
- EMD normalizers
- `T_cpu` and `T_worker` share the healthy-window scheduler score percentile (fixed at `0.90`)

The EMD reference, normalizers, thresholds, and Stage B replay use Vegeta's `XLG-WINDOW` anomaly payloads from `xlg_windows_rps*.log`. 

Stage B fault-setting analysis creates `stage_b_reference.json` with the target rate and mild/mod/severe CPU, worker, and connection settings used for Stage B fault injection.

Stage B conditions create:
- `NORMAL`
- `SUT_DEGRADED` with client-side network delay `10ms`
- `SUT_FASTER` with client-side netem delay set to `0ms`
- `CPU_CONTENTION/mild`, `CPU_CONTENTION/mod`, `CPU_CONTENTION/severe`
- `FEW_WORKERS/mild`, `FEW_WORKERS/mod`, `FEW_WORKERS/severe` with fixed Stage B worker caps and a network-delay ramp from normal delay to normal plus `BOTTLENECK_RAMP_EXTRA_DELAY`
- `FEW_CONNECTIONS/mild`, `FEW_CONNECTIONS/mod`, `FEW_CONNECTIONS/severe` with fixed Stage B connection caps and the same network-delay ramp

Stage B evaluation uses Stage A as the calibration source:
- EMD reference distributions come from Stage A healthy runs
- EMD normalizers and thresholds come from `stage_a_thresholds.json`
- rho center and epsilon come from Stage A baseline calibration
- Stage B `stage_b_reference.json` supplies fault-injection settings, not evaluation calibration

Actual labels in the confusion matrix are ordered as:
```text
FEW_CONNECTIONS, FEW_WORKERS, CPU_CONTENTION, SUT_DEGRADED, SUT_FASTER, NORMAL
```

## Notes
Run-level prediction replays retained windows through the online diagnosis state machine. The replay starts in `NORMAL` after trimming, uses Stage A rho center for the baseline band, advances one window at a time, and latches the first terminal diagnosis. `FEW_CONNECTIONS` uses high rho with elevated connection p25, and `CPU_CONTENTION` uses high rho with elevated scheduler EMD and scheduler median; both require three consecutive matching windows. `FEW_WORKERS` requires three consecutive windows near the worker cap with scheduler or negative-pacer evidence in at least one. No whole-run aggregate override is used.
