#!/usr/bin/env python3
"""Joint monotonic calibration for OpenVQ v0.2.

Fits the base and advanced degradation features simultaneously against
human MOS. The model predicts a non-negative degradation penalty:

    MOS = clip(5 - bias - sum(weight_i * degradation_i), 1, 5)

All weights are constrained non-negative, so increasing any normalized
degradation cannot improve the calibrated score.
"""
import argparse
import csv
import math

FEATURES = [
    ("missing", "missing_weight"),
    ("added", "added_weight"),
    ("coloration", "coloration_weight"),
    ("noisiness", "noisiness_weight"),
    ("discontinuity", "discontinuity_weight"),
    ("loudness", "loudness_weight"),
    ("clipping", "clipping_weight"),
    ("bad_section", "bad_section_weight"),
    ("advanced_multi_resolution", "advanced_multi_resolution_weight"),
    ("advanced_temporal", "advanced_temporal_weight"),
    ("advanced_modulation", "advanced_modulation_weight"),
    ("advanced_asymmetry", "advanced_asymmetry_weight"),
    ("advanced_tilt", "advanced_tilt_weight"),
    ("advanced_level", "advanced_level_weight"),
    ("advanced_bad_interval", "advanced_bad_interval_weight"),
    ("advanced_echo", "advanced_echo_weight"),
    ("advanced_residual", "advanced_residual_weight"),
    ("advanced_temporal_edit", "advanced_temporal_edit_weight"),
    ("advanced_clip_plateau", "advanced_clip_plateau_weight"),
    ("advanced_inactive_noise", "advanced_inactive_noise_weight"),
]

def clamp(x, lo, hi):
    return max(lo, min(hi, x))

def load_rows(path):
    rows = []
    with open(path, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            x = [clamp(float(r[name]), 0.0, 1.0) for name, _ in FEATURES]
            target_penalty = 5.0 - clamp(float(r["human_mos"]), 1.0, 5.0)
            rows.append((x, target_penalty))
    if not rows:
        raise SystemExit("no rows")
    return rows

def fit(rows, epochs=30000, lr=0.018, l2=0.0015):
    w = [0.08] * len(FEATURES)
    bias = 0.05

    for epoch in range(epochs):
        gb = 0.0
        gw = [0.0] * len(w)
        for x, target in rows:
            pred = bias + sum(a*b for a,b in zip(w,x))
            # MOS clipping at 1 implies a maximum meaningful penalty of 4.
            clipped = clamp(pred, 0.0, 4.0)
            if pred < 0.0 or pred > 4.0:
                continue
            err = clipped - target
            gb += 2.0 * err
            for i in range(len(w)):
                gw[i] += 2.0 * err * x[i]

        n = len(rows)
        bias = max(0.0, bias - lr * gb / n)
        for i in range(len(w)):
            grad = gw[i] / n + 2.0*l2*w[i]
            w[i] = max(0.0, w[i] - lr*grad)

        if epoch and epoch % 6000 == 0:
            lr *= 0.72

    return bias, w

def predict_penalty(x, bias, w):
    return clamp(bias + sum(a*b for a,b in zip(w,x)), 0.0, 4.0)

def metrics(rows, bias, w):
    ys, ps = [], []
    for x, target in rows:
        y = 5.0 - target
        p = 5.0 - predict_penalty(x,bias,w)
        ys.append(y); ps.append(p)
    rmse = math.sqrt(sum((p-y)**2 for p,y in zip(ps,ys))/len(ys))
    my=sum(ys)/len(ys); mp=sum(ps)/len(ps)
    num=sum((y-my)*(p-mp) for y,p in zip(ys,ps))
    den=math.sqrt(sum((y-my)**2 for y in ys)*sum((p-mp)**2 for p in ps))
    return rmse, (num/den if den else 0.0)

def write_calibration(path, bias, w):
    with open(path, "w", encoding="utf-8") as f:
        f.write(f"bias={bias:.9f}\n")
        for (_, key), value in zip(FEATURES[:8], w[:8]):
            f.write(f"{key}={value:.9f}\n")
        f.write("visqol_penalty_weight=0.000000000\n")
        # Base penalty is passed through exactly once into final fusion.
        f.write("final_bias=0.000000000\n")
        f.write("base_penalty_weight=1.000000000\n")
        for (_, key), value in zip(FEATURES[8:], w[8:]):
            f.write(f"{key}={value:.9f}\n")

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("csv")
    ap.add_argument("--out", default="openvq-v02.calibration")
    args=ap.parse_args()
    rows=load_rows(args.csv)
    bias,w=fit(rows)
    rmse,corr=metrics(rows,bias,w)
    write_calibration(args.out,bias,w)
    print(f"rows={len(rows)} training_rmse={rmse:.6f} training_pearson={corr:.6f}")
    print(f"bias={bias:.9f}")
    for (name,_),value in zip(FEATURES,w):
        print(f"{name}={value:.9f}")

if __name__=="__main__":
    main()
