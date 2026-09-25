#!/usr/bin/env python3
"""OpenACE development report for provisional Phase 4."""
import argparse,csv,json,math,random
from collections import defaultdict

def ranks(x):
    order=sorted(range(len(x)),key=lambda i:x[i]);out=[0.0]*len(x);i=0
    while i<len(order):
        j=i+1
        while j<len(order) and x[order[j]]==x[order[i]]:j+=1
        r=(i+j-1)/2+1
        for k in range(i,j):out[order[k]]=r
        i=j
    return out
def corr(a,b):
    ma=sum(a)/len(a);mb=sum(b)/len(b)
    aa=sum((x-ma)**2 for x in a);bb=sum((x-mb)**2 for x in b)
    return sum((x-ma)*(y-mb) for x,y in zip(a,b))/math.sqrt(aa*bb) if aa and bb else 0.0
def metric(rows,col):
    rr=[r for r in rows if r.get(col,"")!=""]
    y=[float(r["human_mushra"]) for r in rr];p=[float(r[col]) for r in rr]
    return {"n":len(rr),"pearson":corr(y,p),"spearman":corr(ranks(y),ranks(p))}
def bootstrap(rows,a,b,n=10000,seed=20260925):
    rr=[r for r in rows if r.get(a,"")!="" and r.get(b,"")!=""]
    groups=defaultdict(list)
    for r in rr:groups[(r["speaker"],r["emotion"])].append(r)
    keys=sorted(groups);rng=random.Random(seed);vals=[]
    for _ in range(n):
        s=[]
        for _ in keys:s.extend(groups[rng.choice(keys)])
        vals.append(metric(s,a)["pearson"]-metric(s,b)["pearson"])
    vals.sort()
    return {"samples":n,"clusters":len(keys),"delta_pearson":metric(rr,a)["pearson"]-metric(rr,b)["pearson"],
            "ci95":[vals[int(.025*(n-1))],vals[int(.975*(n-1))]]}
def group(rows,key,cols):
    return {v:{c:metric([r for r in rows if r[key]==v],c) for c in cols}
            for v in sorted({r[key] for r in rows})}
def main():
    ap=argparse.ArgumentParser();ap.add_argument("csv");ap.add_argument("--out",required=True);a=ap.parse_args()
    rows=list(csv.DictReader(open(a.csv,newline="",encoding="utf-8")))
    cols=["phase4_mos","phase4_native_mos","phase3_mos","polqa_mos","published_visqol_mos"]
    out={
      "status":"development diagnostic, not final holdout evidence",
      "dataset":"EARS-EMO-OpenACE",
      "overall":{c:metric(rows,c) for c in cols},
      "phase4_vs_phase3":bootstrap(rows,"phase4_mos","phase3_mos"),
      "phase4_vs_polqa":bootstrap(rows,"phase4_mos","polqa_mos"),
      "by_codec":group(rows,"codec",["phase4_mos","phase3_mos","polqa_mos"]),
      "by_emotion":group(rows,"emotion",["phase4_mos","phase3_mos","polqa_mos"]),
    }
    open(a.out,"w",encoding="utf-8").write(json.dumps(out,indent=2)+"\n")
    print(json.dumps(out,indent=2))
if __name__=="__main__":main()
