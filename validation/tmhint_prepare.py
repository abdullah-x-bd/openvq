#!/usr/bin/env python3
"""Prepare deterministic full-reference TMHINT-QI test pairs with release detection.

Phase 5.1A preserves the historical Phase 5 manifest but corrects the evidence
for all new runs. The downloaded archive is classified from its processing
families and observed listener-score range before a target scale is chosen.
"""
import argparse,csv,hashlib,json
from collections import defaultdict,Counter
from pathlib import Path

CLEAN={"","none","clean","null","na","n/a"}
ORIGINAL_MARKERS={"ddae","klt"}
V2_MARKERS={"cmgan","demucs"}

def sha256(path):
    h=hashlib.sha256()
    with open(path,"rb") as f:
        for chunk in iter(lambda:f.read(1024*1024),b""):
            h.update(chunk)
    return h.hexdigest()

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("root");ap.add_argument("output")
    ap.add_argument("--archive",default=None,
                    help="optional source archive path for provenance hashing")
    ap.add_argument("--provenance-out",default=None)
    args=ap.parse_args()
    root=Path(args.root)
    csvs=list(root.rglob("raw_data.csv"))
    if len(csvs)!=1:
        raise SystemExit(f"expected one raw_data.csv, found {csvs}")
    raw=csvs[0]

    wavs=[]
    test_dirs=[p for p in root.rglob("test") if p.is_dir()]
    for td in test_dirs:
        wavs.extend(td.rglob("*.wav"))
    by_stem={p.stem:p.resolve() for p in wavs}

    ratings=defaultdict(list);meta={}
    all_methods=Counter();all_scores=[]
    with raw.open(newline="",encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            method=(r.get("method") or "").strip()
            if method:
                all_methods[method]+=1
            stem=(r.get("file_name") or "").strip()
            q=(r.get("quality_score") or "").strip()
            if stem and q and stem in by_stem:
                score=float(q)
                ratings[stem].append(score);meta[stem]=r;all_scores.append(score)

    methods_lower={m.lower() for m in all_methods}
    if methods_lower & ORIGINAL_MARKERS:
        release="TMHINT_QI_ORIGINAL"
        score_scale="1_to_5"
    elif methods_lower & V2_MARKERS:
        release="TMHINT_QI_V2"
        # VoiceMOS version-II metadata is documented as 0..5. Detect rather than
        # inventing a rescale when the observed values already occupy 1..5.
        score_scale="0_to_5" if all_scores and min(all_scores)<1.0 else "1_to_5"
    else:
        raise SystemExit(
            "cannot classify TMHINT release from processing families: "
            + ",".join(sorted(all_methods))
        )

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
        if method.lower() in CLEAN:
            continue
        uttr=(r.get("uttr") or "").strip()
        ref=clean_by_uttr.get(uttr)
        if ref is None:
            unresolved.append(stem);continue
        mean_q=sum(scores)/len(scores)
        human_mos=mean_q if score_scale=="1_to_5" else 1.0+0.8*mean_q
        out.append({
          "reference":str(ref),
          "degraded":str(by_stem[stem]),
          "human_mos":human_mos,
          "group_id":uttr,
          "condition_id":method,
          "family":release+"_TEST",
          "filename":by_stem[stem].name,
          "raw_quality_mean":mean_q,
          "listener_count":len(scores),
        })

    if len(out)<1000:
        raise SystemExit(f"too few deterministic pairs: {len(out)}")
    fields=list(out[0])
    with open(args.output,"w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(out)

    provenance={
      "release_detected":release,
      "score_scale_detected":score_scale,
      "score_min":min(all_scores) if all_scores else None,
      "score_max":max(all_scores) if all_scores else None,
      "methods":dict(sorted(all_methods.items())),
      "test_wavs":len(wavs),
      "paired_nonclean":len(out),
      "unresolved_nonclean":len(unresolved),
      "unique_reference_ids":len(set(x["group_id"] for x in out)),
      "raw_data_csv":str(raw),
      "raw_data_sha256":sha256(raw),
      "manifest_sha256":sha256(args.output),
    }
    if args.archive:
        provenance["archive"]=str(args.archive)
        provenance["archive_sha256"]=sha256(args.archive)
    print(json.dumps(provenance,indent=2))
    if args.provenance_out:
        Path(args.provenance_out).write_text(json.dumps(provenance,indent=2)+"\n",
                                             encoding="utf-8")

if __name__=="__main__":
    main()
