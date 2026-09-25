#!/usr/bin/env python3
"""Score a locked manifest with native Phase 4 only."""
import argparse,csv,json,os,subprocess
from concurrent.futures import ThreadPoolExecutor

MODEL_ID="phase4-native-poly2-balanced-2026-09-25-v1"

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("manifest");ap.add_argument("output")
    ap.add_argument("--cli",default="./build/openvq_cli")
    ap.add_argument("--jobs",type=int,default=max(1,min(4,os.cpu_count() or 1)))
    a=ap.parse_args()
    rows=list(csv.DictReader(open(a.manifest,newline="",encoding="utf-8")))
    def one(r):
        obj=json.loads(subprocess.check_output(
          [a.cli,r["reference"],r["degraded"],"--phase4"],text=True))
        if not obj.get("phase4_applied"):raise RuntimeError("Phase 4 was not applied")
        if obj.get("phase4_model")!=MODEL_ID:
            raise RuntimeError(f"unexpected model {obj.get('phase4_model')!r}")
        if obj.get("phase4_experts_applied"):
            raise RuntimeError("primary holdout must not apply external experts")
        out=dict(r);out["openvq_mos"]=obj["mos"];out["model_id"]=obj["phase4_model"]
        return out
    scored=[]
    with ThreadPoolExecutor(max_workers=a.jobs) as p:
        for i,r in enumerate(p.map(one,rows),1):
            scored.append(r)
            if i%40==0 or i==len(rows):print(f"Phase 4 scored {i} / {len(rows)}",flush=True)
    with open(a.output,"w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=list(scored[0]));w.writeheader();w.writerows(scored)

if __name__=="__main__":main()
