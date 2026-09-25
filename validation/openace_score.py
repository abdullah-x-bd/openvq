#!/usr/bin/env python3
"""Score an OpenACE ViSQOL-augmented manifest with frozen native Phase 3."""
import argparse
import csv
import json
import os
import subprocess
from concurrent.futures import ThreadPoolExecutor

MODEL_ID = "phase3-tcd-only-2026-09-24-f099129"

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("manifest")
    ap.add_argument("output")
    ap.add_argument("--cli", default="./build/openvq_cli")
    ap.add_argument("--jobs", type=int, default=max(1, min(4, os.cpu_count() or 1)))
    args = ap.parse_args()

    with open(args.manifest, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    def one(row):
        cmd = [
            args.cli,
            row["reference"],
            row["degraded"],
            "--visqol-speech-score",
            row["visqol_speech_mos"],
            "--visqol-audio-score",
            row["visqol_audio_mos"],
        ]
        obj = json.loads(subprocess.check_output(cmd, text=True))
        if not obj.get("hybrid_applied"):
            raise RuntimeError("frozen Phase-3 hybrid was not applied")
        if obj.get("hybrid_model") != MODEL_ID:
            raise RuntimeError(
                f"unexpected hybrid model {obj.get('hybrid_model')!r}; expected {MODEL_ID!r}"
            )
        out = dict(row)
        out["openvq_mos"] = obj["mos"]
        out["openvq_model_id"] = obj["hybrid_model"]
        return out

    scored = []
    with ThreadPoolExecutor(max_workers=args.jobs) as pool:
        for i, row in enumerate(pool.map(one, rows), 1):
            scored.append(row)
            if i % 24 == 0:
                print(f"OpenVQ scored {i} / {len(rows)}", flush=True)

    fields = list(scored[0].keys())
    with open(args.output, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(scored)

if __name__ == "__main__":
    main()
