#!/usr/bin/env python3
"""Extract Phase 6.3 rich-v4 features from canonical or property manifests."""
import argparse,csv,json,os,subprocess
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from phase63_feature_schema import RICH_V4,FRONTEND_ID,SCHEMA_ID,from_result

def target(r,field,scale):
    raw=float(r[field])
    if scale=="normalized":return raw,raw
    if scale=="mos1to5":return (raw-1.0)/4.0,raw
    if scale=="mushra100":return raw/100.0,raw
    raise ValueError(scale)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("manifest");ap.add_argument("output")
    ap.add_argument("--dataset-field",default="dataset");ap.add_argument("--dataset",default="")
    ap.add_argument("--target-field",required=True)
    ap.add_argument("--target-scale",choices=["normalized","mos1to5","mushra100"],required=True)
    ap.add_argument("--cli",default="./build/openvq_cli")
    ap.add_argument("--jobs",type=int,default=max(1,min(4,os.cpu_count() or 1)))
    a=ap.parse_args()
    rows=list(csv.DictReader(open(a.manifest,newline="",encoding="utf-8")))
    if not rows:raise SystemExit("empty manifest")
    def one(r):
        obj=json.loads(subprocess.check_output([a.cli,r["reference"],r["degraded"]],text=True))
        got=obj.get("frontend_id")
        if got and got!=FRONTEND_ID:raise RuntimeError(f"frontend mismatch {got} != {FRONTEND_ID}")
        norm,raw=target(r,a.target_field,a.target_scale)
        feats=from_result(obj);dataset=(r.get(a.dataset_field) or a.dataset).strip()
        if not dataset:raise RuntimeError("dataset missing")
        out=dict(r);out.update({"dataset":dataset,"target_normalized":norm,"human_raw":raw,
          "target_scale":a.target_scale,"frontend_id":FRONTEND_ID,"feature_schema_id":SCHEMA_ID})
        out.update({k:feats[k] for k in RICH_V4});return out
    out=[]
    with ThreadPoolExecutor(max_workers=a.jobs) as pool:
        for i,x in enumerate(pool.map(one,rows),1):
            out.append(x)
            if i%50==0 or i==len(rows):print("phase63 features",i,"/",len(rows),flush=True)
    Path(a.output).parent.mkdir(parents=True,exist_ok=True)
    fields=[]
    for r in out:
        for k in r:
            if k not in fields:fields.append(k)
    with open(a.output,"w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(out)
if __name__=="__main__":main()
