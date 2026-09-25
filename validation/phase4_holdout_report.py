#!/usr/bin/env python3
"""Report a frozen Phase-4 v2 holdout without fitting or remapping."""
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
def metrics(y,p):
    e=[b-a for a,b in zip(y,p)]
    return {"n":len(y),"pearson":corr(y,p),"spearman":corr(ranks(y),ranks(p)),
      "rmse":math.sqrt(sum(z*z for z in e)/len(e)),
      "mae":sum(abs(z) for z in e)/len(e),"bias":sum(e)/len(e)}
def pred(row,col):
    if col=="phase4_v2_mos":return float(row[col])
    if col=="visqol_speech_mos":return 5.0-4.0*float(row["visqol_speech"])
    if col=="visqol_audio_mos":return 5.0-4.0*float(row["visqol_audio"])
    raise KeyError(col)
def grouped(rows,col):
    groups=defaultdict(list)
    for r in rows:groups[(r.get("family",""),r.get("condition_id",""))].append(r)
    y=[];p=[]
    for rr in groups.values():
        y.append(sum(float(x["human_mos"]) for x in rr)/len(rr))
        p.append(sum(pred(x,col) for x in rr)/len(rr))
    return metrics(y,p)
def bootstrap(rows,col,n,seed):
    rng=random.Random(seed);vals={"pearson":[],"spearman":[],"rmse":[]}
    for _ in range(n):
        rr=[rows[rng.randrange(len(rows))] for _ in rows]
        y=[float(r["human_mos"]) for r in rr];p=[pred(r,col) for r in rr]
        m=metrics(y,p)
        for k in vals:vals[k].append(m[k])
    out={}
    for k,v in vals.items():
        v.sort();out[k+"_ci95"]=[v[int(.025*(n-1))],v[int(.975*(n-1))]]
    return out
def main():
    ap=argparse.ArgumentParser();ap.add_argument("csv");ap.add_argument("--out",required=True)
    ap.add_argument("--bootstrap",type=int,default=10000);ap.add_argument("--seed",type=int,default=20260925)
    a=ap.parse_args()
    rows=list(csv.DictReader(open(a.csv,newline="",encoding="utf-8")))
    if len(rows)!=240:raise SystemExit(f"expected 240 holdout rows, got {len(rows)}")
    y=[float(r["human_mos"]) for r in rows]
    cols=["phase4_v2_mos","visqol_speech_mos","visqol_audio_mos"]
    utterance={c:metrics(y,[pred(r,c) for r in rows]) for c in cols}
    condition={c:grouped(rows,c) for c in cols}
    ci=bootstrap(rows,"phase4_v2_mos",a.bootstrap,a.seed)
    gate={
      "requirements":{"pearson_min":0.75,"spearman_min":0.75,"rmse_max_mos":0.80},
      "passed":bool(
        utterance["phase4_v2_mos"]["pearson"]>=0.75 and
        utterance["phase4_v2_mos"]["spearman"]>=0.75 and
        utterance["phase4_v2_mos"]["rmse"]<=0.80
      )
    }
    out={
      "status":"frozen external holdout; no fitting performed",
      "model_id":rows[0]["phase4_v2_model_id"],
      "family":rows[0].get("family",""),
      "utterance":utterance,"condition":condition,
      "phase4_v2_bootstrap":ci,"generalization_gate":gate
    }
    open(a.out,"w",encoding="utf-8").write(json.dumps(out,indent=2)+"\n")
    print(json.dumps(out,indent=2))
if __name__=="__main__":main()
