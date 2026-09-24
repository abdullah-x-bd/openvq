#!/usr/bin/env python3
"""Condition-group stratified cross-validation for TCD-VoIP.

TCD is treated as a development corpus after the initial diagnostic run. No
speaker clip from a condition may cross folds. Conditions are stratified by
family and condition-level human MOS to avoid severity-ordered condition IDs
creating an artificial train/test distribution shift.
"""
import argparse
import csv
import json
import math
from collections import defaultdict

from calibrate_joint import FEATURES, fit, predict_penalty

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
        av=(i+j-1)/2+1
        for k in range(i,j): r[order[k]]=av
        i=j
    return r

def metrics(rows):
    y=[r["human_mos"] for r in rows]
    p=[r["prediction"] for r in rows]
    e=[pp-yy for pp,yy in zip(p,y)]
    return {
        "n":len(rows),
        "pearson":pearson(p,y),
        "spearman":pearson(ranks(p),ranks(y)),
        "rmse":math.sqrt(sum(x*x for x in e)/len(e)),
        "mae":sum(abs(x) for x in e)/len(e),
        "bias":sum(e)/len(e),
    }

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("features_csv")
    ap.add_argument("--folds",type=int,default=5)
    ap.add_argument("--out",required=True)
    args=ap.parse_args()

    raw=[]
    with open(args.features_csv,newline="",encoding="utf-8") as f:
        for r in csv.DictReader(f):
            x=[max(0.0,min(1.0,float(r[name]))) for name,_ in FEATURES]
            raw.append({
                "x":x,
                "human_mos":float(r["human_mos"]),
                "condition_id":int(r["condition_id"]),
                "family":r["family"],
                "filename":r["filename"],
            })

    cond=defaultdict(list)
    for r in raw:
        cond[(r["family"],r["condition_id"])].append(r)

    fold_of={}
    by_family=defaultdict(list)
    for key,rows in cond.items():
        by_family[key[0]].append((key,sum(r["human_mos"] for r in rows)/len(rows)))

    # Round-robin over MOS-sorted conditions gives every fold a range of
    # severities while maintaining group isolation.
    for fam,items in by_family.items():
        items.sort(key=lambda x:x[1])
        for i,(key,_) in enumerate(items):
            fold_of[key]=i%args.folds

    predictions=[]
    fold_details=[]
    for fold in range(args.folds):
        train=[]
        held=[]
        for r in raw:
            key=(r["family"],r["condition_id"])
            target_pen=5.0-r["human_mos"]
            if fold_of[key]==fold:
                held.append(r)
            else:
                train.append((r["x"],target_pen))
        bias,w=fit(train)
        for r in held:
            p=5.0-predict_penalty(r["x"],bias,w)
            predictions.append({
                **r,
                "prediction":p,
                "fold":fold,
            })
        fold_details.append({
            "fold":fold,
            "train_clips":len(train),
            "test_clips":len(held),
            "test_conditions":len(set((r["family"],r["condition_id"]) for r in held)),
            "weights":{name:value for (name,_),value in zip(FEATURES,w)},
            "bias":bias,
        })

    condition_rows=[]
    for key,rows in cond.items():
        pp=[r for r in predictions if (r["family"],r["condition_id"])==key]
        condition_rows.append({
            "family":key[0],
            "condition_id":key[1],
            "human_mos":sum(r["human_mos"] for r in pp)/len(pp),
            "prediction":sum(r["prediction"] for r in pp)/len(pp),
        })

    result={
        "protocol":"5-fold condition-group stratified out-of-fold validation",
        "utterance":metrics(predictions),
        "condition":metrics(condition_rows),
        "by_family":{},
        "folds":fold_details,
    }
    for fam in sorted(by_family):
        result["by_family"][fam]={
            "utterance":metrics([r for r in predictions if r["family"]==fam]),
            "condition":metrics([r for r in condition_rows if r["family"]==fam]),
        }

    with open(args.out,"w",encoding="utf-8") as f:
        json.dump(result,f,indent=2)
    print(json.dumps(result,indent=2))

if __name__=="__main__":
    main()
