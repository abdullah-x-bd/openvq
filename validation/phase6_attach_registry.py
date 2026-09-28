#!/usr/bin/env python3
"""Attach canonical source identity to Phase 6 feature rows."""
import argparse,csv
def main():
    ap=argparse.ArgumentParser();ap.add_argument("registry");ap.add_argument("features");ap.add_argument("output");a=ap.parse_args()
    reg=list(csv.DictReader(open(a.registry,newline="",encoding="utf-8")))
    m={(r["dataset"],r["filename"]):r for r in reg}
    rows=list(csv.DictReader(open(a.features,newline="",encoding="utf-8")));out=[]
    for r in rows:
        q=m.get((r["dataset"],r["filename"]))
        if q is None:raise SystemExit(f"registry miss {r['dataset']} {r['filename']}")
        x=dict(r);x["legacy_group_id"]=r.get("group_id","");x["canonical_source_id"]=q["canonical_source_id"]
        x["group_id"]=q["canonical_source_id"];x["ancestry"]=q["ancestry"]
        if not x.get("speaker_id"):x["speaker_id"]=q.get("speaker_id","")
        out.append(x)
    with open(a.output,"w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=list(out[0]));w.writeheader();w.writerows(out)
    print("attached canonical sources",len(out))
if __name__=="__main__":main()
