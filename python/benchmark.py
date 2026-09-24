#!/usr/bin/env python3
"""Benchmark OpenVQ and optional baselines against human MOS.

Manifest CSV requires:
reference,degraded,human_mos

Optional columns:
visqol_mos,polqa_mos
"""
import argparse
import csv
import json
import math
import subprocess

def pearson(a, b):
    if len(a) < 2:
        return 0.0
    ma = sum(a) / len(a)
    mb = sum(b) / len(b)
    num = sum((x-ma)*(y-mb) for x,y in zip(a,b))
    den = math.sqrt(sum((x-ma)**2 for x in a) * sum((y-mb)**2 for y in b))
    return num / den if den else 0.0

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

def metrics(pred, truth):
    return {
        "n": len(pred),
        "rmse": math.sqrt(sum((x-y)**2 for x,y in zip(pred,truth)) / len(pred)),
        "pearson": pearson(pred, truth),
        "spearman": pearson(ranks(pred), ranks(truth)),
        "bias": sum(x-y for x,y in zip(pred,truth)) / len(pred),
    }

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("manifest")
    ap.add_argument("--cli", default="./build/openvq_cli")
    ap.add_argument("--calibration")
    args = ap.parse_args()

    human, openvq_scores = [], []
    visqol_pairs, polqa_pairs = [], []

    with open(args.manifest, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            cmd = [args.cli, row["reference"], row["degraded"]]
            if row.get("visqol_mos", ""):
                cmd += ["--visqol-score", row["visqol_mos"]]
            if args.calibration:
                cmd += ["--calibration", args.calibration]

            result = json.loads(subprocess.check_output(cmd, text=True))
            y = float(row["human_mos"])
            human.append(y)
            openvq_scores.append(float(result["mos"]))

            if row.get("visqol_mos", ""):
                visqol_pairs.append((float(row["visqol_mos"]), y))
            if row.get("polqa_mos", ""):
                polqa_pairs.append((float(row["polqa_mos"]), y))

    report = {"openvq": metrics(openvq_scores, human)}
    if visqol_pairs:
        report["visqol"] = metrics(
            [x for x,_ in visqol_pairs],
            [y for _,y in visqol_pairs])
    if polqa_pairs:
        report["polqa"] = metrics(
            [x for x,_ in polqa_pairs],
            [y for _,y in polqa_pairs])

    print(json.dumps(report, indent=2, sort_keys=True))

if __name__ == "__main__":
    main()
