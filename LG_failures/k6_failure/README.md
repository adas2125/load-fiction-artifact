# k6 Failure Experiment

## Overview

This experiment investigates whether `k6` under-sends during client-side CPU spikes when it runs against a SUT that:

- closes connections,
- uses HTTPS, and
- forces HTTP/1.1 connections.

Connection churn can cause brief CPU utilization spikes on a smaller client. If the resulting under-sending overlaps with the SUT's slow phase, fewer requests experience the slow delay and the reported latency distribution can exhibit coordinated omission. Compare CPU utilization, server arrivals, and latency percentiles to establish whether this occurs; successful completion of all iterations alone does not establish accurate arrival timing.

## Setup

This experiment requires two machines:

1. **SUT machine**: runs the HTTPS SUT instances.
2. **LG machine**: runs the `k6` load generator, comparing CPUs `0-7` with CPUs `0-55`.

The LG machine must have logical CPUs `0-55` available to `taskset`. It needs Go, Python 3 with `psutil` and `matplotlib`, and `taskset`. The SUT machine needs Go and OpenSSL; server-side plotting also needs Python 3 with `pandas` and `matplotlib`.

### Build k6 on the LG machine

Initialize the source submodule if it is not already populated:

```bash
cd ~/load-fiction-artifact
git submodule update --init --recursive LG_failures/k6_failure/k6-src
```

Build the binary where the runner expects `./k6`:

```bash
cd ~/load-fiction-artifact/LG_failures/k6_failure/k6-src
go build -o ../k6 .
cd ..
./k6 version
python3 -c 'import psutil, matplotlib'
command -v taskset
```

The LG runner does not build k6. The SUT launcher builds `bin/phase-queued-server` automatically.

### Create the TLS certificate on the SUT machine

Run the SUT commands from the directory containing `run_phase_queued_server.sh`. For the repository layout:

```bash
cd ~/load-fiction-artifact/LG_failures/k6_failure
```

Generate the following certificate and matching key **once**, before starting the servers. Replace `10.10.1.2` with the SUT IP used by the LG:

```bash
openssl req -x509 -newkey rsa:2048 -sha256 -noenc \
  -keyout key.pem -out cert.pem -days 365 \
  -subj "/CN=10.10.1.2" \
  -addext "subjectAltName=IP:10.10.1.2"

chmod 600 key.pem
```

All server instances on this machine can share `cert.pem` and `key.pem`, including instances on different ports. The launcher changes into its script directory, where the server looks for these files. Reuse the pair across both CPU profiles and keep `key.pem` out of version control. The LG runner sets `K6_INSECURE_SKIP_TLS_VERIFY=true` to accept the self-signed certificate while retaining HTTPS.

### Start five fresh SUT instances

In the paper, we do ten trials, but for this demo, you can use 5. Run each command in a separate terminal on the SUT machine. Set `ADDR` explicitly because the launcher has a different default IP and otherwise uses the same port for every `RUN_ID`.

```bash
RUN_ID=1 ./run_phase_queued_server.sh
RUN_ID=2 ./run_phase_queued_server.sh
RUN_ID=3 ./run_phase_queued_server.sh
RUN_ID=4 ./run_phase_queued_server.sh
RUN_ID=5 ./run_phase_queued_server.sh
```

## Running the Load Generator

On the LG machine, run the two CPU profiles separately from `LG_failures/k6_failure`. The examples use `https://10.10.1.2`; replace it with the SUT address. Each invocation starts at port `8080` and advances one port per run. Five runs therefore use ports `8080-8084`.

### 1. Limited CPU setup

This simulates a smaller client machine. Make sure to update the IPs.

```bash
RUNS_PER_CPU=5 CPU_PROFILE_SPEC="limited_cpu_0-7:0-7" ./run_burst_k6_with_cpu.sh
```

After this profile finishes, preserve its SUT arrival logs before restarting the servers:

```bash
# On the SUT machine, in the experiment directory:
mkdir -p sut_arrivals/cpu_0_7
cp -a arrivals_{1..5} sut_arrivals/cpu_0_7/
```

### 2. Full CPU setup

Stop the five SUT processes and restart them using the same five commands above. Each instance needs a fresh phase clock for the full-CPU profile. Restarting also overwrites the original `arrivals_*/arrivals.csv` files, which is why they must be preserved first.

On the LG machine, use all 56 logical CPUs:

```bash
RUNS_PER_CPU=5 CPU_PROFILE_SPEC="full_cpu_0-55:0-55" ./run_burst_k6_with_cpu.sh
```

Preserve the full-CPU arrivals on the SUT machine:

```bash
mkdir -p sut_arrivals/cpu_0_55
cp -a arrivals_{1..5} sut_arrivals/cpu_0_55/
```

## Expected Results Directory Structure

The LG writes results to `results/` by default:

```text
results/
  limited_cpu_0-7/run_1/ ... run_5/
  full_cpu_0-55/run_1/ ... run_5/
```

Each run contains `burst-results.json`, `cpu_utilization.csv`, `k6.log`, `run_config.txt`, `latencies.txt`, and `burst-cpu-vus.png`. The CPU monitor samples host-wide per-core utilization approximately every 100ms; the plot averages the selected CPU set.

## Checking Completion and Interpreting Latencies

At `RATE=3000` and `DURATION=60s`, expect approximately 180,000 iterations. Check `k6.log` for matching `iterations` and `http_reqs`, zero interrupted iterations, zero failed requests, passing HTTP 200 checks, and any `dropped_iterations` or insufficient-VUs warnings. An omitted dropped-iterations metric is not an explicit zero. These totals do not show whether the SUT received requests at the intended times. The server should assign approximately 6,000 requests the `2s` delay at a uniform arrival rate over its two-second slow phase, but we show this may not be the case under a limited cpu profile.


## Plotting Latency Results

On the LG machine, compare both profiles over the same filtered window:

```bash
python3 plot_latencies.py --start-after=20 --end-before=50
```

This compares `[20s, 50s)`, excluding much of the startup period. Under uniform arrivals, the slow phase represents approximately `2 / 30 = 6.67%` of this window, so both p95 and p97.5 should fall in the slow tier for an ideal arrival pattern. Under-sending during that phase can reduce its representation in the latency samples.

The script plots all runs found under `results/` and prints the mean and approximate 95% confidence interval of each profile's per-run p95 and p97.5. These filtered values differ from the whole-run values in `latencies.txt`.

## Plotting Arrivals at the SUT

On the SUT machine, the preserved arrivals should have this structure:

```text
sut_arrivals/
  cpu_0_7/arrivals_1/arrivals.csv ... arrivals_5/arrivals.csv
  cpu_0_55/arrivals_1/arrivals.csv ... arrivals_5/arrivals.csv
```

`plot_arrivals.py` defaults to ten runs. For the five-run examples above, invoke its plotting function with five runs:
`count_arrivals.py` counts the number of arrivals assigned a given delay at the SUT

Run the following ot see arrival patterns

```bash
python3 plot_arrivals.py
python3 count_arrivals.py --arrivals-dir sut_arrivals --delay-ms 2000
```
