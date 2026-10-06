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

## Data
The raw data required to reproduce the results is available below:
[SocialNetwork](https://drive.google.com/file/d/1FSCQ2heOoFnNUHjZLQ_mCgsbo8xmR9SP/view?usp=sharing)
[HotelReservation](https://drive.google.com/file/d/1ivCBOKiD2NYkqFF1_iCmtreN1Ru9ZuDK/view?usp=sharing)
[ExpServer](https://drive.google.com/file/d/1z9X0IpRemRvwSpJZHy499Qzig5R1_gzX/view?usp=sharing)
Unzip these files, store them in the data/ folder and run `stage_b_cross_rps.py` for the full 
offline evaluation from logs captued online during the run.

## Streaming XLG Experiment

The main streaming experiment is provided in:

```bash
test_xlg_window.sh
```

This script tests the XLG tool in a streaming fashion. We recommend running it with `cmd/ramping_regime_shift_server/main.go`, since that can trigger every failure other than CPU contention.
