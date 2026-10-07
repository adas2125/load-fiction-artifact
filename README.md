# Load Fiction

This repository contains code for the short paper **“Load Fiction: How Your Load Generator is Misleading You.”**

## Repository layout

| Directory | Experiment |
| --- | --- |
| [`LG_failures/wrk2_dsb/`](LG_failures/wrk2_dsb/README.md) | Tests how wrk2 connection limits affect request arrivals against a server with periodic response delays. Uses the wrk2 implementation bundled with DeathStarBench. |
| [`LG_failures/h2load/`](LG_failures/h2load/README.md) | Tests how server-side HTTP/2 stream concurrency limits affect throughput and request arrivals. |
| [`LG_failures/k6_failure/`](LG_failures/k6_failure/README.md) | Investigates k6 arrival timing and latency measurements under different client CPU allocations, using HTTPS and connection churn. |
| [`LG_failures/vegeta_failure/`](LG_failures/vegeta_failure/README.md) | Examines Vegeta request delivery and latency measurements against a phase-shifting server with limited concurrency. |
| [`xlg/`](xlg/README.md) | an observability layer built on top of Vegeta to diagnose bottlenecks in LG runs. |
| [`cilantro_experiment`](cilantro_experiment/README.md) | Highlights the impact that load generator failures may have on experimental results of the Cilantro paper. |

## Getting started

Clone the artifact repository:

```bash
git clone https://github.com/adas2125/load-fiction-artifact.git
cd load-fiction-artifact
```

Choose an experiment from the table above and follow its README for dependencies, source initialization, builds, server setup, execution, and plotting.

The repository references DeathStarBench, k6, and Vegeta source repositories as Git submodules. Follow the selected experiment's instructions to initialize and build the required sources.
