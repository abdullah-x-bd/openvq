#!/usr/bin/env python3
"""Select disjoint primary and qualification clean references from local development audio."""
import argparse,csv,hashlib,json
from collections import defaultdict
from pathlib import Path
CLEAN={"","none","clean","null","na","n/a"}
def sha256(path):
    h=hashlib.sha256()
    with open(path,"rb") as f:
        for b in iter(lambda:f.read(1<<20),b""):h.update(b)
    return h.hexdigest()
def choose_disjoint(items):
    items=sorted(items,key=lambda x:str(x));n=len(items)
    if n<7:raise RuntimeError(f"need >=7 candidates, found {n}")
    pidx=[0,round((n-1)/2),n-1];primary=[items[i] for i in pidx];used=set(pidx);secondary=[]
    for frac in (0.20,0.38,0.72,0.82,0.28,0.62):
        i=round((n-1)*frac);picked=False
        for delta in range(n):
            for j in (i-delta,i+delta):
                if 0<=j<n and j not in used:
                    used.add(j);secondary.append(items[j]);picked=True;break
            if picked:break
        if len(secondary)==3:break
    if len(secondary)!=3:raise RuntimeError("could not choose secondary references")
    return primary,secondary
def tcd_candidates(root):return sorted(p.resolve() for p in Path(root).rglob("R_*.wav"))
def tmhint_candidates(root):
    root=Path(root);csvs=[p for p in root.rglob("raw_data.csv")]
    if len(csvs)!=1:raise RuntimeError(f"expected one raw_data.csv, found {csvs}")
    meta={}
    with csvs[0].open(newline="",encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            stem=(r.get("file_name") or "").strip()
            if stem:meta[stem]=r
    by=defaultdict(list)
    for p in root.rglob("*.wav"):
        if "test" in {x.lower() for x in p.parts}:by[p.stem].append(p.resolve())
    per=defaultdict(list)
    for stem,r in meta.items():
        method=(r.get("method") or "").strip().lower();utt=(r.get("uttr") or "").strip()
        if utt and method in CLEAN and len(by.get(stem,[]))==1:per[utt].append(by[stem][0])
    return sorted((utt,pp[0]) for utt,pp in per.items() if len(pp)==1)
def write(rows,path):
    fields=["reference_id","property_corpus","source_corpus","language","reference","reference_sha256","source_utterance_id","selection_role"]
    with open(path,"w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)
def main():
    ap=argparse.ArgumentParser();ap.add_argument("--tcd-root",required=True);ap.add_argument("--tmhint-root",required=True)
    ap.add_argument("--primary",required=True);ap.add_argument("--secondary",required=True);ap.add_argument("--out",required=True);a=ap.parse_args()
    tp,ts=choose_disjoint(tcd_candidates(a.tcd_root));mp,ms=choose_disjoint(tmhint_candidates(a.tmhint_root))
    def rows(items,corpus,source,lang,role):
        out=[]
        for i,item in enumerate(items,1):
            utt="" if corpus=="tcd" else item[0];p=item if corpus=="tcd" else item[1]
            out.append({"reference_id":f"phase63-{role}-{corpus}-{i:02d}","property_corpus":corpus,
              "source_corpus":source,"language":lang,"reference":str(p),"reference_sha256":sha256(p),
              "source_utterance_id":utt,"selection_role":role})
        return out
    primary=rows(tp,"tcd","TCD-VoIP","English","primary")+rows(mp,"tmhint","TMHINT-QI-original","Mandarin","primary")
    secondary=rows(ts,"tcd","TCD-VoIP","English","secondary")+rows(ms,"tmhint","TMHINT-QI-original","Mandarin","secondary")
    if {r["reference_sha256"] for r in primary}&{r["reference_sha256"] for r in secondary}:raise SystemExit("reference overlap")
    Path(a.primary).parent.mkdir(parents=True,exist_ok=True);write(primary,a.primary);write(secondary,a.secondary)
    result={"phase":"6.3B-R1","primary":len(primary),"secondary":len(secondary),"primary_secondary_disjoint":True,
      "human_labels_read":False,"primary_sha256":sha256(a.primary),"secondary_sha256":sha256(a.secondary)}
    Path(a.out).write_text(json.dumps(result,indent=2)+"\n");print(json.dumps(result,indent=2))
if __name__=="__main__":main()
