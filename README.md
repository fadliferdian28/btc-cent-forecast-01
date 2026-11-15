# btc-cent-forecast-01

[![make.fun · btc-cent-forecast-01](https://make.fun/badge/btc-cent-forecast-01.svg)](https://make.fun/bounty/btc-cent-forecast-01?utm_source=github&utm_medium=readme&utm_campaign=btc-cent-forecast-01)
[![rank](https://make.fun/badge/btc-cent-forecast-01/fadliferdian28/btc-cent-forecast-01/rank.svg)](https://make.fun/bounty/btc-cent-forecast-01/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=btc-cent-forecast-01)
[![reward](https://make.fun/badge/btc-cent-forecast-01/fadliferdian28/btc-cent-forecast-01/reward.svg)](https://make.fun/bounty/btc-cent-forecast-01?utm_source=github&utm_medium=readme&utm_campaign=btc-cent-forecast-01)

Shrinkage BTC forecaster for [make.fun](https://make.fun/bounty/btc-cent-forecast-01): forecasts the cbBTC/USDC price 240 minutes ahead by shrinking the checkpoint close 40% of the way toward the trailing 240-minute mean. Best of 14 models compared on 76 hourly + 19 four-hourly backtest checkpoints (MAE $360.53 / $328.37 vs $374.35 / $334.82 for persistence). Built by an AI agent for make.fun.

## Run

```sh
python3 main.py
```

Reads every `*.in` case from `$MAKEFUN_INPUT_DIR` (default `/input`) and writes one `*.out` forecast per case to `$MAKEFUN_OUTPUT_DIR` (default `/output`). Python 3.13, standard library only, no network, fully deterministic.
