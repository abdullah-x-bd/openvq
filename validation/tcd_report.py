#!/usr/bin/env python3
"""Compute transparent MOS validation metrics from OpenVQ predictions."""
import argparse
import csv
import json
import math
from collections import defaultdict

def pearson(a,b):
    if len(a)<2:return 0.0
    ma=sum(a)/len(a); mb=sum(b)/len(b)
    num=sum((x-ma)*(y-mb) for x,y in zip(a,b))
    den=math.sqrt(sum((x-ma)**2 for x in a)*sum((y-mb)**2 for y in b))
    return num/den if den else 0.0

def ranks(v):
    order=sorted(range(len(v)),key=lambda i:v[i])
    r=[0.0]*len(v); i=0
    while i<len(order):
        j=i+1
        while j<len(order) and v[order[j]]==v[order[i]]: j+=1
        avg=(i+j-1)/2+1
        for k in range(i,j):r[order[k]]=avg
        i=j
    return r

def metrics(rows):
    y=[r["human_mos"] for r in rows]
    p=[r["openvq_mos"] for r in rows]
    e=[a-b for a,b in zip(p,y)]
    return {
        "n":len(rows),
        "pearson":pearson(p,y),
        "spearman":pearson(ranks(p),ranks(y)),
        "rmse":math.sqrt(sum(x*x for x in e)/len(e)),
        "mae":sum(abs(x) for x in e)/len(e),
        "bias":sum(e)/len(e),
        "human_mean":sum(y)/len(y),
        "prediction_mean":sum(p)/len(p),
    }

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("predictions")
    ap.add_argument("--out",required=True)
    args=ap.parse_args()
    rows=[]
    with open(args.predictions,newline="",encoding="utf-8") as f:
        for r in csv.DictReader(f):
            r["human_mos"]=float(r["human_mos"])
            r["openvq_mos"]=float(r["openvq_mos"])
            r["condition_id"]=int(r["condition_id"])
            rows.append(r)

    by_condition=defaultdict(list)
    for r in rows:
        by_condition[(r["family"],r["condition_id"])].append(r)
    condition_rows=[]
    for (fam,cid),rr in by_condition.items():
        condition_rows.append({
            "family":fam,
            "condition_id":cid,
            "human_mos":sum(x["human_mos"] for x in rr)/len(rr),
            "openvq_mos":sum(x["openvq_mos"] for x in rr)/len(rr),
        })

    by_family={}
    for fam in sorted(set(r["family"] for r in rows)):
        by_family[fam]={
            "utterance":metrics([r for r in rows if r["family"]==fam]),
            "condition":metrics([r for r in condition_rows if r["family"]==fam]),
        }

    residuals=sorted(
        [{
            "filename":r["filename"],
            "family":r["family"],
            "condition_id":r["condition_id"],
            "human_mos":r["human_mos"],
            "openvq_mos":r["openvq_mos"],
            "error":r["openvq_mos"]-r["human_mos"],
        } for r in rows],
        key=lambda x:abs(x["error"]),
        reverse=True
    )

    result={
        "utterance":metrics(rows),
        "condition":metrics(condition_rows),
        "by_family":by_family,
        "worst_20_residuals":residuals[:20],
    }
    with open(args.out,"w",encoding="utf-8") as f: json.dump(result,f,indent=2)
    print(json.dumps(result,indent=2))

if __name__=="__main__":
    main()
