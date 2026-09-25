#!/usr/bin/env python3
"""Prepare an untouched NISQA full-reference subset without altering labels."""
from __future__ import annotations
import argparse,csv,json
from pathlib import Path

def choose(fieldnames,candidates,required=True):
    lower={str(x).lower():x for x in fieldnames}
    for c in candidates:
        if c.lower() in lower:return lower[c.lower()]
    if required:raise SystemExit(f"missing expected column from {candidates}; have {fieldnames}")
    return None

def resolve(root:Path,value:str,by_name:dict[str,Path],kind:str):
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
    args=ap.parse_args()
    root=Path(args.root)
    files=list(root.rglob("*"))
    csvs=[p for p in files if p.is_file() and p.name.endswith("_file.csv")]
    if not csvs:raise SystemExit(f"no *_file.csv beneath {root}")
    source=csvs[0]
    wavs=[p for p in files if p.suffix.lower()==".wav"]
    by_name={p.name:p for p in wavs}
    rows=[];missing=[]
    with source.open(newline="",encoding="utf-8-sig") as f:
        rd=csv.DictReader(f);fields=rd.fieldnames or []
        mos_col=choose(fields,["mos","MOS","sample MOS","score"])
        deg_col=choose(fields,["filepath_deg","deg","degraded","file","filename"])
        ref_col=choose(fields,["filepath_ref","ref","reference","ref_file"])
        con_col=choose(fields,["con","condition","condition_id","ConditionID"],False)
        for idx,row in enumerate(rd,1):
            d=resolve(root,row.get(deg_col,""),by_name,"deg")
            r=resolve(root,row.get(ref_col,""),by_name,"ref")
            if d is None or r is None:
                missing.append({"row":idx,"deg":row.get(deg_col,""),"ref":row.get(ref_col,"")})
                continue
            rows.append({
              "reference":str(r),"degraded":str(d),
              "human_mos":float(row[mos_col]),
              "condition_id":row.get(con_col,"") if con_col else "",
              "family":args.family,"filename":d.name,
            })
    if missing:raise SystemExit(f"unresolved pairs: {json.dumps(missing[:8])}")
    if len(rows)!=args.expected:raise SystemExit(f"expected {args.expected} rows, got {len(rows)}")
    out=Path(args.output);out.parent.mkdir(parents=True,exist_ok=True)
    fields=["reference","degraded","human_mos","condition_id","family","filename"]
    with out.open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)
    print(json.dumps({
      "family":args.family,"rows":len(rows),
      "unique_refs":len(set(r["reference"] for r in rows)),
      "unique_conditions":len(set(r["condition_id"] for r in rows))
    },indent=2))

if __name__=="__main__":main()
