#!/usr/bin/env python3
"""Frozen Phase 6 external report with source-cluster bootstrap."""
import argparse,csv,json,math
from collections import defaultdict
from pathlib import Path
import numpy as np

def ranks(v):
    v=np.asarray(v,float);o=np.argsort(v,kind="mergesort");r=np.empty(len(v));i=0
    while i<len(o):
        j=i+1
        while j<len(o) and v[o[j]]==v[o[i]]:j+=1
        r[o[i:j]]=(i+j-1)/2+1;i=j
    return r
def corr(a,b):
    a=np.asarray(a,float);b=np.asarray(b,float)
    if len(a)<2 or np.std(a)<1e-12 or np.std(b)<1e-12:return 0.0
    return float(np.corrcoef(a,b)[0,1])
def metrics(rows,pcol="openvq_mos"):
    y=np.asarray([float(r["human_mos"]) for r in rows]);p=np.asarray([float(r[pcol]) for r in rows]);e=p-y
    return {"n":len(rows),"pearson":corr(y,p),"spearman":corr(ranks(y),ranks(p)),
      "rmse":float(np.sqrt(np.mean(e*e))),"mae":float(np.mean(np.abs(e))),"bias":float(np.mean(e)),
      "near_floor_fraction":float(np.mean(p<=1.2)),"near_ceiling_fraction":float(np.mean(p>=4.8))}
def main():
    ap=argparse.ArgumentParser();ap.add_argument("scored");ap.add_argument("--out",required=True)
    ap.add_argument("--bootstrap",type=int,default=10000);ap.add_argument("--seed",type=int,default=20260926)
    a=ap.parse_args();rows=list(csv.DictReader(open(a.scored,newline="",encoding="utf-8")))
    overall=metrics(rows);by_system={};by_language={}
    for k,grp in (("system_id",by_system),("language",by_language)):
        vals=defaultdict(list)
        for r in rows:vals[r.get(k,"")].append(r)
        for q,v in vals.items():
            if len(v)>=4:grp[q]=metrics(v)
    groups=defaultdict(list)
    for r in rows:groups[r["group_id"]].append(r)
    keys=sorted(groups);rng=np.random.default_rng(a.seed);boot=[]
    for _ in range(a.bootstrap):
        kk=rng.choice(keys,len(keys),replace=True);sample=[r for k in kk for r in groups[k]]
        m=metrics(sample);boot.append([m["pearson"],m["spearman"],m["rmse"]])
    b=np.asarray(boot)
    ci={"pearson_95":[float(x) for x in np.quantile(b[:,0],[.025,.975])],
        "spearman_95":[float(x) for x in np.quantile(b[:,1],[.025,.975])],
        "rmse_95":[float(x) for x in np.quantile(b[:,2],[.025,.975])]}
    result={"dataset":"URGENT2026_ACR_SIMULATED_VERIFIED_FULL_REFERENCE",
      "overall":overall,"cluster_unit":"utterance_id/reference source","bootstrap_resamples":a.bootstrap,
      "confidence_intervals":ci,"by_system":by_system,"by_language":by_language,
      "research_screen":{"pearson_min":.70,"spearman_min":.70,"rmse_max":.80,
        "passes":overall["pearson"]>=.70 and overall["spearman"]>=.70 and overall["rmse"]<=.80},
      "claim_boundary":"Passing this project screen is external generalization evidence, not P.863 conformance or POLQA superiority."}
    Path(a.out).write_text(json.dumps(result,indent=2)+"\n");print(json.dumps(result,indent=2))
if __name__=="__main__":main()
