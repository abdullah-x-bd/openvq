#!/usr/bin/env python3
"""Explicit Phase 6 adapter for the pinned original TMHINT-QI archive."""
import argparse,csv,hashlib,json
from collections import defaultdict
from pathlib import Path

EXPECTED_ARCHIVE="cda6581c9fb0ea634b8bac4c6503e772feb080629a5d95eb84f3d1888876912b"
CLEAN={"","none","clean","null","na","n/a"}

def sha(p):
    h=hashlib.sha256()
    with open(p,"rb") as f:
        for b in iter(lambda:f.read(1<<20),b""):h.update(b)
    return h.hexdigest()
def main():
    ap=argparse.ArgumentParser();ap.add_argument("root");ap.add_argument("output")
    ap.add_argument("--archive",required=True);ap.add_argument("--exclusions",required=True)
    a=ap.parse_args();root=Path(a.root);archive=Path(a.archive)
    got=sha(archive)
    if got!=EXPECTED_ARCHIVE:raise SystemExit(f"TMHINT archive hash mismatch {got}")
    raw=list(root.rglob("raw_data.csv"))
    if len(raw)!=1:raise SystemExit(f"expected one raw_data.csv, found {raw}")
    wavs=[];[wavs.extend(p.rglob("*.wav")) for p in root.rglob("test") if p.is_dir()]
    by={p.stem:p.resolve() for p in wavs};ratings=defaultdict(list);meta={}
    with raw[0].open(newline="",encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            stem=(r.get("file_name") or "").strip();q=(r.get("quality_score") or "").strip()
            if stem and q and stem in by:ratings[stem].append(float(q));meta[stem]=r
    methods={((r.get("method") or "").strip().lower()) for r in meta.values()}
    if not ({"ddae","klt"} & methods):raise SystemExit("archive does not match original TMHINT processing families")
    clean=defaultdict(list)
    for stem,r in meta.items():
        u=(r.get("uttr") or "").strip();m=(r.get("method") or "").strip().lower()
        if u and m in CLEAN:clean[u].append(stem)
    refs={u:by[v[0]] for u,v in clean.items() if len(v)==1}
    out=[];exc=[]
    for stem,scores in sorted(ratings.items()):
        r=meta[stem];m=(r.get("method") or "").strip()
        if m.lower() in CLEAN:continue
        u=(r.get("uttr") or "").strip();rp=refs.get(u)
        if rp is None:exc.append({"filename":stem,"reason":"no_unique_clean_reference","utterance_id":u});continue
        mean=sum(scores)/len(scores)
        if not (1.0<=mean<=5.0):raise SystemExit(f"unexpected original TMHINT rating {mean}")
        out.append({"reference":str(rp),"degraded":str(by[stem]),"human_mos":mean,
                    "group_id":u,"condition_id":m,"family":"TMHINT_QI_ORIGINAL_TEST",
                    "filename":by[stem].name,"listener_count":len(scores)})
    with open(a.output,"w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=list(out[0]));w.writeheader();w.writerows(out)
    with open(a.exclusions,"w",newline="",encoding="utf-8") as f:
        fields=["filename","reason","utterance_id"];w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(exc)
    print(json.dumps({"release":"TMHINT_QI_ORIGINAL","scale":"MOS_1_5","archive_sha256":got,
                      "paired":len(out),"excluded":len(exc),"unique_refs":len(refs)},indent=2))
if __name__=="__main__":main()
