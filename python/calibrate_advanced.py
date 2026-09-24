#!/usr/bin/env python3
"""Fit the final OpenVQ fusion stage to human MOS.

Run after the base calibration has been fitted and features have been
re-extracted with that base calibration.

Required CSV columns:
human_mos,base_penalty,advanced_multi_resolution,advanced_temporal,
advanced_modulation,advanced_asymmetry,advanced_tilt,advanced_level,
advanced_bad_interval,advanced_echo,advanced_choppiness,
advanced_residual_intrusion

All learned weights are constrained to be non-negative so increasing a
measured degradation cannot improve the predicted MOS.
"""
import argparse
import csv
import math

FEATURES = [
    "base_penalty",
    "advanced_multi_resolution",
    "advanced_temporal",
    "advanced_modulation",
    "advanced_asymmetry",
    "advanced_tilt",
    "advanced_level",
    "advanced_bad_interval",
    "advanced_echo",
    "advanced_choppiness",
    "advanced_residual_intrusion",
]

OUTPUT_KEYS = [
    "base_penalty_weight",
    "advanced_multi_resolution_weight",
    "advanced_temporal_weight",
    "advanced_modulation_weight",
    "advanced_asymmetry_weight",
    "advanced_tilt_weight",
    "advanced_level_weight",
    "advanced_bad_interval_weight",
    "advanced_echo_weight",
    "advanced_choppiness_weight",
    "advanced_residual_intrusion_weight",
]

DEFAULTS = [
    0.58, 0.3864, 0.2688, 0.1680, 0.3192, 0.1344, 0.1680, 0.2352,
    0.40, 0.40, 0.20,
]

def clamp(x, lo, hi):
    return max(lo, min(hi, x))

def load(path):
    rows = []
    with open(path, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            x = [max(0.0, float(r[k])) for k in FEATURES]
            y = clamp(float(r["human_mos"]), 1.0, 5.0)
            rows.append((x, y))
    if not rows:
        raise SystemExit("no rows")
    return rows

def fit(rows, epochs=16000, lr=0.015, l2=0.001):
    w = DEFAULTS[:]
    bias = 0.0

    for epoch in range(epochs):
        gb = 0.0
        gw = [0.0] * len(w)

        for x, y in rows:
            raw = 5.0 - bias - sum(a * b for a, b in zip(w, x))
            pred = clamp(raw, 1.0, 5.0)
            if raw <= 1.0 or raw >= 5.0:
                continue

            err = pred - y
            gb += -2.0 * err
            for i in range(len(w)):
                gw[i] += -2.0 * err * x[i]

        n = max(1, len(rows))
        bias = max(0.0, bias - lr * gb / n)
        for i in range(len(w)):
            grad = gw[i] / n + 2.0 * l2 * w[i]
            w[i] = max(0.0, w[i] - lr * grad)

        if epoch and epoch % 4000 == 0:
            lr *= 0.7

    return bias, w

def metrics(rows, bias, w):
    ys, ps = [], []
    for x, y in rows:
        p = clamp(5.0 - bias - sum(a * b for a, b in zip(w, x)), 1.0, 5.0)
        ys.append(y)
        ps.append(p)

    rmse = math.sqrt(sum((p-y)**2 for p,y in zip(ps,ys)) / len(ys))
    my = sum(ys) / len(ys)
    mp = sum(ps) / len(ps)
    num = sum((y-my)*(p-mp) for y,p in zip(ys,ps))
    den = math.sqrt(
        sum((y-my)**2 for y in ys) *
        sum((p-mp)**2 for p in ps)
    )
    return rmse, (num / den if den else 0.0)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("csv")
    ap.add_argument("--base-calibration")
    ap.add_argument("--out", default="openvq-final.calibration")
    args = ap.parse_args()

    rows = load(args.csv)
    bias, weights = fit(rows)
    rmse, corr = metrics(rows, bias, weights)

    prefix = ""
    if args.base_calibration:
        with open(args.base_calibration, encoding="utf-8") as f:
            prefix = f.read().rstrip() + "\n"

    with open(args.out, "w", encoding="utf-8") as f:
        f.write(prefix)
        f.write(f"final_bias={bias:.9f}\n")
        for key, value in zip(OUTPUT_KEYS, weights):
            f.write(f"{key}={value:.9f}\n")
        f.write(f"advanced_training_rmse={rmse:.9f}\n")
        f.write(f"advanced_training_pearson={corr:.9f}\n")

    print(
        f"rows={len(rows)} rmse={rmse:.4f} "
        f"pearson={corr:.4f} out={args.out}"
    )

if __name__ == "__main__":
    main()
