#!/usr/bin/env python3
"""Prepare a NISQA family for Phase 6 only when exact full-reference pairs exist."""
import argparse,csv,json
from pathlib import Path

def choose(fields,cands,required=True):
    low={str(x).lower():x for x in fields}
    for c in cands:
        if c.lower() in low:return low[c.lower()]
    if required:raise SystemExit(f"missing column {cands}; have {fields}")
    return None
def resolve(root,val,by_name,kind):
    if not val:return None,"empty"
    p=Path(str(val).replace("\\","/"))
    hits=[]
    for q in (root/p,root/p.name,root/kind/p.name):
        if q.is_file():hits.append(q.resolve())
    if p.name in by_name:hits.extend(by_name[p.name])
    hits=list(dict.fromkeys(hits))
    if len(hits)==1:return hits[0],""
    if not hits:return None,"not_found"
    return None,"ambiguous"

def main():
    ap=argparse.ArgumentParser();ap.add_argument("root");ap.add_argument("output")
    ap.add_argument("--family",required=True);ap.add_argument("--exclusions",required=True)
    ap.add_argument("--min-paired",type=int,default=1)
    a=ap.parse_args();root=Path(a.root)
    csvs=[p for p in root.rglob("*_file.csv") if a.family.lower() in str(p).lower()]
    if len(csvs)!=1:raise SystemExit(f"expected one {a.family} *_file.csv, found {csvs}")
    source=csvs[0];wavs=[p for p in root.rglob("*.wav")];by={}
    for p in wavs:by.setdefault(p.name,[]).append(p)
    out=[];excluded=[]
    with source.open(newline="",encoding="utf-8-sig") as f:
        rd=csv.DictReader(f);fields=rd.fieldnames or []
        mos=choose(fields,["mos","MOS","sample MOS"])
        deg=choose(fields,["filepath_deg","deg","degraded","file","filename"])
        ref=choose(fields,["filepath_ref","ref","reference","ref_file"],False)
        con=choose(fields,["con","condition","condition_id","ConditionID"],False)
        src=choose(fields,["source","source_id","speaker"],False)
        if ref is None:
            raise SystemExit(f"{a.family} metadata has no explicit reference column; refuse full-reference use")
        for i,r in enumerate(rd,1):
            dp,dr=resolve(root,r.get(deg,""),by,"deg");rp,rr=resolve(root,r.get(ref,""),by,"ref")
            if dp is None or rp is None:
                excluded.append({"row":i,"reason":"degraded_"+dr if dp is None else "reference_"+rr,
                                 "degraded":r.get(deg,""),"reference":r.get(ref,"")});continue
            out.append({"reference":str(rp),"degraded":str(dp),"human_mos":float(r[mos]),
                        "condition_id":r.get(con,"") if con else "","family":a.family,
                        "source_id":r.get(src,"") if src else "","filename":dp.name})
    Path(a.exclusions).parent.mkdir(parents=True,exist_ok=True)
    with open(a.exclusions,"w",newline="",encoding="utf-8") as f:
        fields=["row","reason","degraded","reference"];w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(excluded)
    if len(out)<a.min_paired:
        raise SystemExit(f"{a.family}: only {len(out)} exact pairs; not eligible for Phase 6 full-reference training")
    with open(a.output,"w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=list(out[0]));w.writeheader();w.writerows(out)
    print(json.dumps({"family":a.family,"paired":len(out),"excluded":len(excluded),
                      "unique_references":len(set(r["reference"] for r in out))},indent=2))
if __name__=="__main__":main()
