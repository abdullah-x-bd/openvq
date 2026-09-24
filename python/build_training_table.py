#!/usr/bin/env python3
"""Extract OpenVQ degradation features from a labeled manifest.

Input CSV:
reference,degraded,human_mos[,visqol_mos][,polqa_mos]

Output CSV is directly consumable by calibrate.py.
"""
import argparse
import csv
import json
import subprocess

def clamp(x, lo=0.0, hi=1.0):
    return max(lo, min(hi, x))

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("manifest")
    ap.add_argument("output")
    ap.add_argument("--cli", default="./build/openvq_cli")
    args = ap.parse_args()

    fields = [
        "human_mos", "missing", "added", "coloration", "noisiness",
        "discontinuity", "loudness", "clipping", "bad_section",
        "visqol_mos", "polqa_mos", "reference", "degraded"
    ]

    with open(args.manifest, newline="", encoding="utf-8") as src, \
         open(args.output, "w", newline="", encoding="utf-8") as dst:
        reader = csv.DictReader(src)
        writer = csv.DictWriter(dst, fieldnames=fields)
        writer.writeheader()

        for row in reader:
            result = json.loads(subprocess.check_output(
                [args.cli, row["reference"], row["degraded"]], text=True))
            dims = result["dimensions"]
            writer.writerow({
                "human_mos": row["human_mos"],
                "missing": clamp(float(result["missing_disturbance"])),
                "added": clamp(float(result["added_disturbance"])),
                "coloration": clamp((5.0 - float(dims["coloration"])) / 4.0),
                "noisiness": clamp((5.0 - float(dims["noisiness"])) / 4.0),
                "discontinuity": clamp((5.0 - float(dims["discontinuity"])) / 4.0),
                "loudness": clamp((5.0 - float(dims["loudness"])) / 4.0),
                "clipping": clamp(float(result["clipping_ratio"]) * 40.0),
                "bad_section": clamp(float(result["bad_section_fraction"])),
                "visqol_mos": row.get("visqol_mos", ""),
                "polqa_mos": row.get("polqa_mos", ""),
                "reference": row["reference"],
                "degraded": row["degraded"],
            })

if __name__ == "__main__":
    main()
