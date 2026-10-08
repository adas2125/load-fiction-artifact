# XLG Inspector (Originally a Vegeta Fork)
This repository is a fork of [Vegeta](https://github.com/tsenart/vegeta).
All credit for the original Vegeta load-testing tool goes to the upstream Vegeta authors.

## Overview
This fork instruments Vegeta with additional signals required by **XLG Inspector**. It also includes analysis scripts and experiments used to generate the findings in our paper.

Our main contributions are:
- Instrumentation of Vegeta with signals needed by XLG Inspector.
- Analysis scripts for reproducing the paper’s figures and tables.
- Experiments using Vegeta to evaluate load-generation behavior.

Experiments are summarized in the `README.md` files associated with `experiments_eval` and `experiments_eval_silent`.

## Streaming XLG Experiment

The main streaming experiment is provided in:

```bash
test_xlg_window.sh
```

This script tests the XLG tool in a streaming fashion. We recommend running it with `cmd/ramping_regime_shift_server/main.go`, since that can trigger every failure other than CPU contention.
