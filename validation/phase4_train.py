#!/usr/bin/env python3
"""Train a dataset-balanced Phase 4 model under engineering constraints."""
import argparse
import csv
import json
from pathlib import Path

import numpy as np
from scipy.optimize import LinearConstraint, minimize

NATIVE = [
    "base", "missing", "added", "coloration", "noisiness",
    "discontinuity", "loudness", "clipping", "bad_section",
    "multi_resolution", "temporal", "modulation", "asymmetry", "tilt",
    "level", "bad_interval", "echo", "choppiness", "residual",
]
ALPHAS = [1.0, 3.0, 10.0, 30.0, 100.0, 300.0]
EXPERT_BLENDS = [0.0, 0.1, 0.2, 0.3, 0.4]
FOLDS = 5
MODEL_ID = "phase4-native-poly2-constrained-2026-09-25-v3"
MONOTONIC_FAMILIES = [
    "dropout", "dropout_count", "noise", "lowpass", "clipping",
    "attenuation", "clock_drift", "time_scale", "mixed",
]

def read_csv(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))

def clamp(x, lo=0.0, hi=1.0):
    return max(lo, min(hi, float(x)))

def native_from_result(obj):
    d = obj["dimensions"]
    q = obj["advanced"]
    return [
        clamp((5.0 - float(obj["base_mos"])) / 4.0),
        clamp(obj["missing_disturbance"]),
        clamp(obj["added_disturbance"]),
        clamp((5.0 - float(d["coloration"])) / 4.0),
        clamp((5.0 - float(d["noisiness"])) / 4.0),
        clamp((5.0 - float(d["discontinuity"])) / 4.0),
        clamp((5.0 - float(d["loudness"])) / 4.0),
        clamp(float(obj["clipping_ratio"]) * 40.0),
        clamp(obj["bad_section_fraction"]),
        clamp(1.0 - float(q["multi_resolution_similarity"])),
        clamp(1.0 - float(q["temporal_envelope_similarity"])),
        clamp(1.0 - float(q["modulation_similarity"])),
        clamp(q["asymmetric_disturbance"]),
        clamp(q["spectral_tilt_error"]),
        clamp(float(q["active_level_delta_db"]) / 18.0),
        clamp(q["bad_interval_severity"]),
        clamp(q.get("echo_score", 0.0)),
        clamp(q.get("choppiness_score", 0.0)),
        clamp(q.get("residual_intrusion", 0.0)),
    ]

def basis(x):
    out = list(x)
    for i in range(len(x)):
        for j in range(i, len(x)):
            out.append(x[i] * x[j])
    return np.asarray(out, dtype=float)

def basis_names():
    out = list(NATIVE)
    for i, a in enumerate(NATIVE):
        for b in NATIVE[i:]:
            out.append(a + "*" + b)
    return out

def ranks(values):
    values = np.asarray(values, dtype=float)
    order = np.argsort(values, kind="mergesort")
    out = np.empty(len(values), dtype=float)
    i = 0
    while i < len(order):
        j = i + 1
        while j < len(order) and values[order[j]] == values[order[i]]:
            j += 1
        out[order[i:j]] = (i + j - 1) / 2.0 + 1.0
        i = j
    return out

def corr(a, b):
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    if len(a) < 2 or np.std(a) < 1e-12 or np.std(b) < 1e-12:
        return 0.0
    return float(np.corrcoef(a, b)[0, 1])

def metrics(y, p):
    y = np.asarray(y, dtype=float)
    p = np.asarray(p, dtype=float)
    e = p - y
    return {
        "n": int(len(y)),
        "pearson": corr(y, p),
        "spearman": corr(ranks(y), ranks(p)),
        "rmse_normalized": float(np.sqrt(np.mean(e * e))),
        "bias_normalized": float(np.mean(e)),
    }

def dataset_rows(tcd_paths, nisqa_path, openace_path):
    rows = []
    for path in tcd_paths:
        for r in read_csv(path):
            rows.append({
                "dataset": "tcd",
                "group": "tcd:" + r.get("family", "") + ":" + r["condition_id"],
                "target": (float(r["human_mos"]) - 1.0) / 4.0,
                "native": [float(r[x]) for x in NATIVE],
                "speech_q": 1.0 - float(r["visqol_speech"]),
                "audio_q": 1.0 - float(r["visqol_audio"]),
            })
    for r in read_csv(nisqa_path):
        rows.append({
            "dataset": "nisqa",
            "group": "nisqa:" + r["condition_id"],
            "target": (float(r["human_mos"]) - 1.0) / 4.0,
            "native": [float(r[x]) for x in NATIVE],
            "speech_q": 1.0 - float(r["visqol_speech"]),
            "audio_q": 1.0 - float(r["visqol_audio"]),
        })
    for r in read_csv(openace_path):
        rows.append({
            "dataset": "openace",
            "group": "openace:" + r["speaker"],
            "target": float(r["human_mushra"]) / 100.0,
            "native": [float(r[x]) for x in NATIVE],
            "speech_q": 1.0 - float(r["visqol_speech"]),
            "audio_q": 1.0 - float(r["visqol_audio"]),
        })
    return rows

def engineering_rows(path):
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    return [{
        "family": c["family"],
        "level": float(c["level"]),
        "label": c["label"],
        "native": native_from_result(c["result"]),
    } for c in payload["cases"]]

def assign_folds(rows):
    group_fold = {}
    for ds in sorted(set(r["dataset"] for r in rows)):
        groups = sorted(set(r["group"] for r in rows if r["dataset"] == ds))
        for i, group in enumerate(groups):
            group_fold[group] = i % FOLDS
    return np.asarray([group_fold[r["group"]] for r in rows], dtype=int)

def domain_weights(datasets):
    w = np.zeros(len(datasets), dtype=float)
    for ds in sorted(set(datasets)):
        mask = datasets == ds
        w[mask] = 1.0 / max(1, int(mask.sum()))
    return w / w.sum() * len(w)

def engineering_constraint_matrix(engineering, mean, scale):
    xe = np.vstack([basis(r["native"]) for r in engineering])
    ze = (xe - mean) / scale
    a = np.column_stack([np.ones(len(ze)), ze])
    rows, lower, upper = [], [], []

    identity = next(i for i, r in enumerate(engineering) if r["family"] == "clean")
    rows.append(a[identity]); lower.append(0.875); upper.append(np.inf)

    for i, r in enumerate(engineering):
        if r["family"] == "sample_rate_identity":
            rows.append(a[i]); lower.append(0.80); upper.append(np.inf)

    for i, r in enumerate(engineering):
        if r["family"] == "delay":
            rows.append(a[i] - a[identity])
            lower.append(-0.1125); upper.append(0.1125)

    for family in MONOTONIC_FAMILIES:
        inds = sorted(
            [i for i, r in enumerate(engineering) if r["family"] == family],
            key=lambda i: engineering[i]["level"],
        )
        for before, after in zip(inds, inds[1:]):
            rows.append(a[after] - a[before])
            lower.append(-np.inf); upper.append(0.0)

    return np.asarray(rows), np.asarray(lower), np.asarray(upper)

def fit(x, y, datasets, engineering, alpha):
    w = domain_weights(datasets)
    mean = np.average(x, axis=0, weights=w)
    scale = np.sqrt(np.average((x - mean) ** 2, axis=0, weights=w))
    scale[scale < 1e-8] = 1.0
    z = (x - mean) / scale
    a = np.column_stack([np.ones(len(z)), z])
    sw = np.sqrt(w)
    aw = a * sw[:, None]
    yw = y * sw

    reg = np.eye(a.shape[1])
    reg[0, 0] = 0.0
    h = aw.T @ aw + alpha * reg
    g = aw.T @ yw
    initial = np.linalg.solve(h, g)

    ca, lower, upper = engineering_constraint_matrix(engineering, mean, scale)

    def objective(theta):
        return 0.5 * theta @ h @ theta - g @ theta

    def gradient(theta):
        return h @ theta - g

    result = minimize(
        objective,
        initial,
        jac=gradient,
        constraints=[LinearConstraint(ca, lower, upper)],
        method="SLSQP",
        options={"maxiter": 1200, "ftol": 1e-9, "disp": False},
    )
    if not result.success:
        raise RuntimeError("constrained fit failed: " + result.message)
    return mean, scale, result.x, int(result.nit)

def predict(model, x):
    mean, scale, theta, _ = model
    a = np.column_stack([np.ones(len(x)), (x - mean) / scale])
    return np.clip(a @ theta, 0.0, 1.0)

def hybrid(native, speech, audio, blend):
    consensus = np.median(np.vstack([native, speech, audio]), axis=0)
    return np.clip((1.0 - blend) * native + blend * consensus, 0.0, 1.0)

def cross_validate(rows, engineering, alpha, expert_blend):
    x = np.vstack([basis(r["native"]) for r in rows])
    y = np.asarray([r["target"] for r in rows], dtype=float)
    datasets = np.asarray([r["dataset"] for r in rows])
    speech = np.asarray([r["speech_q"] for r in rows], dtype=float)
    audio = np.asarray([r["audio_q"] for r in rows], dtype=float)
    folds = assign_folds(rows)
    native = np.zeros(len(rows), dtype=float)
    iterations = []

    for fold in range(FOLDS):
        train = folds != fold
        valid = folds == fold
        model = fit(x[train], y[train], datasets[train], engineering, alpha)
        iterations.append(model[3])
        native[valid] = predict(model, x[valid])

    combined = hybrid(native, speech, audio, expert_blend)
    by_dataset, scores = {}, []
    for ds in sorted(set(datasets)):
        mask = datasets == ds
        by_dataset[ds] = {
            "native": metrics(y[mask], native[mask]),
            "hybrid": metrics(y[mask], combined[mask]),
        }
        scores.extend([
            by_dataset[ds]["hybrid"]["pearson"],
            by_dataset[ds]["hybrid"]["spearman"],
        ])
    return {
        "by_dataset": by_dataset,
        "objective": {
            "worst_correlation": float(min(scores)),
            "mean_correlation": float(np.mean(scores)),
        },
        "solver_iterations": iterations,
    }

def engineering_report(model, engineering):
    x = np.vstack([basis(r["native"]) for r in engineering])
    p = predict(model, x)
    out = {}
    for family in ["clean", "sample_rate_identity"] + MONOTONIC_FAMILIES:
        inds = [i for i, r in enumerate(engineering) if r["family"] == family]
        if not inds:
            continue
        inds = sorted(inds, key=lambda i: engineering[i]["level"])
        out[family] = [
            {"level": engineering[i]["level"], "label": engineering[i]["label"],
             "mos": float(1.0 + 4.0 * p[i])}
            for i in inds
        ]
    return out

def emit_cpp(path, model, expert_blend):
    mean, scale, theta, _ = model

    def array(name, values):
        body = ",\n    ".join(f"{float(v):.17g}" for v in values)
        return f"inline constexpr std::array<double, {len(values)}> {name} = {{{{\n    {body}\n}}}};\n"

    text = "#pragma once\n#include <array>\nnamespace openvq::phase4_model {\n"
    text += f'inline constexpr const char* kModelId = "{MODEL_ID}";\n'
    text += f"inline constexpr double kExpertBlend = {expert_blend:.17g};\n"
    text += f"inline constexpr double kIntercept = {theta[0]:.17g};\n"
    text += array("kMean", mean)
    text += array("kScale", scale)
    text += array("kWeights", theta[1:])
    text += "}\n"
    Path(path).write_text(text, encoding="utf-8")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tcd-train", required=True)
    ap.add_argument("--tcd-dev", required=True)
    ap.add_argument("--tcd-test", required=True)
    ap.add_argument("--nisqa", required=True)
    ap.add_argument("--openace", required=True)
    ap.add_argument("--engineering", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--cpp-out", required=True)
    args = ap.parse_args()

    rows = dataset_rows(
        [args.tcd_train, args.tcd_dev, args.tcd_test],
        args.nisqa, args.openace,
    )
    engineering = engineering_rows(args.engineering)

    grid, best = [], None
    for alpha in ALPHAS:
        for blend in EXPERT_BLENDS:
            cv = cross_validate(rows, engineering, alpha, blend)
            item = {"alpha": alpha, "expert_blend": blend, **cv}
            grid.append(item)
            key = (
                cv["objective"]["worst_correlation"],
                cv["objective"]["mean_correlation"],
                -blend, -alpha,
            )
            if best is None or key > best[0]:
                best = (key, item)

    selected = best[1]
    x = np.vstack([basis(r["native"]) for r in rows])
    y = np.asarray([r["target"] for r in rows], dtype=float)
    datasets = np.asarray([r["dataset"] for r in rows])
    final_model = fit(x, y, datasets, engineering, selected["alpha"])

    result = {
        "model_id": MODEL_ID,
        "status": "development candidate; external holdouts remain blinded",
        "feature_order": NATIVE,
        "basis_order": basis_names(),
        "target_mapping": {
            "tcd_nisqa": "(MOS-1)/4",
            "openace": "MUSHRA/100",
        },
        "dataset_counts": {
            ds: sum(r["dataset"] == ds for r in rows)
            for ds in sorted(set(datasets))
        },
        "engineering_constraints": {
            "identity_mos_min": 4.5,
            "sample_rate_identity_mos_min": 4.2,
            "delay_max_abs_delta_mos": 0.45,
            "monotonic_nonincreasing_families": MONOTONIC_FAMILIES,
        },
        "selection_rule": (
            "maximize the weakest Pearson/Spearman correlation across TCD, "
            "NISQA P501 and OpenACE under fixed engineering inequality constraints; "
            "optional ViSQOL consensus capped at 40 percent"
        ),
        "selected": selected,
        "grid": grid,
        "solver_iterations_full_fit": final_model[3],
        "engineering_full_fit": engineering_report(final_model, engineering),
        "expert_blend": selected["expert_blend"],
        "native_model": {
            "alpha": selected["alpha"],
            "mean": final_model[0].tolist(),
            "scale": final_model[1].tolist(),
            "coef": final_model[2].tolist(),
        },
        "warning": (
            "TCD, NISQA P501, OpenACE and the synthetic engineering matrix are "
            "development data for this candidate. New untouched subjective corpora "
            "are required before a generalization or POLQA-parity claim."
        ),
    }

    Path(args.out).write_text(
        json.dumps(result, indent=2, allow_nan=False) + "\n", encoding="utf-8"
    )
    emit_cpp(args.cpp_out, final_model, selected["expert_blend"])
    print(json.dumps({
        "model_id": MODEL_ID,
        "dataset_counts": result["dataset_counts"],
        "selected": selected,
        "solver_iterations_full_fit": final_model[3],
    }, indent=2, allow_nan=False))

if __name__ == "__main__":
    main()
