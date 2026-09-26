#!/usr/bin/env python3
"""Convert all full-reference manifest audio to mono PCM16 without changing labels."""
import argparse,csv,tempfile
from pathlib import Path
import soundfile as sf

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("manifest");ap.add_argument("output");ap.add_argument("audio_dir")
    a=ap.parse_args()
    rows=list(csv.DictReader(open(a.manifest,newline="",encoding="utf-8")))
    outdir=Path(a.audio_dir);outdir.mkdir(parents=True,exist_ok=True)
    cache={}
    for r in rows:
        for key in ["reference","degraded"]:
            src=r[key]
            if src not in cache:
                x,sr=sf.read(src,dtype="float64",always_2d=True)
                mono=x.mean(axis=1)
                dst=outdir/f"{len(cache):05d}.wav"
                sf.write(dst,mono,sr,subtype="PCM_16")
                cache[src]=str(dst.resolve())
            r[key]=cache[src]
    with open(a.output,"w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    print("converted unique audio files",len(cache),"rows",len(rows))
if __name__=="__main__":main()
