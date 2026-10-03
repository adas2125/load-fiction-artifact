# Load Fiction

Official artifact repository for **“Load Fiction: How Your Load Generator is Misleading You.”**

This repository contains experiments examining how load generators can send request patterns that differ from their configured workloads, affecting performance measurements. The experiments compare request arrivals, latency distributions, and, where applicable, client CPU utilization.

## Repository layout

| Directory | Experiment |
| --- | --- |
| [`LG_failures/wrk2_dsb/`](LG_failures/wrk2_dsb/README.md) | Tests how wrk2 connection limits affect request arrivals against a server with periodic response delays. Uses the wrk2 implementation bundled with DeathStarBench. |
| [`LG_failures/h2load/`](LG_failures/h2load/README.md) | Tests how server-side HTTP/2 stream concurrency limits affect throughput and request arrivals. |
| [`LG_failures/k6_failure/`](LG_failures/k6_failure/README.md) | Investigates k6 arrival timing and latency measurements under different client CPU allocations, using HTTPS and connection churn. |
| [`LG_failures/vegeta_failure/`](LG_failures/vegeta_failure/README.md) | Examines Vegeta request delivery and latency measurements against a phase-shifting server with limited concurrency. |
| `xlg/` | Placeholder. |
| `cilantro_experiment/` | Placeholder. |

## Getting started

Clone the artifact repository:

```bash
git clone https://github.com/adas2125/load-fiction-artifact.git
cd load-fiction-artifact
```

Choose an experiment from the table above and follow its README for dependencies, source initialization, builds, server setup, execution, and plotting.

The repository references DeathStarBench, k6, and Vegeta source repositories as Git submodules. Follow the selected experiment's instructions to initialize and build the required sources.
