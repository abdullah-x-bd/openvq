#!/usr/bin/env python3
"""Extract native OpenVQ and expert features for Phase 4 OpenACE forensics."""
import argparse
import csv
import json
import os
import subprocess
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
import soundfile as sf

def clamp(x, lo=0.0, hi=1.0):
    return max(lo, min(hi, x))

def convert_pcm16(src, dst):
    audio, sr = sf.read(src, dtype="float64", always_2d=True)
    mono = audio.mean(axis=1)
    sf.write(dst, mono, sr, subtype="PCM_16")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("manifest")
    ap.add_argument("output")
    ap.add_argument("--cli", default="./build/openvq_cli")
    ap.add_argument("--jobs", type=int, default=max(1, min(4, os.cpu_count() or 1)))
    args = ap.parse_args()

    with open(args.manifest, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    with tempfile.TemporaryDirectory(prefix="openvq-phase4-openace-") as td:
        td = Path(td)
        converted = {}
        for row in rows:
            for key in ("reference", "degraded"):
                src = row[key]
                if src not in converted:
                    dst = td / f"{len(converted):04d}.wav"
                    convert_pcm16(src, dst)
                    converted[src] = str(dst)

        def one(row):
            obj = json.loads(subprocess.check_output(
                [args.cli, converted[row["reference"]], converted[row["degraded"]]],
                text=True,
            ))
            d = obj["dimensions"]
            q = obj["advanced"]
            return {
                "speaker": row["speaker"],
                "emotion": row["emotion"],
                "codec": row["codec"],
                "filename": row["distorted_file"],
                "human_mushra": float(row["distorted_mushra_rating"]),
                "polqa_score": row.get("polqa_score", ""),
                "published_visqol_score": row.get("visqol_score", ""),
                "visqol_speech_mos": float(row["visqol_speech_mos"]),
                "visqol_audio_mos": float(row["visqol_audio_mos"]),
                "base": clamp((5-float(obj["base_mos"]))/4),
                "missing": clamp(float(obj["missing_disturbance"])),
                "added": clamp(float(obj["added_disturbance"])),
                "coloration": clamp((5-float(d["coloration"]))/4),
                "noisiness": clamp((5-float(d["noisiness"]))/4),
                "discontinuity": clamp((5-float(d["discontinuity"]))/4),
                "loudness": clamp((5-float(d["loudness"]))/4),
                "clipping": clamp(float(obj["clipping_ratio"])*40),
                "bad_section": clamp(float(obj["bad_section_fraction"])),
                "multi_resolution": clamp(1-float(q["multi_resolution_similarity"])),
                "temporal": clamp(1-float(q["temporal_envelope_similarity"])),
                "modulation": clamp(1-float(q["modulation_similarity"])),
                "asymmetry": clamp(float(q["asymmetric_disturbance"])),
                "tilt": clamp(float(q["spectral_tilt_error"])),
                "level": clamp(float(q["active_level_delta_db"])/18),
                "bad_interval": clamp(float(q["bad_interval_severity"])),
                "echo": clamp(float(q.get("echo_score",0))),
                "choppiness": clamp(float(q.get("choppiness_score",0))),
                "residual": clamp(float(q.get("residual_intrusion",0))),
                "visqol_speech": clamp((5-float(row["visqol_speech_mos"]))/4),
                "visqol_audio": clamp((5-float(row["visqol_audio_mos"]))/4),
            }

        out = []
        with ThreadPoolExecutor(max_workers=args.jobs) as pool:
            for i, item in enumerate(pool.map(one, rows), 1):
                out.append(item)
                if i % 24 == 0 or i == len(rows):
                    print(f"Phase 4 OpenACE features {i} / {len(rows)}", flush=True)

    with open(args.output, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(out[0].keys()))
        w.writeheader()
        w.writerows(out)

if __name__ == "__main__":
    main()
