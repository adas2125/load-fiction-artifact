# Reproducing the h2load HTTP/2 Stream Concurrency Experiment

This experiment measures how a server-side cap on concurrent HTTP/2 streams affects request throughput and arrival rates. The h2load client sends a target of **100 requests/second over 20 connections** to a Go HTTP/2 server. The server runs once with its default stream limit and once each with `max-streams` set to **100, 200, 256 and 300**.

## Contents

1. [Hardware and software](#1-hardware-and-software)
2. [Install dependencies and build](#2-install-dependencies-and-build)
3. [Run the experiments](#3-run-the-experiments)
4. [Generate the plots](#4-generate-the-plots)

---

## 1. Hardware and software

The experiment uses two nodes: a **Load Generator (LG)** and a **Server**. Both ran on the **Clemson CloudLab** cluster with the same bare-metal hardware.

### Hardware (per node)

| Component        | Detail                                              |
|------------------|-----------------------------------------------------|
| Processor        | Intel E5-2660v2                                     |
| CPU speed        | 2200 MHz                                            |
| CPU architecture | 64-bit, 2 sockets, 10 cores/socket, 2 threads/core  |
| System memory    | 256 GB (262144 MB)                                  |
| Dom0 memory      | 8192 MB                                             |

### Software

| Software          | Version          | Node           |
|-------------------|------------------|----------------|
| Go                | 1.27.1 linux/amd64 | Server       |
| nghttp2 (h2load)  | 1.69.0           | Load Generator |

### The server under test

The server is a single file, `<git folder>/main.go`. It uses only the Go standard library and serves cleartext HTTP/2 (native h2c) and HTTP/1.1 on the same port. It switches between two phases on a repeating cycle. The cycle starts when the first request arrives.

| Phase | Duration (`-slow-dur` / `-fast-dur`) | Delay per request (`-slow-delay` / `-fast-delay`) |
|-------|--------------------------------------|---------------------------------------------------|
| SLOW  | 10 s                                 | 10 s                                              |
| FAST  | 15 s                                 | 0 s                                               |

Server flags used in this experiment:

| Flag            | Default | Meaning                                         |
|-----------------|---------|-------------------------------------------------|
| `-addr`         | `:8080` | Listen address                                  |
| `-max-streams`  | `50000` | Max concurrent HTTP/2 streams per connection    |

About once per second, the server writes a line like this to **stderr**:

```
t=12.001s phase_now=FAST cumulative_arrivals=1200
```

The commands below redirect stderr to `load_test.log`, which the plotting script reads.

---

## 2. Install dependencies and build

Go is needed on the **Server node**. h2load is needed on the **Load Generator node**.

### 2.1 Install Go 1.27.1 (Server node)

Download Go, unpack it, and add it to your `PATH`:

```bash
wget https://go.dev/dl/go1.27.1.linux-amd64.tar.gz
sudo tar -C /usr/local -xzf go1.27.1.linux-amd64.tar.gz
echo 'export PATH=$PATH:/usr/local/go/bin' >> ~/.bashrc
source ~/.bashrc
go version
```

You should see `go version go1.27.1 linux/amd64`.

### 2.2 Build h2load 1.69.0 (Load Generator node)

Install the required C libraries. Then build nghttp2 from source with the apps enabled (`--enable-app`), which builds `h2load`:

```bash
sudo apt update
sudo apt install -y libc-ares-dev libevent-dev libjansson-dev pkg-config
wget https://github.com/nghttp2/nghttp2/releases/download/v1.69.0/nghttp2-1.69.0.tar.gz
tar -xzvf nghttp2-1.69.0.tar.gz
cd ~/nghttp2-1.69.0
./configure --enable-app
make -j$(nproc)
sudo make install
sudo ldconfig
h2load --version
```

You should see `h2load nghttp2/1.69.0`.

---

## 3. Run the experiments

Each run needs two terminals:

- **Terminal 1** on the Server node runs the Go server, `<git folder>/main.go`.
- **Terminal 2** on the Load Generator node runs h2load.

> **Important:** Start the server first and wait until it logs `listening on :8080 using native h2c; ...`. Then start h2load. Restart the server for every run so that its phase clock and counters start from zero.

### h2load parameters

| Parameter          | Meaning                                         |
|--------------------|-------------------------------------------------|
| `-c 20`            | 20 concurrent connections                       |
| `-m 50000`         | Up to 50,000 concurrent streams per session     |
| `--rps=100`        | Target rate of 100 requests per second          |
| `--duration=50s`   | Run the benchmark for 50 seconds                |
| `--log-file`       | Per-request TSV log                             |
| `--output-file`    | Summary statistics as JSON                      |

> **Note:** Replace `<Server IP:PORT>` in every h2load command with the Server node's URL, for example `http://10.10.1.1:8080/`. Use `http://`, not `https://`, because the server uses cleartext h2c.

> **Note:** In the server commands, replace `<git folder>` with the folder that holds `main.go`.

### 3.1 Baseline: default (no concurrency cap)

No `-max-streams` flag is given, so the server uses its default of 50,000 streams per connection. At 100 req/s this limit is never reached, so the run is effectively uncapped.

**Terminal 1 (Server):**

```bash
mkdir -p results_default
go run <git folder>/main.go 2> results_default/load_test.log
```

**Terminal 2 (Load Generator):**

```bash
mkdir -p results_default
h2load -c 20 -m 50000 --rps=100 --duration=50s \
  --log-file results_default/h2load_phase_test.tsv \
  --output-file results_default/h2load_phase_test.json \
  <Server IP:PORT> > results_default/h2load.log
```

When h2load finishes, stop the server with **Ctrl+C** in Terminal 1.

### 3.2 Capped stream limits (100, 200, 256, 300)

Repeat the same start, run, stop steps for each limit. Only `-max-streams` and the output directory change.

#### `max-streams = 100`

**Terminal 1 (Server):**

```bash
mkdir -p results_100
go run <git folder>/main.go -max-streams=100 2> results_100/load_test.log
```

**Terminal 2 (Load Generator):**

```bash
mkdir -p results_100
h2load -c 20 -m 50000 --rps=100 --duration=50s \
  --log-file results_100/h2load_phase_test.tsv \
  --output-file results_100/h2load_phase_test.json \
  <Server IP:PORT> > results_100/h2load.log
```

Stop the server with **Ctrl+C**.

#### `max-streams = 200`

**Terminal 1 (Server):**

```bash
mkdir -p results_200
go run <git folder>/main.go -max-streams=200 2> results_200/load_test.log
```

**Terminal 2 (Load Generator):**

```bash
mkdir -p results_200
h2load -c 20 -m 50000 --rps=100 --duration=50s \
  --log-file results_200/h2load_phase_test.tsv \
  --output-file results_200/h2load_phase_test.json \
  <Server IP:PORT> > results_200/h2load.log
```

Stop the server with **Ctrl+C**.

#### `max-streams = 256`

**Terminal 1 (Server):**

```bash
mkdir -p results_256
go run <git folder>/main.go -max-streams=256 2> results_256/load_test.log
```

**Terminal 2 (Load Generator):**

```bash
mkdir -p results_256
h2load -c 20 -m 50000 --rps=100 --duration=50s \
  --log-file results_256/h2load_phase_test.tsv \
  --output-file results_256/h2load_phase_test.json \
  <Server IP:PORT> > results_256/h2load.log
```

Stop the server with **Ctrl+C**.

#### `max-streams = 300`

**Terminal 1 (Server):**

```bash
mkdir -p results_300
go run <git folder>/main.go -max-streams=300 2> results_300/load_test.log
```

**Terminal 2 (Load Generator):**

```bash
mkdir -p results_300
h2load -c 20 -m 50000 --rps=100 --duration=50s \
  --log-file results_300/h2load_phase_test.tsv \
  --output-file results_300/h2load_phase_test.json \
  <Server IP:PORT> > results_300/h2load.log
```

Stop the server with **Ctrl+C**.

### 3.3 Output files

After all five runs, each `results_<setting>/` directory holds:

| File                       | Node   | Contents                                     |
|----------------------------|--------|----------------------------------------------|
| `load_test.log`            | Server | Server stderr: cumulative arrivals and current phase, once per second |
| `h2load.log`               | LG     | h2load stdout summary                        |
| `h2load_phase_test.tsv`    | LG     | Per-request log from h2load                  |
| `h2load_phase_test.json`   | LG     | h2load summary statistics                    |

---

## 4. Generate the plots

The plotting script draws the cumulative arrival graph from a server log file. Run it once for each setting:

```bash
python3 plot_cumulative_arrivals.py results_300/load_test.log -o out_300.png
```

Optional arguments:

| Flag                  | Effect                                                                 |
|-----------------------|------------------------------------------------------------------------|
| `-o out.png`          | Where to save the output PNG                                           |
| `--title "..."`       | Chart title                                                            |
| `--show`              | Open the chart in an interactive window                                |
| `--no-phase-shading`  | Turn off the FAST/SLOW background shading                              |
| `--ideal-rate 1500`   | Move the dashed "ideal rate" reference line (default 2000/s; `0` hides it) |

To plot all five runs:

```bash
for s in default 100 200 256 300; do
  python3 plot_cumulative_arrivals.py results_$s/load_test.log -o out_$s.png
done
```
