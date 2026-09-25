#!/usr/bin/env python3
"""Development-only report for Phase-4 v2 on observed corpora."""
import argparse,csv,json,math

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
      "rmse":math.sqrt(sum(z*z for z in e)/len(e)),"mae":sum(abs(z) for z in e)/len(e),
      "bias":sum(e)/len(e)}
def main():
    ap=argparse.ArgumentParser();ap.add_argument("csv");ap.add_argument("--target",choices=["mos","mushra"],required=True);ap.add_argument("--out",required=True);a=ap.parse_args()
    rows=list(csv.DictReader(open(a.csv,newline="",encoding="utf-8")))
    p=[float(r["phase4_v2_mos"]) for r in rows]
    if a.target=="mos":y=[float(r["human_mos"]) for r in rows]
    else:y=[1.0+4.0*float(r["human_mushra"])/100.0 for r in rows]
    out={"status":"development only; not external validation","target_scale":"MOS-equivalent 1..5","phase4_v2":metrics(y,p)}
    open(a.out,"w",encoding="utf-8").write(json.dumps(out,indent=2)+"\n");print(json.dumps(out,indent=2))
if __name__=="__main__":main()
