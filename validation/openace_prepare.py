#!/usr/bin/env python3
"""Download pinned, public OpenACE audio and preserve pair provenance."""
import argparse
import csv
import hashlib
import io
import json
import math
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import soundfile as sf

REVISION = "31acd607eb4fb1d136677fab2aa6ced0af0e1194"
BASE = f"https://huggingface.co/datasets/mcernak/EARS-EMO-OpenACE/resolve/{REVISION}/"
CODECS = {"Opus", "EVS", "LC3", "LC3Plus"}


def digest(data):
    return hashlib.sha256(data).hexdigest()


def download(relative, root):
    relative_path = Path(relative)
    if relative_path.is_absolute() or ".." in relative_path.parts:
        raise ValueError(f"unsafe relative path: {relative}")
    path = root / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        for attempt in range(4):
            try:
                with urllib.request.urlopen(BASE + relative, timeout=90) as response:
                    data = response.read()
                tmp = path.with_suffix(path.suffix + ".part")
                tmp.write_bytes(data)
                tmp.replace(path)
                break
            except Exception:
                if attempt == 3:
                    raise
                time.sleep(attempt + 1)
    return path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("outdir", type=Path)
    ap.add_argument("--shard", type=int, default=0)
    ap.add_argument("--shards", type=int, default=1)
    args = ap.parse_args()
    if not 0 <= args.shard < args.shards:
        ap.error("invalid shard")
    root = args.outdir.resolve()
    raw = root / "original"
    meta = download("metadata.csv", raw).read_bytes()
    all_rows = list(csv.DictReader(io.StringIO(meta.decode("utf-8-sig"))))
    rows = sorted((r for r in all_rows if r["codec"] in CODECS),
                  key=lambda r: r["distorted_file"])
    if len(rows) != 144 or len({r["distorted_file"] for r in rows}) != 144:
        raise ValueError("expected exactly 144 unique coded recordings")
    selected = rows[args.shard::args.shards]
    paths = sorted({r[k] for r in selected for k in ("reference_file", "distorted_file")})

    def one(relative):
        source = download(relative, raw)
        x, sr = sf.read(source, dtype="float32", always_2d=True)
        if x.shape[1] != 1 or sr != 48000 or len(x) == 0:
            raise ValueError(f"unexpected audio format: {relative}")
        dest = root / "native" / relative
        dest.parent.mkdir(parents=True, exist_ok=True)
        sf.write(dest, x, sr, subtype="FLOAT")
        return relative, {"path": str(dest), "sha256": digest(source.read_bytes()),
                          "native_sha256": digest(dest.read_bytes()),
                          "sample_rate": sr, "samples": len(x)}

    with ThreadPoolExecutor(max_workers=8) as pool:
        audio = dict(pool.map(one, paths))
    manifest = []
    for r in selected:
        y = float(r["distorted_mushra_rating"])
        if not math.isfinite(y) or not 0 <= y <= 100:
            raise ValueError("invalid human MUSHRA label")
        ref, deg = audio[r["reference_file"]], audio[r["distorted_file"]]
        manifest.append({
            "row_id": r["distorted_file"], "reference": ref["path"],
            "degraded": deg["path"], "speaker": r["speaker"], "emotion": r["emotion"],
            "codec": r["codec"], "human_mushra": y,
            "condition_id": r["speaker"] + "/" + r["emotion"],
            "family": "EARS_EMO_OPENACE", "filename": r["distorted_file"],
            "published_polqa": r["polqa_score"],
            "published_visqol": r["visqol_score"],
            "reference_sha256": ref["sha256"], "degraded_sha256": deg["sha256"],
            "reference_native_sha256": ref["native_sha256"],
            "degraded_native_sha256": deg["native_sha256"],
        })
    out = root / f"shard-{args.shard}-manifest.csv"
    with out.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(manifest[0]))
        w.writeheader()
        w.writerows(manifest)
    provenance = {"dataset": "mcernak/EARS-EMO-OpenACE", "revision": REVISION,
                  "metadata_sha256": digest(meta), "rows": len(manifest),
                  "original_audio": "unaltered author files",
                  "native_audio": "float32 WAV, unchanged sample rate and signal level",
                  "shard": args.shard, "shards": args.shards}
    (root / f"shard-{args.shard}-provenance.json").write_text(json.dumps(provenance, indent=2) + "\n")
    print(json.dumps(provenance, indent=2))


if __name__ == "__main__":
    main()
