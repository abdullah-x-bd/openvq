#!/usr/bin/env python3
"""Score the unchanged Phase 3 native mapper and export label-free features."""
import argparse
import csv
import json
import math
import subprocess
from concurrent.futures import ThreadPoolExecutor


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("input")
    ap.add_argument("output")
    ap.add_argument("--cli", default="./build/openvq_cli")
    ap.add_argument("--jobs", type=int, default=2)
    a = ap.parse_args()
    with open(a.input, newline="") as f:
        rows = list(csv.DictReader(f))
    if len({r["row_id"] for r in rows}) != len(rows) or not rows:
        raise ValueError("empty or duplicate rows")
    def clamp(v):
        return min(1., max(0., float(v)))
    def one(r):
        obj = json.loads(subprocess.check_output([
            a.cli, r["reference"], r["degraded"],
            "--visqol-speech-score", r["visqol_speech_mos"],
            "--visqol-audio-score", r["visqol_audio_mos"]], text=True))
        if not obj.get("hybrid_applied") or not math.isfinite(obj["mos"]):
            raise ValueError("native frozen hybrid not applied")
        d, q = obj["dimensions"], obj["advanced"]
        feats = {
            "base": (5-obj["base_mos"])/4,
            "missing": obj["missing_disturbance"], "added": obj["added_disturbance"],
            **{k: (5-d[k])/4 for k in ("coloration", "noisiness", "discontinuity", "loudness")},
            "clipping": obj["clipping_ratio"]*40, "bad_section": obj["bad_section_fraction"],
            "multi_resolution": 1-q["multi_resolution_similarity"],
            "temporal": 1-q["temporal_envelope_similarity"],
            "modulation": 1-q["modulation_similarity"],
            "asymmetry": q["asymmetric_disturbance"], "tilt": q["spectral_tilt_error"],
            "level": q["active_level_delta_db"]/18, "bad_interval": q["bad_interval_severity"],
            "echo": q["echo_score"], "choppiness": q["choppiness_score"],
            "residual": q["residual_intrusion"],
            "visqol_speech": (5-float(r["visqol_speech_mos"]))/4,
            "visqol_audio": (5-float(r["visqol_audio_mos"]))/4,
        }
        return {**r, "openvq_mos": obj["mos"],
                **{"feature_"+k: clamp(v) for k, v in feats.items()}}
    with ThreadPoolExecutor(max_workers=a.jobs) as pool:
        out = list(pool.map(one, rows))
    with open(a.output, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(out[0])); w.writeheader(); w.writerows(out)
    print(f"Scored {len(out)} unique pairs with frozen Phase 3")


if __name__ == "__main__":
    main()
