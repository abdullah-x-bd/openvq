#!/usr/bin/env python3
"""Report raw and mapped human-MOS performance for a frozen holdout."""
from __future__ import annotations
import argparse,csv,json,math
from collections import defaultdict

def pearson(a,b):
    if len(a)<2:return 0.0
    ma=sum(a)/len(a); mb=sum(b)/len(b)
    num=sum((x-ma)*(y-mb) for x,y in zip(a,b))
    den=math.sqrt(sum((x-ma)**2 for x in a)*sum((y-mb)**2 for y in b))
    return num/den if den else 0.0

def ranks(v):
    order=sorted(range(len(v)),key=lambda i:v[i])
    r=[0.0]*len(v);i=0
    while i<len(order):
        j=i+1
        while j<len(order) and v[order[j]]==v[order[i]]:j+=1
        q=(i+j-1)/2+1
        for k in range(i,j):r[order[k]]=q
        i=j
    return r

def solve(a,b):
    n=len(b)
    m=[list(a[i])+[b[i]] for i in range(n)]
    for col in range(n):
        pivot=max(range(col,n),key=lambda r:abs(m[r][col]))
        m[col],m[pivot]=m[pivot],m[col]
        if abs(m[col][col])<1e-12:
            return [0.0]*n
        q=m[col][col]
        m[col]=[x/q for x in m[col]]
        for r in range(n):
            if r==col:continue
            q=m[r][col]
            m[r]=[x-q*y for x,y in zip(m[r],m[col])]
    return [m[i][-1] for i in range(n)]

def polyfit(x,y,degree):
    # least-squares normal equations with tiny ridge for numerical stability
    p=degree+1
    ata=[[0.0]*p for _ in range(p)]
    aty=[0.0]*p
    for xi,yi in zip(x,y):
        z=[xi**j for j in range(p)]
        for j in range(p):
            aty[j]+=z[j]*yi
            for k in range(p):ata[j][k]+=z[j]*z[k]
    for i in range(p):ata[i][i]+=1e-9
    return solve(ata,aty)

def polyval(coef,x):
    return sum(c*(x**i) for i,c in enumerate(coef))

def metrics(rows):
    y=[r["human_mos"] for r in rows]
    p=[r["openvq_mos"] for r in rows]
    e=[a-b for a,b in zip(p,y)]
    c1=polyfit(p,y,1); m1=[polyval(c1,x) for x in p]
    c3=polyfit(p,y,3); m3=[polyval(c3,x) for x in p]
    return {
        "n":len(rows),
        "pearson":pearson(p,y),
        "spearman":pearson(ranks(p),ranks(y)),
        "rmse":math.sqrt(sum(x*x for x in e)/len(e)),
        "mae":sum(abs(x) for x in e)/len(e),
        "bias":sum(e)/len(e),
        "mapped_rmse_linear":math.sqrt(sum((a-b)**2 for a,b in zip(m1,y))/len(y)),
        "mapped_rmse_cubic":math.sqrt(sum((a-b)**2 for a,b in zip(m3,y))/len(y)),
        "human_mean":sum(y)/len(y),
        "prediction_mean":sum(p)/len(p),
        "mapping_linear":c1,
        "mapping_cubic":c3,
    }

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("predictions")
    ap.add_argument("--out",required=True)
    args=ap.parse_args()
    rows=[]
    with open(args.predictions,newline="",encoding="utf-8") as f:
        for r in csv.DictReader(f):
            rows.append({
                **r,
                "human_mos":float(r["human_mos"]),
                "openvq_mos":float(r["openvq_mos"]),
            })
    by={}
    for r in rows:
        key=r.get("condition_id","")
        by.setdefault(key,[]).append(r)
    cond=[]
    for key,rr in by.items():
        cond.append({
            "condition_id":key,
            "human_mos":sum(x["human_mos"] for x in rr)/len(rr),
            "openvq_mos":sum(x["openvq_mos"] for x in rr)/len(rr),
        })
    residuals=sorted([
        {
            "filename":r["filename"],
            "condition_id":r.get("condition_id",""),
            "human_mos":r["human_mos"],
            "openvq_mos":r["openvq_mos"],
            "error":r["openvq_mos"]-r["human_mos"],
        } for r in rows
    ],key=lambda x:abs(x["error"]),reverse=True)
    out={
        "utterance":metrics(rows),
        "condition":metrics(cond) if len(cond)>1 else None,
        "condition_count":len(cond),
        "worst_25_residuals":residuals[:25],
    }
    Path=None
    with open(args.out,"w",encoding="utf-8") as f:json.dump(out,f,indent=2)
    print(json.dumps(out,indent=2))

if __name__=="__main__":main()
