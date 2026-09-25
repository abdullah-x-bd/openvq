#!/usr/bin/env python3
"""Report a locked Phase 4 native holdout result."""
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
def pearson(a,b):
    ma=sum(a)/len(a);mb=sum(b)/len(b)
    num=sum((x-ma)*(y-mb) for x,y in zip(a,b))
    den=math.sqrt(sum((x-ma)**2 for x in a)*sum((y-mb)**2 for y in b))
    return num/den if den else 0.0
def metrics(y,p):
    e=[b-a for a,b in zip(y,p)]
    return {"n":len(y),"pearson":pearson(y,p),"spearman":pearson(ranks(y),ranks(p)),
      "rmse":math.sqrt(sum(x*x for x in e)/len(e)),
      "mae":sum(abs(x) for x in e)/len(e),"bias":sum(e)/len(e)}
def grouped(rows):
    groups={}
    for r in rows:
        cid=r.get("condition_id","")
        if not cid:return None
        groups.setdefault(cid,[]).append(r)
    y=[];p=[]
    for rr in groups.values():
        y.append(sum(float(x["human_mos"]) for x in rr)/len(rr))
        p.append(sum(float(x["openvq_mos"]) for x in rr)/len(rr))
    return metrics(y,p)

def main():
    ap=argparse.ArgumentParser();ap.add_argument("csv");ap.add_argument("--out",required=True)
    a=ap.parse_args();rows=list(csv.DictReader(open(a.csv,newline="",encoding="utf-8")))
    y=[float(r["human_mos"]) for r in rows];p=[float(r["openvq_mos"]) for r in rows]
    u=metrics(y,p);g=grouped(rows)
    passes=u["pearson"]>=.70 and u["spearman"]>=.70 and u["rmse"]<=.80
    out={"model_id":"phase4-native-poly2-balanced-2026-09-25-v1",
      "family":rows[0].get("family","") if rows else "",
      "utterance":u,"condition":g,
      "criterion":{"pearson_min":.70,"spearman_min":.70,"rmse_max":.80},
      "passes_external_generalization_criterion":passes}
    open(a.out,"w",encoding="utf-8").write(json.dumps(out,indent=2)+"\n")
    print(json.dumps(out,indent=2))
    if not passes:raise SystemExit(2)

if __name__=="__main__":main()
