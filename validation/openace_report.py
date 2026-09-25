#!/usr/bin/env python3
"""Paired public POLQA comparison and nested speaker-held-out development."""
import argparse
import csv
import hashlib
import json
import math
from pathlib import Path

import numpy as np
from scipy.stats import pearsonr, spearmanr

ALPHAS = [0.1, 1., 10., 100., 1000.]
METRICS = ["openvq_mos", "visqol_speech_mos", "visqol_audio_mos", "published_visqol", "published_polqa"]


def finite(value):
    try:
        return math.isfinite(float(value))
    except (ValueError, TypeError):
        return False


def regression_metrics(y, p):
    return {"n": len(y), "rmse_mushra": float(np.sqrt(np.mean((p-y)**2))),
            "mae_mushra": float(np.mean(np.abs(p-y))), "bias_mushra": float(np.mean(p-y))}


def correlations(y, p):
    if len(y) < 3 or np.std(p) == 0 or np.std(y) == 0:
        return {"pearson": None, "spearman": None}
    return {"pearson": float(pearsonr(y, p).statistic),
            "spearman": float(spearmanr(y, p).statistic)}


def affine_oof(x, y, speakers):
    predictions = np.zeros_like(y)
    params = {}
    for speaker in sorted(set(speakers)):
        train = speakers != speaker
        test = ~train
        xc = x[train] - x[train].mean()
        slope = max(0., float(xc @ (y[train]-y[train].mean()) / max(xc @ xc, 1e-12)))
        intercept = float(y[train].mean() - slope*x[train].mean())
        predictions[test] = np.clip(intercept + slope*x[test], 0, 100)
        params[speaker] = {"slope": slope, "intercept": intercept, "train_n": int(train.sum())}
    return predictions, params


def ridge_fit(x, y, alpha):
    mean = x.mean(axis=0)
    sd = x.std(axis=0)
    sd[sd < 1e-10] = 1.
    z = (x-mean)/sd
    bias = y.mean()
    w = np.linalg.solve(z.T@z + alpha*np.eye(x.shape[1]), z.T@(y-bias))
    return {"mean": mean, "sd": sd, "weights": w, "bias": bias, "alpha": alpha}


def ridge_predict(model, x):
    return np.clip((x-model["mean"])/model["sd"]@model["weights"]+model["bias"], 0, 100)


def select_alpha(x, y, speakers):
    errors = {}
    for alpha in ALPHAS:
        p = np.zeros_like(y)
        for s in sorted(set(speakers)):
            tr = speakers != s
            p[~tr] = ridge_predict(ridge_fit(x[tr], y[tr], alpha), x[~tr])
        errors[alpha] = float(np.mean((p-y)**2))
    return min(ALPHAS, key=lambda a: (errors[a], -a)), errors


def nested_ridge(x, y, speakers):
    pred = np.zeros_like(y)
    folds = {}
    for s in sorted(set(speakers)):
        tr = speakers != s
        alpha, errors = select_alpha(x[tr], y[tr], speakers[tr])
        model = ridge_fit(x[tr], y[tr], alpha)
        pred[~tr] = ridge_predict(model, x[~tr])
        folds[s] = {"selected_alpha": alpha, "inner_mse": errors,
                    "train_speakers": sorted(set(speakers[tr])), "train_n": int(tr.sum()),
                    "test_n": int((~tr).sum()), **regression_metrics(y[~tr], pred[~tr])}
    return pred, folds


def paired_bootstrap(y, candidate, comparator, clusters, nboot, seed):
    rng = np.random.default_rng(seed)
    groups = [np.flatnonzero(clusters == c) for c in sorted(set(clusters))]
    delta = np.empty(nboot)
    for i in range(nboot):
        ix = np.concatenate([groups[j] for j in rng.integers(0, len(groups), len(groups))])
        delta[i] = np.sqrt(np.mean((candidate[ix]-y[ix])**2))-np.sqrt(np.mean((comparator[ix]-y[ix])**2))
    return {"delta_rmse_mushra": float(np.sqrt(np.mean((candidate-y)**2))-np.sqrt(np.mean((comparator-y)**2))),
            "ci95": np.quantile(delta, [0.025, 0.975]).tolist(),
            "resampling_unit": "speaker plus emotion, retaining codec variants",
            "n_clusters": len(groups), "bootstrap_samples": nboot, "seed": seed,
            "scope": "conditional on observed speakers and fitted cross-validation models"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("inputs", nargs="+", type=Path)
    ap.add_argument("--outdir", required=True, type=Path)
    ap.add_argument("--bootstrap", type=int, default=10000)
    a = ap.parse_args()
    rows = []
    for path in a.inputs:
        with path.open(newline="") as f:
            rows.extend(csv.DictReader(f))
    rows.sort(key=lambda r: r["row_id"])
    if len(rows) != 144 or len({r["row_id"] for r in rows}) != 144:
        raise ValueError("require all 144 unique predeclared codec recordings")
    features = sorted(k for k in rows[0] if k.startswith("feature_"))
    if len(features) != 21:
        raise ValueError("require exactly the 21 signal-only features")
    for r in rows:
        for k in features + ["human_mushra", "openvq_mos", "visqol_speech_mos", "visqol_audio_mos"]:
            if not finite(r[k]):
                raise ValueError(f"invalid {k} for {r['row_id']}")
    y_all = np.array([float(r["human_mushra"]) for r in rows])
    s_all = np.array([r["speaker"] for r in rows])
    x = np.array([[float(r[k]) for k in features] for r in rows])
    specialist, folds = nested_ridge(x, y_all, s_all)
    valid = np.array([all(finite(r[k]) for k in METRICS) for r in rows])
    matched = [r for r, ok in zip(rows, valid) if ok]
    y, speakers = y_all[valid], s_all[valid]
    clusters = np.array([r["condition_id"] for r in matched])
    report = {
        "dataset": "EARS-EMO-OpenACE", "target": "human MUSHRA, 0 to 100; not ACR MOS",
        "model_id": "phase3-tcd-only-2026-09-24-f099129",
        "protocol": "validation/OPENACE_PROTOCOL.md", "total_coded_pairs": len(rows),
        "paired_complete_cases": len(matched),
        "excluded_from_paired_comparison": [r["row_id"] for r, ok in zip(rows, valid) if not ok],
        "source_sha256": {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in a.inputs},
        "raw_score_correlations": {}, "speaker_held_out_affine": {}, "by_speaker": {},
        "original_locked_mos_parity": "not established by this different dataset and rating scale",
        "polqa_provenance": "author-published P.863 scores; executable version and command not published in dataset card",
    }
    oof = {}
    for metric in METRICS:
        p = np.array([float(r[metric]) for r in matched])
        report["raw_score_correlations"][metric] = {"n": len(y), **correlations(y, p)}
        oof[metric], params = affine_oof(p, y, speakers)
        report["speaker_held_out_affine"][metric] = {**regression_metrics(y, oof[metric]), "folds": params}
    oof["codec_specialist_nested_oof"] = specialist[valid]
    report["codec_specialist_development"] = {
        "evaluation": "nested leave-one-speaker-out; development result, not an independent external test",
        "features": features, "folds": folds,
        "complete_case_metrics": {**regression_metrics(y, specialist[valid]), **correlations(y, specialist[valid])},
        "all_144_metrics": {**regression_metrics(y_all, specialist), **correlations(y_all, specialist)},
    }
    report["paired_rmse_vs_polqa"] = {
        k: paired_bootstrap(y, p, oof["published_polqa"], clusters, a.bootstrap, 20260925)
        for k, p in oof.items() if k != "published_polqa"
    }
    for s in sorted(set(speakers)):
        ix = speakers == s
        report["by_speaker"][s] = {k: regression_metrics(y[ix], p[ix]) for k, p in oof.items()}
    for r, p in zip(rows, specialist):
        r["codec_specialist_nested_oof_mushra"] = p
    for j, r in enumerate(matched):
        for k in METRICS:
            r[k+"_affine_oof_mushra"] = oof[k][j]
    for r, ok in zip(rows, valid):
        if not ok:
            for k in METRICS:
                r[k+"_affine_oof_mushra"] = ""
    a.outdir.mkdir(parents=True, exist_ok=True)
    (a.outdir / "report.json").write_text(json.dumps(report, indent=2, allow_nan=False)+"\n")
    with (a.outdir / "predictions.csv").open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    print(json.dumps({k: report[k] for k in ["paired_complete_cases", "raw_score_correlations", "paired_rmse_vs_polqa"]}, indent=2))


if __name__ == "__main__":
    main()
