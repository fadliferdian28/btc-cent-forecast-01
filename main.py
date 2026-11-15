#!/usr/bin/env python3
"""btc-cent-forecast-01: 240-minute-ahead BTC (cbBTC/USDC Orca pool) price
forecaster. One program, run once per case, no network, fully deterministic.

Forecast = shrinkage: the checkpoint close shrunk 40% of the way toward the
trailing 240-minute mean. This was the best of 14 candidate models on the
reliable backtests (76 hourly checkpoints: MAE $360.53 vs $374.35 for
persistence, -3.7%; 19 independent 4-hourly checkpoints: $328.37 vs $334.82,
-1.9%). A k-NN analog model won on the 5 practice cases but lost badly on
the 76-checkpoint grid (+24% vs persistence), so it was rejected as noise.

On any error the forecaster falls back to the checkpoint close (persistence),
so every case always yields a valid output.
"""

import json
import math
import os

HORIZON = 240         # minutes ahead to forecast; also the trailing-mean window
SHRINK = 0.4          # fraction of the way from the last price to the mean


def forecast(prices):
    """Last price shrunk SHRINK toward the trailing 240-minute mean.
    Falls back to persistence on any error."""
    last = prices[-1]
    try:
        tail = prices[-HORIZON:]
        mean = sum(tail) / len(tail)
        value = last + SHRINK * (mean - last)
        if math.isfinite(value) and value > 0:
            return value
        return last
    except Exception:
        return last


def run_case(case):
    """Forecast one case dict. Returns the price (float)."""
    markets = case.get("markets") or []
    if not markets:
        raise ValueError("no markets in case")
    prices = markets[0].get("prices") or []
    if len(prices) < HORIZON + 1:
        raise ValueError("too few prices in case")
    price = forecast(prices)
    if not math.isfinite(price) or price <= 0 or price >= 10_000_000:
        price = prices[-1]
    return round(float(price), 5)


def main():
    in_dir = os.environ.get("MAKEFUN_INPUT_DIR", "/input")
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    names = sorted(f for f in os.listdir(in_dir) if f.endswith(".in"))
    for name in names:
        case_id = name[: -len(".in")]
        try:
            with open(os.path.join(in_dir, name), "r", encoding="utf-8") as fh:
                case = json.load(fh)
            price = run_case(case)
        except Exception:
            # Last-resort fallback: re-read only the last price, else 1.0.
            price = 1.0
            try:
                with open(os.path.join(in_dir, name), "r", encoding="utf-8") as fh:
                    case = json.load(fh)
                last = case["markets"][0]["prices"][-1]
                if math.isfinite(last) and 0 < last < 10_000_000:
                    price = round(float(last), 5)
            except Exception:
                pass
        out = {"forecasts": [{"case": case_id, "price": price}]}
        with open(os.path.join(out_dir, case_id + ".out"), "w", encoding="utf-8") as fh:
            json.dump(out, fh)


if __name__ == "__main__":
    main()
