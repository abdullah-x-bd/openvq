#!/usr/bin/env python3
"""Prepare the frozen EARS-EMO-OpenACE objective comparison manifest."""
import argparse
import csv
from pathlib import Path

CODECS = ("EVS", "LC3", "LC3Plus", "Opus")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("root")
    ap.add_argument("output")
    args = ap.parse_args()

    root = Path(args.root)
    metadata = root / "metadata.csv"
    if not metadata.exists():
        raise SystemExit(f"missing metadata: {metadata}")

    with metadata.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    selected = []
    for row in rows:
        if row.get("codec") not in CODECS:
            continue
        ref = root / row["reference_file"]
        deg = root / row["distorted_file"]
        if not ref.is_file():
            raise SystemExit(f"missing reference audio: {ref}")
        if not deg.is_file():
            raise SystemExit(f"missing distorted audio: {deg}")
        out = dict(row)
        out["reference"] = str(ref)
        out["degraded"] = str(deg)
        out["family"] = "codec"
        out["condition_id"] = row["codec"]
        out["filename"] = row["distorted_file"]
        selected.append(out)

    if len(selected) != 144:
        raise SystemExit(f"expected 144 coded samples, found {len(selected)}")

    polqa_n = sum(bool(r.get("polqa_score", "").strip()) for r in selected)
    if polqa_n != 143:
        raise SystemExit(f"expected 143 published POLQA scores, found {polqa_n}")

    fields = list(selected[0].keys())
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(selected)

    print(f"prepared {len(selected)} OpenACE coded samples; POLQA available for {polqa_n}")

if __name__ == "__main__":
    main()
