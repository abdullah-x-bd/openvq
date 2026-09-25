#!/usr/bin/env python3
import argparse,csv,json,math,random
DEFAULT_MARGIN=0.10
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
    e=[a-b for a,b in zip(p,y)]
    return {"n":len(y),"pearson":pearson(y,p),"spearman":pearson(ranks(y),ranks(p)),
      "rmse":math.sqrt(sum(z*z for z in e)/len(e)),"mae":sum(abs(z) for z in e)/len(e),
      "bias":sum(e)/len(e)}
def grouped(rows,pred):
    groups={}
    for r in rows:
        condition=r.get("condition_id","")
        if not condition:return None
        # Condition IDs may repeat across degradation families (for example
        # in TCD-VoIP), so family is part of the condition identity.
        k=(r.get("family",""),condition)
        groups.setdefault(k,[]).append(r)
    y=[];p=[]
    for rr in groups.values():
        y.append(sum(float(x["human_mos"]) for x in rr)/len(rr))
        p.append(sum(float(x[pred]) for x in rr)/len(rr))
    return metrics(y,p)
def bootstrap_delta(rows,nboot,seed):
    rng=random.Random(seed);vals=[];n=len(rows)
    for _ in range(nboot):
        rr=[rows[rng.randrange(n)] for _ in range(n)]
        y=[float(r["human_mos"]) for r in rr]
        o=[float(r["openvq_mos"]) for r in rr]
        q=[float(r["polqa_mos"]) for r in rr]
        vals.append(metrics(y,o)["rmse"]-metrics(y,q)["rmse"])
    vals.sort()
    return {"delta_rmse_ci95":[vals[int(.025*(nboot-1))],vals[int(.975*(nboot-1))]],"bootstrap_samples":nboot}
def main():
    ap=argparse.ArgumentParser();ap.add_argument("csv");ap.add_argument("--out",required=True)
    ap.add_argument("--margin",type=float,default=DEFAULT_MARGIN);ap.add_argument("--bootstrap",type=int,default=10000)
    ap.add_argument("--seed",type=int,default=20260924);a=ap.parse_args()
    rows=list(csv.DictReader(open(a.csv,newline="",encoding="utf-8")))
    if not rows or not {"human_mos","openvq_mos","visqol_mos"}.issubset(rows[0]):
        raise SystemExit("CSV requires human_mos, openvq_mos and visqol_mos")
    y=[float(r["human_mos"]) for r in rows]
    out={"margin_rmse_mos":a.margin,"utterance":{},"condition":{}}
    for col in ["openvq_mos","visqol_mos"]:
        out["utterance"][col]=metrics(y,[float(r[col]) for r in rows]);g=grouped(rows,col)
        if g:out["condition"][col]=g
    if "polqa_mos" in rows[0] and all(r.get("polqa_mos","")!="" for r in rows):
        out["utterance"]["polqa_mos"]=metrics(y,[float(r["polqa_mos"]) for r in rows]);g=grouped(rows,"polqa_mos")
        if g:out["condition"]["polqa_mos"]=g
        b=bootstrap_delta(rows,a.bootstrap,a.seed)
        out["openvq_vs_polqa"]={"delta_rmse":out["utterance"]["openvq_mos"]["rmse"]-out["utterance"]["polqa_mos"]["rmse"],**b,
          "noninferior":b["delta_rmse_ci95"][1] < a.margin}
    else:out["polqa_status"]="licensed POLQA scores not supplied; no POLQA parity conclusion is possible"
    open(a.out,"w",encoding="utf-8").write(json.dumps(out,indent=2)+"\n");print(json.dumps(out,indent=2))
if __name__=="__main__":main()
