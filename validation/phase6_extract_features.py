#!/usr/bin/env python3
"""Extract Phase 6 features from a canonical full-reference manifest."""
import argparse,csv,json,os,subprocess
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from phase6_feature_schema import RICH_V3,FRONTEND_ID,SCHEMA_ID,from_result

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("manifest");ap.add_argument("output")
    ap.add_argument("--dataset",required=True)
    ap.add_argument("--target-field",required=True)
    ap.add_argument("--target-scale",choices=["mos1to5","mushra100"],required=True)
    ap.add_argument("--group-field",required=True)
    ap.add_argument("--system-field",default="condition_id")
    ap.add_argument("--speaker-field",default="")
    ap.add_argument("--cli",default="./build/openvq_cli")
    ap.add_argument("--jobs",type=int,default=max(1,min(4,os.cpu_count() or 1)))
    a=ap.parse_args()
    rows=list(csv.DictReader(open(a.manifest,newline="",encoding="utf-8")))
    def one(r):
        obj=json.loads(subprocess.check_output([a.cli,r["reference"],r["degraded"]],text=True))
        got=obj.get("frontend_id")
        if got and got!=FRONTEND_ID:
            raise RuntimeError(f"frontend mismatch: {got} != {FRONTEND_ID}")
        raw=float(r[a.target_field])
        target=(raw-1.0)/4.0 if a.target_scale=="mos1to5" else raw/100.0
        feats=from_result(obj)
        group=(r.get(a.group_field) or "").strip() or r.get("filename","")
        system=(r.get(a.system_field) or "").strip() or r.get("family","")
        speaker=(r.get(a.speaker_field) or "").strip() if a.speaker_field else ""
        return {
            "dataset":a.dataset,"group_id":group,"system_id":system,
            "speaker_id":speaker,"family":r.get("family",""),
            "condition_id":r.get("condition_id",""),
            "filename":r.get("filename",r.get("distorted_file","")),
            "reference":r["reference"],"degraded":r["degraded"],
            "target_normalized":target,"human_raw":raw,
            "target_scale":a.target_scale,"frontend_id":FRONTEND_ID,
            "feature_schema_id":SCHEMA_ID,
            **{k:feats[k] for k in RICH_V3},
        }
    out=[]
    with ThreadPoolExecutor(max_workers=a.jobs) as pool:
        for i,x in enumerate(pool.map(one,rows),1):
            out.append(x)
            if i%40==0 or i==len(rows):
                print(a.dataset,"features",i,"/",len(rows),flush=True)
    Path(a.output).parent.mkdir(parents=True,exist_ok=True)
    with open(a.output,"w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=list(out[0]));w.writeheader();w.writerows(out)
if __name__=="__main__":main()
