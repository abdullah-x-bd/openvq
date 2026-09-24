#!/usr/bin/env python3
"""Fit non-negative degradation weights to human MOS labels.

CSV columns:
human_mos,missing,added,coloration,noisiness,discontinuity,loudness,clipping,bad_section[,visqol_mos]

The fitted model is monotonic by construction because every degradation weight
is projected to be non-negative. The output is a simple key=value file suitable
for review and later embedding into the native calibration struct.
"""
import argparse
import csv
import math

FEATURES = ["missing", "added", "coloration", "noisiness", "discontinuity", "loudness", "clipping", "bad_section"]

def clamp(x, lo, hi):
    return max(lo, min(hi, x))

def load(path):
    rows = []
    with open(path, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            x = [clamp(float(r[k]), 0.0, 1.0) for k in FEATURES]
            if r.get("visqol_mos", ""):
                x.append(clamp((5.0 - float(r["visqol_mos"])) / 4.0, 0.0, 1.0))
            else:
                x.append(0.0)
            y = clamp(float(r["human_mos"]), 1.0, 5.0)
            rows.append((x, y))
    if not rows:
        raise SystemExit("no rows")
    return rows

def fit(rows, epochs=12000, lr=0.03, l2=0.002):
    w = [0.5] * 9
    bias = 0.02
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
        if epoch and epoch % 3000 == 0:
            lr *= 0.7
    return bias, w

def metrics(rows, bias, w):
    errors = []
    ys, ps = [], []
    for x, y in rows:
        p = clamp(5.0 - bias - sum(a * b for a, b in zip(w, x)), 1.0, 5.0)
        errors.append((p-y)**2)
        ys.append(y)
        ps.append(p)
    rmse = math.sqrt(sum(errors)/len(errors))
    my = sum(ys)/len(ys)
    mp = sum(ps)/len(ps)
    num = sum((a-my)*(b-mp) for a,b in zip(ys,ps))
    den = math.sqrt(sum((a-my)**2 for a in ys)*sum((b-mp)**2 for b in ps))
    return rmse, (num/den if den else 0.0)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("csv")
    ap.add_argument("--out", default="openvq.calibration")
    args = ap.parse_args()
    rows = load(args.csv)
    bias, w = fit(rows)
    rmse, corr = metrics(rows, bias, w)
    names = FEATURES + ["visqol_penalty"]
    with open(args.out, "w", encoding="utf-8") as f:
        f.write(f"bias={bias:.9f}\n")
        for k,v in zip(names,w):
            f.write(f"{k}_weight={v:.9f}\n")
        f.write(f"training_rmse={rmse:.9f}\ntraining_pearson={corr:.9f}\n")
    print(f"rows={len(rows)} rmse={rmse:.4f} pearson={corr:.4f}")

if __name__ == "__main__":
    main()
