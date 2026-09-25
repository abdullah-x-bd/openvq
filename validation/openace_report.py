#!/usr/bin/env python3
"""Report frozen OpenVQ versus published POLQA on EARS-EMO-OpenACE."""
import argparse
import csv
import json
import math
import random
from collections import defaultdict

def ranks(values):
    order = sorted(range(len(values)), key=lambda i: values[i])
    out = [0.0] * len(values)
    i = 0
    while i < len(order):
        j = i + 1
        while j < len(order) and values[order[j]] == values[order[i]]:
            j += 1
        rank = (i + j - 1) / 2 + 1
        for k in range(i, j):
            out[order[k]] = rank
        i = j
    return out

def pearson(a, b):
    if len(a) != len(b) or len(a) < 2:
        return float("nan")
    ma = sum(a) / len(a)
    mb = sum(b) / len(b)
    aa = sum((x - ma) ** 2 for x in a)
    bb = sum((y - mb) ** 2 for y in b)
    if aa == 0 or bb == 0:
        return float("nan")
    return sum((x - ma) * (y - mb) for x, y in zip(a, b)) / math.sqrt(aa * bb)

def metrics(rows, column):
    pairs = [
        (float(r["distorted_mushra_rating"]), float(r[column]))
        for r in rows
        if r.get(column, "").strip()
    ]
    y = [x for x, _ in pairs]
    p = [x for _, x in pairs]
    return {
        "n": len(pairs),
        "pearson": pearson(y, p),
        "spearman": pearson(ranks(y), ranks(p)),
    }

def finite_quantiles(values):
    x = sorted(v for v in values if math.isfinite(v))
    if not x:
        return [float("nan"), float("nan")]
    def at(q):
        i = int(q * (len(x) - 1))
        return x[i]
    return [at(0.025), at(0.975)]

def cluster_bootstrap(rows, nboot, seed):
    paired = [r for r in rows if r.get("polqa_score", "").strip()]
    groups = defaultdict(list)
    for r in paired:
        groups[(r["speaker"], r["emotion"])].append(r)
    keys = sorted(groups)
    rng = random.Random(seed)
    dr = []
    ds = []
    for _ in range(nboot):
        sample = []
        for _ in keys:
            sample.extend(groups[rng.choice(keys)])
        mo = metrics(sample, "openvq_mos")
        mp = metrics(sample, "polqa_score")
        dr.append(mo["pearson"] - mp["pearson"])
        ds.append(mo["spearman"] - mp["spearman"])
    return {
        "clusters": len(keys),
        "samples": nboot,
        "delta_pearson_ci95": finite_quantiles(dr),
        "delta_spearman_ci95": finite_quantiles(ds),
    }

def grouped(rows, key, columns):
    out = {}
    for value in sorted({r[key] for r in rows}):
        rr = [r for r in rows if r[key] == value]
        out[value] = {c: metrics(rr, c) for c in columns}
    return out

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("csv")
    ap.add_argument("--out", required=True)
    ap.add_argument("--bootstrap", type=int, default=10000)
    ap.add_argument("--seed", type=int, default=20260925)
    args = ap.parse_args()

    with open(args.csv, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    if len(rows) != 144:
        raise SystemExit(f"expected 144 scored OpenACE rows, found {len(rows)}")

    columns = [
        "openvq_mos",
        "polqa_score",
        "visqol_score",
        "visqol_speech_mos",
        "visqol_audio_mos",
    ]
    overall = {c: metrics(rows, c) for c in columns}

    paired = [r for r in rows if r.get("polqa_score", "").strip()]
    openvq_paired = metrics(paired, "openvq_mos")
    polqa_paired = metrics(paired, "polqa_score")
    comparison = {
        "n": len(paired),
        "delta_pearson_openvq_minus_polqa":
            openvq_paired["pearson"] - polqa_paired["pearson"],
        "delta_spearman_openvq_minus_polqa":
            openvq_paired["spearman"] - polqa_paired["spearman"],
        **cluster_bootstrap(rows, args.bootstrap, args.seed),
    }

    out = {
        "dataset": "mcernak/EARS-EMO-OpenACE",
        "candidate": "phase3-tcd-only-2026-09-24-f099129",
        "human_target": "distorted_mushra_rating",
        "primary_statistic": "Pearson correlation with human MUSHRA",
        "overall": overall,
        "paired_openvq_vs_polqa": comparison,
        "by_codec": grouped(rows, "codec", ["openvq_mos", "polqa_score"]),
        "by_emotion": grouped(rows, "emotion", ["openvq_mos", "polqa_score"]),
        "interpretation_note":
            "OpenACE is an independent external cross-check. Formal POLQA parity remains governed by validation/LOCKED_POLQA_PROTOCOL.md.",
    }

    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, allow_nan=False)
        f.write("\n")
    print(json.dumps(out, indent=2, allow_nan=False))

if __name__ == "__main__":
    main()
