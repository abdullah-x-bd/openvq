#!/usr/bin/env python3
"""Extract OpenVQ features from a labeled audio manifest.

Input CSV:
reference,degraded,human_mos[,visqol_mos][,polqa_mos]

For second-stage fitting, pass --calibration with the fitted base calibration.
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
    ap.add_argument("--calibration")
    args = ap.parse_args()

    fields = [
        "human_mos",
        "missing", "added", "coloration", "noisiness",
        "discontinuity", "loudness", "clipping", "bad_section",
        "base_penalty",
        "advanced_multi_resolution",
        "advanced_temporal",
        "advanced_modulation",
        "advanced_asymmetry",
        "advanced_tilt",
        "advanced_level",
        "advanced_bad_interval",
        "advanced_echo",
        "advanced_choppiness",
        "advanced_residual_intrusion",
        "visqol_mos", "polqa_mos", "reference", "degraded"
    ]

    with open(args.manifest, newline="", encoding="utf-8") as src, \
         open(args.output, "w", newline="", encoding="utf-8") as dst:
        reader = csv.DictReader(src)
        writer = csv.DictWriter(dst, fieldnames=fields)
        writer.writeheader()

        for row in reader:
            cmd = [args.cli, row["reference"], row["degraded"]]
            if row.get("visqol_mos", ""):
                cmd += ["--visqol-score", row["visqol_mos"]]
            if args.calibration:
                cmd += ["--calibration", args.calibration]

            result = json.loads(subprocess.check_output(cmd, text=True))
            dims = result["dimensions"]
            advanced = result["advanced"]

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
                "base_penalty": max(0.0, min(4.0, 5.0 - float(result["base_mos"]))),
                "advanced_multi_resolution": clamp(
                    1.0 - float(advanced["multi_resolution_similarity"])),
                "advanced_temporal": clamp(
                    1.0 - float(advanced["temporal_envelope_similarity"])),
                "advanced_modulation": clamp(
                    1.0 - float(advanced["modulation_similarity"])),
                "advanced_asymmetry": clamp(
                    float(advanced["asymmetric_disturbance"])),
                "advanced_tilt": clamp(
                    float(advanced["spectral_tilt_error"])),
                "advanced_level": clamp(
                    float(advanced["active_level_delta_db"]) / 18.0),
                "advanced_bad_interval": clamp(
                    float(advanced["bad_interval_severity"])),
                "advanced_echo": clamp(
                    float(advanced.get("echo_score", 0.0))),
                "advanced_choppiness": clamp(
                    float(advanced.get("choppiness_score", 0.0))),
                "advanced_residual_intrusion": clamp(
                    float(advanced.get("residual_intrusion", 0.0))),
                "visqol_mos": row.get("visqol_mos", ""),
                "polqa_mos": row.get("polqa_mos", ""),
                "reference": row["reference"],
                "degraded": row["degraded"],
            })

if __name__ == "__main__":
    main()
