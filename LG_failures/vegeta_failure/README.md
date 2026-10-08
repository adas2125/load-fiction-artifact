### Reproducing Vegeta Failures

This experiment runs several attacks against a phase-shifting SUT. The SUT
alternates between fast and slow phases and uses a limited concurrency pool,
which also introduces queuing artifacts. The goal is to show that, with default 
Vegeta settings, the load generator (LG) can silently fail to deliver the expected 
load distribution to the SUT. This can lead to issues such as coordinated omission.

### Applying the Vegeta patch

The included `vegeta.patch` contains the Vegeta code and dependency changes
needed for this experiment. These are minimal changes for tracking and logging
worker growth over time. Apply it once to a fresh submodule checkout:

```sh
# From the artifact repository root:
git submodule update --init --recursive LG_failures/vegeta_failure/vegeta-src
cd LG_failures/vegeta_failure
git -C vegeta-src apply --check ../vegeta.patch
git -C vegeta-src apply ../vegeta.patch
```

Skip patch application if the changes are already present. Then run
`./setup_vegeta.sh` from this directory to install dependencies, generate
code, and build the local `vegeta` binary. Keep the script here; it expects
`vegeta-src/`, `attack.go`, and `lib/attack.go` alongside it.

#### 12K Vegeta Attack Against a Limited-Concurrency CPU on a Large Node

This case simulates a larger node by increasing CPU access with `taskset`.

On the SUT VM, run the following commands in separate terminals.

```sh
sudo apt-get update
sudo apt-get install -y golang-go git ca-certificates
go version

# build the server
mkdir -p bin
go build -o bin/phase-queued-server ./cmd/phase-queued-sut/main.go
```

The current instructions are for 5 runs, but in the paper, we include a total of 10 runs.
Also, make sure to override/set the ip address at which the server is listening on.

```sh
RUN_ID=1 CONCURRENCY=4800 ./run_phase_queued_server.sh
RUN_ID=2 CONCURRENCY=4800 ./run_phase_queued_server.sh
RUN_ID=3 CONCURRENCY=4800 ./run_phase_queued_server.sh
RUN_ID=4 CONCURRENCY=4800 ./run_phase_queued_server.sh
RUN_ID=5 CONCURRENCY=4800 ./run_phase_queued_server.sh
```

These commands use the `RUN_ID` variable to start the servers on different ports
and initialize them with different seeds for request-handling randomization.

On the LG VM, run the following command after setting the correct IP:

```sh
VEGETA_CPUSET="0-55"  RPS=12000 ./experiment/phase_run_queued_sut_attack.sh
```

#### 12K Vegeta Attack Against a Limited-Concurrency CPU on a Small Node

This case simulates a smaller node by decreasing CPU access with `taskset`.

On the SUT VM, run the following commands in separate terminals:

```sh
RUN_ID=1 CONCURRENCY=4800 ./run_phase_queued_server.sh
RUN_ID=2 CONCURRENCY=4800 ./run_phase_queued_server.sh
RUN_ID=3 CONCURRENCY=4800 ./run_phase_queued_server.sh
RUN_ID=4 CONCURRENCY=4800 ./run_phase_queued_server.sh
RUN_ID=5 CONCURRENCY=4800 ./run_phase_queued_server.sh
```

On the LG VM, run the following command:

```sh
VEGETA_CPUSET="0-7"  RPS=12000 ./experiment/phase_run_queued_sut_attack.sh
```

#### Analysis Scripts

After the results have been collected, this workflow assumes they are stored in
the standard format under the `phase-smooth-data/` directory.

Run the following scripts to generate the full results and figures:

```sh
# For the 12K runs in our paper, we have 10 runs
python3 experiment/plot_send_rate.py --rps=12000 --runs=10 --cpu-set=0-7
python3 experiment/plot_send_rate.py --rps=12000 --runs=10 --cpu-set=0-55

# Plots and saves CPU utilization over time
python3 display_cpu_util.py --rps=12000 --cpu-set=0-7
python3 display_cpu_util.py --rps=12000 --cpu-set=0-55

# For the 12K runs in our paper, we have 10 runs
python3 experiment/phase_compare_queued_sut_latency.py --results-csv=experiments_phase_queued_sut/rps_12000_0-7/run_1/results.csv --rps=12000 --concurrency=4800 --duration=30 --runs=10 --cpu-set=0-7

python3 experiment/phase_compare_queued_sut_latency.py --results-csv=experiments_phase_queued_sut/rps_12000_0-55/run_1/results.csv --rps=12000 --concurrency=4800 --duration=30 --runs=10 --cpu-set=0-55

# For the 12K runs, to compare queueing delay
python3 experiment/phase_compare_queued_sut_queue_delay.py --rps=12000
```
