#!/usr/bin/env python3
"""Prepare NISQA_TEST_P501 as a full-reference OpenVQ holdout manifest.

The script deliberately performs no training and does not modify labels.
It accepts the original NISQA per-file CSV and resolves reference/degraded
paths within the extracted P501 subset.
"""
from __future__ import annotations
import argparse, csv, json
from pathlib import Path

def choose(fieldnames, candidates, required=True):
    lower={str(x).lower():x for x in fieldnames}
    for c in candidates:
        if c.lower() in lower:
            return lower[c.lower()]
    if required:
        raise SystemExit(f"missing expected column from {candidates}; have {fieldnames}")
    return None

def resolve(root:Path, value:str, by_name:dict[str,Path], kind:str):
    if not value:
        return None
    raw=str(value).replace("\\","/")
    p=Path(raw)
    candidates=[
        root/p,
        root/p.name,
        root/kind/p.name,
    ]
    for c in candidates:
        if c.exists():
            return c.resolve()
    hit=by_name.get(p.name)
    return hit.resolve() if hit else None

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("root")
    ap.add_argument("output")
    args=ap.parse_args()
    root=Path(args.root)
    files=list(root.rglob("*"))
    file_csvs=[p for p in files if p.is_file() and p.name.endswith("_file.csv")]
    if not file_csvs:
        raise SystemExit(f"no *_file.csv beneath {root}")
    source=file_csvs[0]

    wavs=[p for p in files if p.suffix.lower()==".wav"]
    by_name={p.name:p for p in wavs}

    with source.open(newline="",encoding="utf-8-sig") as f:
        rd=csv.DictReader(f)
        fields=rd.fieldnames or []
        mos_col=choose(fields,["mos","MOS","sample MOS","score"])
        deg_col=choose(fields,["filepath_deg","deg","degraded","file","filename"])
        ref_col=choose(fields,["filepath_ref","ref","reference","ref_file"])
        con_col=choose(fields,["con","condition","condition_id","ConditionID"],required=False)
        db_col=choose(fields,["db","dataset"],required=False)

        rows=[]
        missing=[]
        for idx,row in enumerate(rd,1):
            d=resolve(root,row.get(deg_col,""),by_name,"deg")
            r=resolve(root,row.get(ref_col,""),by_name,"ref")
            if d is None or r is None:
                missing.append({
                    "row":idx,
                    "deg":row.get(deg_col,""),
                    "ref":row.get(ref_col,"")
                })
                continue
            rows.append({
                "reference":str(r),
                "degraded":str(d),
                "human_mos":float(row[mos_col]),
                "condition_id":row.get(con_col,"") if con_col else "",
                "family":row.get(db_col,"NISQA_TEST_P501") if db_col else "NISQA_TEST_P501",
                "filename":d.name,
            })

    if missing:
        raise SystemExit(f"unresolved pairs: {json.dumps(missing[:8])}")
    if len(rows) != 240:
        raise SystemExit(f"expected 240 P501 rows, got {len(rows)}")

    out=Path(args.output)
    out.parent.mkdir(parents=True,exist_ok=True)
    fields=["reference","degraded","human_mos","condition_id","family","filename"]
    with out.open("w",newline="",encoding="utf-8") as f:
        wr=csv.DictWriter(f,fieldnames=fields)
        wr.writeheader(); wr.writerows(rows)

    summary={
        "source_csv":str(source),
        "rows":len(rows),
        "unique_refs":len(set(r["reference"] for r in rows)),
        "unique_conditions":len(set(r["condition_id"] for r in rows)),
        "mos_min":min(r["human_mos"] for r in rows),
        "mos_max":max(r["human_mos"] for r in rows),
        "mos_mean":sum(r["human_mos"] for r in rows)/len(rows),
        "columns":{
            "mos":mos_col,"degraded":deg_col,"reference":ref_col,
            "condition":con_col,"dataset":db_col
        }
    }
    print(json.dumps(summary,indent=2))

if __name__=="__main__":
    main()
