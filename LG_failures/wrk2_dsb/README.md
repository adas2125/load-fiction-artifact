# Reproducing the DeathStarBench wrk2 burst experiment

This experiment compares a target rate of 400 requests/second using 40 and 100 connections against a server with periodically increased response latency. It shows how connection limits affect request arrivals even when average throughput remains close to the target.

## 1. Repository and file locations

Start from an existing checkout of `load-fiction-artifact`. The commands below assume it is at `~/load-fiction-artifact`; adjust that path if needed.

| Location | Purpose and source |
| --- | --- |
| `load-fiction-artifact/` | Artifact repository containing setup, experiments, and plotting scripts. |
| `LG_failures/wrk2_dsb/DeathStarBench/` | Git submodule from https://github.com/delimitrou/DeathStarBench.git. |
| `DeathStarBench/wrk2/` | DeathStarBench's workload generator; compilation produces `wrk` here. |
| `DeathStarBench/wrk2/deps/luajit/` | Nested submodule from https://github.com/LuaJIT/LuaJIT.git, built automatically by the wrk2 Makefile. |
| `cmd/main.go` | Local burst server, using only Go's standard library. |
| `run_burst.sh` | Runs one connection-count experiment and collects results. |
| `plot_arrival_counts.py` | Plots server arrival rates, trimming five seconds from each end of the log. |
| `plot_burst_comparison.py` | Compares the recorded HDR latency distributions. |
| `utils.py` | Shared colors, labels, and line styles. |

This experiment uses the wrk2 generator and local Go server. It does not require deploying DeathStarBench's microservices or installing Docker.

## 2. Install dependencies and build

These instructions target Ubuntu 24.04 on an x86-64 node.

```bash
cd ~/load-fiction-artifact
sudo apt-get update
sudo apt-get install -y \
  git build-essential libssl-dev zlib1g-dev golang-go \
  python3-pandas python3-matplotlib

git submodule update --init --recursive
make -C LG_failures/wrk2_dsb/DeathStarBench/wrk2 -j4

cd LG_failures/wrk2_dsb
go build -o burst-server cmd/main.go
```

## 3. Run the 100-connection experiment

Use two terminals, both in:

```bash
cd ~/load-fiction-artifact/LG_failures/wrk2_dsb
```

In terminal 1, start the server:

```bash
./burst-server
```

Wait for `listening on :8080` before starting the generator. The server uses a 10 ms fast delay and a 200 ms slow delay. Each four-second cycle begins with a 1.5-second slow phase; timing starts with the first request. It listens on port 8080 on all available interfaces, is reachable through localhost, and records arrivals once per second in `arrival_counts.csv`.

In terminal 2, choose a new, unused run name and start the generator:

```bash
export RUN_NAME=burst_compare_01
./run_burst.sh
```

Choose an unused run name for each comparison. Keep terminal 2 open so both experiments use the same exported `RUN_NAME`.

The defaults are four threads, 30 seconds, 400 requests/second, connections=100, fixed scheduling intervals, and `http://localhost:8080/`.

After the generator finishes, wait for at least one additional server arrival-log message, then stop the server with Ctrl+C in terminal 1.

## 4. Run the 40-connection experiment

Ensure the previous server has stopped and its CSV has been archived. Restart it in terminal 1 using the same settings. Starting the server overwrites the working `arrival_counts.csv` and resets its counters and latency-cycle origin:

```bash
./burst-server
```
After it reports that it is listening, run this in terminal 2, keeping the same `RUN_NAME`:

```bash
CONNECTIONS=40 ./run_burst.sh
```

## 5. Generate the plots

Run both scripts from `LG_failures/wrk2_dsb`. Make sure paths are correct.

```bash
python3 plot_arrival_counts.py
python3 plot_burst_comparison.py
```

The run directory will contain:
- `combined_arrival_rates_trimmed.png`
- `latency_percentiles.png`
