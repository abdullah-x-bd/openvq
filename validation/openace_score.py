#!/usr/bin/env python3
"""Score an OpenACE ViSQOL-augmented manifest with frozen native Phase 3."""
import argparse
import csv
import json
import os
import subprocess
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import soundfile as sf

MODEL_ID = "phase3-tcd-only-2026-09-24-f099129"

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

    with tempfile.TemporaryDirectory(prefix="openvq-openace-pcm16-") as td:
        td = Path(td)
        converted = {}

        # OpenACE WAVs can use a PCM subtype not accepted by the frozen native
        # loader. Convert only the container/sample representation to mono PCM16
        # at the original sample rate. This does not alter the frozen model,
        # features, ViSQOL scores, or evaluation criteria.
        unique = []
        for row in rows:
            for key in ("reference", "degraded"):
                src = row[key]
                if src not in converted:
                    unique.append(src)
                    converted[src] = str(td / f"{len(converted):04d}.wav")

        for i, src in enumerate(unique, 1):
            convert_pcm16(src, converted[src])
            if i % 48 == 0 or i == len(unique):
                print(f"PCM16 compatibility conversion {i} / {len(unique)}", flush=True)

        def one(row):
            cmd = [
                args.cli,
                converted[row["reference"]],
                converted[row["degraded"]],
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
                if i % 24 == 0 or i == len(rows):
                    print(f"OpenVQ scored {i} / {len(rows)}", flush=True)

    fields = list(scored[0].keys())
    with open(args.output, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(scored)

if __name__ == "__main__":
    main()
