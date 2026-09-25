#!/usr/bin/env python3
"""Deterministic engineering validation matrix for OpenVQ.

This suite is deliberately independent of subjective calibration. It tests
properties that a telecom full-reference perceptual metric should satisfy:
stability, sensible monotonic response, alignment tolerance, sample-rate
handling, bounded output, determinism, and crash resistance.
"""
from __future__ import annotations

import argparse
import array
import json
import math
import os
import random
import statistics
import subprocess
import tempfile
import wave
from dataclasses import dataclass, asdict
from pathlib import Path


SR = 48000
DURATION_S = 6.0
CLI_EXTRA = []


@dataclass
class Case:
    family: str
    level: float
    label: str
    mos: float
    confidence: float
    delay_ms: float
    result: dict


def clamp(x, lo=-1.0, hi=1.0):
    return max(lo, min(hi, x))


def speech_like(sr=SR, seconds=DURATION_S):
    n = int(sr * seconds)
    out = []
    rng = random.Random(20260924)
    phases = [rng.random() * 2 * math.pi for _ in range(8)]
    freqs = [115, 187, 331, 710, 1510, 2810, 5150, 9200]
    amps = [0.13, 0.16, 0.11, 0.09, 0.065, 0.045, 0.028, 0.016]

    for i in range(n):
        t = i / sr
        # quasi-syllabic envelope with deliberate low-energy gaps
        syll = 0.30 + 0.70 * max(0.0, math.sin(2 * math.pi * 2.35 * t)) ** 0.7
        phrase = 1.0 if (i // int(0.88 * sr)) % 5 != 4 else 0.08
        breath = 0.012 * math.sin(2 * math.pi * 37 * t)
        s = sum(
            a * math.sin(2 * math.pi * f * t + p)
            for a, f, p in zip(amps, freqs, phases)
        )
        # mild AM and FM-like variation to avoid a stationary toy signal
        s *= syll * phrase * (0.90 + 0.10 * math.sin(2 * math.pi * 0.37 * t))
        s += breath * syll
        out.append(clamp(s * 1.8))
    return out


def write_wav(path: Path, samples, sr=SR):
    pcm = array.array("h", [int(clamp(v, -0.999969, 0.999969) * 32768) for v in samples])
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(pcm.tobytes())


def linear_resample(samples, in_sr, out_sr):
    if in_sr == out_sr:
        return list(samples)
    n = int(round(len(samples) * out_sr / in_sr))
    out = []
    for i in range(n):
        p = i * in_sr / out_sr
        j = int(p)
        f = p - j
        if j >= len(samples) - 1:
            out.append(samples[-1])
        else:
            out.append(samples[j] * (1 - f) + samples[j + 1] * f)
    return out


def delay(samples, sr, ms):
    return [0.0] * int(sr * ms / 1000.0) + list(samples)


def dropout(samples, sr, duration_ms, start_s=2.15):
    x = list(samples)
    b = int(start_s * sr)
    e = min(len(x), b + int(duration_ms * sr / 1000))
    for i in range(b, e):
        x[i] = 0.0
    return x


def repeated_dropouts(samples, sr, duration_ms, count):
    x = list(samples)
    starts = [0.9 + i * 0.8 for i in range(count)]
    for s in starts:
        x = dropout(x, sr, duration_ms, s)
    return x


def add_noise(samples, snr_db, seed=42):
    rng = random.Random(seed)
    rms = math.sqrt(sum(v * v for v in samples) / len(samples))
    sigma = rms / (10 ** (snr_db / 20.0))
    return [clamp(v + rng.gauss(0, sigma)) for v in samples]


def clip_signal(samples, threshold):
    return [clamp(v, -threshold, threshold) for v in samples]


def gain(samples, db):
    g = 10 ** (db / 20.0)
    return [clamp(v * g) for v in samples]


def one_pole_lowpass(samples, sr, cutoff):
    # cascaded three times to make bandwidth effects visible while staying stable
    a = math.exp(-2 * math.pi * cutoff / sr)
    y = list(samples)
    for _ in range(3):
        z = 0.0
        stage = []
        for v in y:
            z = (1 - a) * v + a * z
            stage.append(z)
        y = stage
    return y


def clock_drift(samples, ppm):
    # A receiver clock offset changes apparent duration. Positive ppm makes the
    # degraded stream slightly longer before it is stamped at the original SR.
    factor = 1.0 + ppm * 1e-6
    virtual_sr = SR / factor
    return linear_resample(samples, SR, virtual_sr)


def time_scale(samples, factor):
    # factor > 1 produces longer output.
    return linear_resample(samples, SR, SR * factor)


def run(cli, ref_path, deg_path):
    raw = subprocess.check_output([cli, str(ref_path), str(deg_path)] + CLI_EXTRA, text=True)
    obj = json.loads(raw)
    if not 1.0 <= float(obj["mos"]) <= 5.0:
        raise AssertionError(f"MOS outside range: {obj['mos']}")
    if not 0.0 <= float(obj["confidence"]) <= 1.0:
        raise AssertionError(f"confidence outside range: {obj['confidence']}")
    return obj


def rank_corr(xs, ys):
    def ranks(vals):
        order = sorted(range(len(vals)), key=lambda i: vals[i])
        r = [0.0] * len(vals)
        i = 0
        while i < len(vals):
            j = i + 1
            while j < len(vals) and vals[order[j]] == vals[order[i]]:
                j += 1
            avg = (i + j - 1) / 2.0
            for k in range(i, j):
                r[order[k]] = avg
            i = j
        return r

    a, b = ranks(xs), ranks(ys)
    ma, mb = statistics.mean(a), statistics.mean(b)
    num = sum((x-ma)*(y-mb) for x,y in zip(a,b))
    den = math.sqrt(sum((x-ma)**2 for x in a) * sum((y-mb)**2 for y in b))
    return num / den if den else 0.0


def add_case(cases, cli, tmp, ref_path, family, level, label, samples, sr=SR):
    path = tmp / f"{family}_{label}.wav"
    safe = str(path).replace(" ", "_")
    path = Path(safe)
    write_wav(path, samples, sr)
    r = run(cli, ref_path, path)
    cases.append(Case(
        family=family,
        level=float(level),
        label=label,
        mos=float(r["mos"]),
        confidence=float(r["confidence"]),
        delay_ms=float(r.get("delay_ms", 0.0)),
        result=r,
    ))


def monotonic_report(cases, family, descending_with_level=True):
    rows = sorted((c for c in cases if c.family == family), key=lambda c: c.level)
    levels = [c.level for c in rows]
    mos = [c.mos for c in rows]
    rho = rank_corr(levels, mos)
    expected_sign = -1 if descending_with_level else 1
    violations = 0
    for a, b in zip(rows, rows[1:]):
        if descending_with_level:
            if b.mos > a.mos + 0.12:
                violations += 1
        else:
            if b.mos < a.mos - 0.12:
                violations += 1
    return {
        "family": family,
        "rho": rho,
        "expected_sign": expected_sign,
        "violations_gt_0.12_mos": violations,
        "rows": [{"level": c.level, "label": c.label, "mos": c.mos} for c in rows],
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cli", default="./build/openvq_cli")
    ap.add_argument("--out", default="validation-results.json")
    ap.add_argument("--fuzz", type=int, default=120)
    ap.add_argument("--phase4", action="store_true")
    args = ap.parse_args()
    global CLI_EXTRA
    CLI_EXTRA = ["--phase4"] if args.phase4 else []

    cases = []
    failures = []
    base = speech_like()

    with tempfile.TemporaryDirectory(prefix="openvq-validation-") as td:
        tmp = Path(td)
        ref = tmp / "reference.wav"
        write_wav(ref, base)

        clean = run(args.cli, ref, ref)
        cases.append(Case("clean", 0, "identity", float(clean["mos"]),
                          float(clean["confidence"]), float(clean["delay_ms"]), clean))

        # Determinism
        for _ in range(4):
            again = run(args.cli, ref, ref)
            if again != clean:
                failures.append("non-deterministic identity result")

        # Pure transport delay should not materially change listening quality.
        for ms in [25, 50, 100, 200, 400, 800, 1200]:
            add_case(cases, args.cli, tmp, ref, "delay", ms, f"{ms}ms", delay(base, SR, ms))

        # Increasing missing-speech duration.
        for ms in [10, 20, 40, 80, 160, 320, 640, 1000]:
            add_case(cases, args.cli, tmp, ref, "dropout", ms, f"{ms}ms", dropout(base, SR, ms))

        # Increasing number of short dropouts.
        for count in [1, 2, 3, 4, 5]:
            add_case(cases, args.cli, tmp, ref, "dropout_count", count,
                     f"{count}x80ms", repeated_dropouts(base, SR, 80, count))

        # Noise. Severity level is inverse SNR, so larger means worse.
        for snr in [40, 30, 20, 15, 10, 5, 0]:
            add_case(cases, args.cli, tmp, ref, "noise", 50-snr,
                     f"snr{snr}", add_noise(base, snr))

        # Lower cutoff is worse. Level is inverse cutoff for monotonic checks.
        for cutoff in [18000, 14000, 10000, 7000, 4000, 3400, 2200]:
            add_case(cases, args.cli, tmp, ref, "lowpass", 20000-cutoff,
                     f"{cutoff}hz", one_pole_lowpass(base, SR, cutoff))

        # More restrictive clipping is worse.
        for threshold in [0.95, 0.70, 0.50, 0.35, 0.25, 0.15, 0.08]:
            add_case(cases, args.cli, tmp, ref, "clipping", 1-threshold,
                     f"thr{threshold}", clip_signal(base, threshold))

        # Absolute-level mismatch.
        for db in [-1, -3, -6, -9, -12, -18, -24]:
            add_case(cases, args.cli, tmp, ref, "attenuation", abs(db),
                     f"{db}db", gain(base, db))

        # Clock-rate mismatch.
        for ppm in [25, 50, 100, 250, 500, 1000, 2000]:
            add_case(cases, args.cli, tmp, ref, "clock_drift", ppm,
                     f"{ppm}ppm", clock_drift(base, ppm))

        # Time-scale distortion, much larger than a clock error.
        for pct in [0.25, 0.5, 1, 2, 4, 8]:
            factor = 1 + pct / 100
            add_case(cases, args.cli, tmp, ref, "time_scale", pct,
                     f"plus{pct}pct", time_scale(base, factor))

        # Clean equivalent material at different input sample rates.
        for sr in [8000, 16000, 24000, 32000, 44100, 48000]:
            low = linear_resample(base, SR, sr)
            # Both reference and degraded are generated from the same low-rate signal.
            rp = tmp / f"sr_ref_{sr}.wav"
            dp = tmp / f"sr_deg_{sr}.wav"
            write_wav(rp, low, sr)
            write_wav(dp, low, sr)
            r = run(args.cli, rp, dp)
            cases.append(Case("sample_rate_identity", sr, str(sr),
                              float(r["mos"]), float(r["confidence"]),
                              float(r["delay_ms"]), r))

        # Mixed telecom-style impairments.
        mixes = [
            ("mild", add_noise(dropout(base, SR, 20), 30)),
            ("moderate", add_noise(dropout(one_pole_lowpass(base, SR, 7000), SR, 80), 18)),
            ("severe", add_noise(dropout(one_pole_lowpass(gain(base, -8), SR, 3400), SR, 320), 8)),
        ]
        for idx, (name, x) in enumerate(mixes, 1):
            add_case(cases, args.cli, tmp, ref, "mixed", idx, name, x)

        # Randomized fuzz. Expected property here is robustness and valid ranges,
        # not monotonic ordering.
        rng = random.Random(123456)
        for i in range(args.fuzz):
            x = list(base)
            if rng.random() < 0.75:
                x = add_noise(x, rng.uniform(0, 45), seed=1000+i)
            if rng.random() < 0.65:
                x = gain(x, rng.uniform(-30, 8))
            if rng.random() < 0.60:
                x = dropout(x, SR, rng.uniform(1, 1100), rng.uniform(0.3, 4.8))
            if rng.random() < 0.45:
                x = clip_signal(x, rng.uniform(0.05, 0.95))
            if rng.random() < 0.40:
                x = one_pole_lowpass(x, SR, rng.uniform(1800, 18000))
            if rng.random() < 0.25:
                x = delay(x, SR, rng.uniform(0, 1400))
            add_case(cases, args.cli, tmp, ref, "fuzz", i, f"{i:03d}", x)

    reports = []
    for fam in ["dropout", "dropout_count", "noise", "lowpass",
                "clipping", "attenuation", "clock_drift", "time_scale", "mixed"]:
        reports.append(monotonic_report(cases, fam, True))

    clean_mos = next(c.mos for c in cases if c.family == "clean")
    delay_scores = [c.mos for c in cases if c.family == "delay"]
    sr_scores = [c.mos for c in cases if c.family == "sample_rate_identity"]

    summary = {
        "candidate": "OpenVQ Phase 4 engineering matrix" if args.phase4 else "OpenVQ validation engineering matrix",
        "total_cases": len(cases),
        "fuzz_cases": args.fuzz,
        "clean_mos": clean_mos,
        "delay_invariance_max_delta_from_clean": max(abs(x-clean_mos) for x in delay_scores),
        "sample_rate_identity_min_mos": min(sr_scores),
        "sample_rate_identity_max_mos": max(sr_scores),
        "monotonic_reports": reports,
        "failures": failures,
    }

    # Hard engineering assertions. These do not claim subjective validity.
    if clean_mos < 4.5:
        failures.append(f"identity MOS too low: {clean_mos:.3f}")
    if summary["delay_invariance_max_delta_from_clean"] > 0.45:
        failures.append(
            "pure delay changes MOS by more than 0.45: "
            f"{summary['delay_invariance_max_delta_from_clean']:.3f}"
        )
    if min(sr_scores) < 4.2:
        failures.append(
            f"identity score below 4.2 at some supported sample rate: {min(sr_scores):.3f}"
        )

    # We permit occasional local reversals, but not grossly anti-monotonic behavior.
    for rep in reports:
        if rep["rho"] > -0.20:
            failures.append(
                f"{rep['family']} severity is not negatively associated with MOS "
                f"(Spearman {rep['rho']:.3f})"
            )

    summary["failures"] = failures

    payload = {
        "summary": summary,
        "cases": [asdict(c) for c in cases],
    }
    Path(args.out).write_text(json.dumps(payload, indent=2), encoding="utf-8")

    print(json.dumps(summary, indent=2))
    if failures:
        print("\nENGINEERING VALIDATION FAILURES:")
        for f in failures:
            print(" -", f)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
