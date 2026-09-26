#!/usr/bin/env python3
"""Prepare deterministic full-reference TMHINT-QI v2 test pairs."""
import argparse,csv,json
from collections import defaultdict
from pathlib import Path

CLEAN={"","none","clean","null","na","n/a"}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("root");ap.add_argument("output")
    args=ap.parse_args()
    root=Path(args.root)
    csvs=list(root.rglob("raw_data.csv"))
    if len(csvs)!=1: raise SystemExit(f"expected one raw_data.csv, found {csvs}")
    raw=csvs[0]
    wavs=[]
    for td in [p for p in root.rglob("test") if p.is_dir()]:
        wavs.extend(td.rglob("*.wav"))
    by_stem={p.stem:p.resolve() for p in wavs}
    ratings=defaultdict(list);meta={}
    with raw.open(newline="",encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            stem=(r.get("file_name") or "").strip()
            q=(r.get("quality_score") or "").strip()
            if stem and q and stem in by_stem:
                ratings[stem].append(float(q));meta[stem]=r

    clean_candidates=defaultdict(list)
    for stem,r in meta.items():
        method=(r.get("method") or "").strip().lower()
        uttr=(r.get("uttr") or "").strip()
        if method in CLEAN and uttr:
            clean_candidates[uttr].append(stem)
    clean_by_uttr={u:by_stem[s[0]] for u,s in clean_candidates.items() if len(s)==1}

    out=[];unresolved=[]
    for stem,scores in sorted(ratings.items()):
        r=meta[stem];method=(r.get("method") or "").strip()
        if method.lower() in CLEAN: continue
        uttr=(r.get("uttr") or "").strip()
        ref=clean_by_uttr.get(uttr)
        if ref is None:
            unresolved.append(stem);continue
        mean_q=sum(scores)/len(scores)
        out.append({
          "reference":str(ref),
          "degraded":str(by_stem[stem]),
          "human_mos":1.0+0.8*mean_q,
          "group_id":uttr,
          "condition_id":method,
          "family":"TMHINT_QI_V2_TEST",
          "filename":by_stem[stem].name,
          "raw_quality_mean":mean_q,
          "listener_count":len(scores),
        })
    print(json.dumps({"test_wavs":len(wavs),"paired":len(out),
                      "unresolved":len(unresolved),"unique_sources":len(set(x["group_id"] for x in out))},
                     indent=2))
    if len(out)<1000: raise SystemExit(f"too few deterministic pairs: {len(out)}")
    fields=list(out[0])
    with open(args.output,"w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(out)
if __name__=="__main__":main()
