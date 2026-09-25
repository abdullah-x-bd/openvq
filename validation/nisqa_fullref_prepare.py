#!/usr/bin/env python3
"""Prepare one 240-file NISQA full-reference test set without fitting."""
from __future__ import annotations
import argparse,csv,json
from pathlib import Path

def choose(fields,candidates,required=True):
    lower={str(x).lower():x for x in fields}
    for c in candidates:
        if c.lower() in lower:return lower[c.lower()]
    if required:raise SystemExit(f"missing expected column from {candidates}; have {fields}")
    return None

def resolve(root,value,by_name,kind):
    if not value:return None
    raw=str(value).replace("\\","/")
    p=Path(raw)
    for c in (root/p,root/p.name,root/kind/p.name):
        if c.exists():return c.resolve()
    hit=by_name.get(p.name)
    return hit.resolve() if hit else None

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("root");ap.add_argument("output")
    ap.add_argument("--family",required=True)
    ap.add_argument("--expected",type=int,default=240)
    a=ap.parse_args()
    root=Path(a.root)
    files=list(root.rglob("*"))
    csvs=[p for p in files if p.is_file() and p.name.endswith("_file.csv")]
    if len(csvs)!=1:
        raise SystemExit(f"expected one *_file.csv beneath {root}, found {len(csvs)}: {[str(x) for x in csvs[:8]]}")
    source=csvs[0]
    wavs=[p for p in files if p.suffix.lower()==".wav"]
    by_name={}
    duplicates=set()
    for p in wavs:
        if p.name in by_name:duplicates.add(p.name)
        else:by_name[p.name]=p
    for name in duplicates:by_name.pop(name,None)

    with source.open(newline="",encoding="utf-8-sig") as f:
        rd=csv.DictReader(f);fields=rd.fieldnames or []
        mos_col=choose(fields,["mos","sample MOS","score"])
        deg_col=choose(fields,["filepath_deg","deg","degraded","file","filename"])
        ref_col=choose(fields,["filepath_ref","ref","reference","ref_file"])
        con_col=choose(fields,["con","condition","condition_id","ConditionID"],required=False)
        rows=[];missing=[]
        for idx,row in enumerate(rd,1):
            d=resolve(root,row.get(deg_col,""),by_name,"deg")
            r=resolve(root,row.get(ref_col,""),by_name,"ref")
            if d is None or r is None:
                missing.append({"row":idx,"deg":row.get(deg_col,""),"ref":row.get(ref_col,"")})
                continue
            rows.append({
              "reference":str(r),"degraded":str(d),"human_mos":float(row[mos_col]),
              "condition_id":row.get(con_col,"") if con_col else "",
              "family":a.family,"filename":d.name,
            })
    if missing:raise SystemExit(f"unresolved pairs: {json.dumps(missing[:8])}")
    if len(rows)!=a.expected:raise SystemExit(f"expected {a.expected} rows, got {len(rows)}")
    out=Path(a.output);out.parent.mkdir(parents=True,exist_ok=True)
    keys=["reference","degraded","human_mos","condition_id","family","filename"]
    with out.open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=keys);w.writeheader();w.writerows(rows)
    print(json.dumps({
      "family":a.family,"rows":len(rows),
      "conditions":len(set(r["condition_id"] for r in rows)),
      "mos_min":min(r["human_mos"] for r in rows),
      "mos_max":max(r["human_mos"] for r in rows),
      "mos_mean":sum(r["human_mos"] for r in rows)/len(rows)
    },indent=2))

if __name__=="__main__":main()
