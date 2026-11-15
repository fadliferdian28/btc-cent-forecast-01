#!/usr/bin/env python3
"""btc-cent-forecast-01: 240-minute-ahead BTC (cbBTC/USDC Orca pool) price
forecaster. One program, run once per case, no network, fully deterministic.

Forecast = k-NN analog estimate: the last 480 minutes, demeaned and
volatility-normalized into a 48-point shape, matched against every earlier
480-minute window in the 72-hour history; the forecast is the current price
scaled by the median 240-minute-ahead ratio of the 10 nearest analogs.
Shrinkage (last price 20% toward the trailing 240-minute mean) is the
fallback when no analog is usable.

On any error the forecaster falls back to the checkpoint close (persistence),
so every case always yields a valid output.
"""

import json
import math
import os
import sys

WINDOW = 480          # minutes in the analog shape window
STEP = 10             # downsample: one point per 10 minutes -> 48-dim shape
HORIZON = 240         # minutes ahead to forecast
K = 10                # nearest analogs kept
SHRINK = 0.2          # shrinkage toward the trailing 240-min mean (fallback)


def shape(prices, end):
    """Demeaned, volatility-normalized 48-point shape ending at index `end`
    (exclusive). Returns a list of floats, or None if the window is unusable."""
    raw = [prices[end - WINDOW + i * STEP] for i in range(WINDOW // STEP)]
    mean = sum(raw) / len(raw)
    dev = [x - mean for x in raw]
    var = sum(x * x for x in dev) / len(dev)
    std = math.sqrt(var)
    if std <= 0:
        return [0.0] * len(dev)
    return [x / std for x in dev]


def knn_forecast(prices):
    """Median-analog forecast. Returns None if no usable analog exists."""
    n = len(prices)
    last = prices[-1]
    query = shape(prices, n)
    if query is None:
        return None
    # Candidate windows end at t (exclusive), with a known outcome 240 min
    # later: t ranges so that t + HORIZON < n and the window fits.
    scored = []
    for t in range(WINDOW, n - HORIZON):
        cand = shape(prices, t)
        if cand is None:
            continue
        dist = 0.0
        for a, b in zip(query, cand):
            d = a - b
            dist += d * d
        # Outcome as a ratio from the candidate window's end price.
        base = prices[t - 1]
        if base <= 0:
            continue
        ratio = prices[t + HORIZON] / base
        if not (0.5 < ratio < 2.0):
            continue
        scored.append((dist, ratio))
    if len(scored) < K:
        return None
    scored.sort(key=lambda item: item[0])
    ratios = sorted(r for _, r in scored[:K])
    mid = K // 2
    median_ratio = (ratios[mid - 1] + ratios[mid]) / 2.0
    return last * median_ratio


def shrink_forecast(prices):
    """Last price shrunk SHRINK of the way toward the trailing 240-min mean."""
    last = prices[-1]
    tail = prices[-HORIZON:]
    mean = sum(tail) / len(tail)
    return last + SHRINK * (mean - last)


def forecast(prices):
    """k-NN analog forecast, with shrinkage as the fallback when no analog
    is usable; falls back to persistence on any error."""
    last = prices[-1]
    try:
        knn = knn_forecast(prices)
        if knn is not None and math.isfinite(knn) and knn > 0:
            return knn
        shr = shrink_forecast(prices)
        if math.isfinite(shr) and shr > 0:
            return shr
        return last
    except Exception:
        return last


def run_case(case):
    """Forecast one case dict. Returns the price (float)."""
    markets = case.get("markets") or []
    if not markets:
        raise ValueError("no markets in case")
    prices = markets[0].get("prices") or []
    if len(prices) < WINDOW + HORIZON + 1:
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
