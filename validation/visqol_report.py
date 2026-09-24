#!/usr/bin/env python3
import argparse,csv,json,math
from collections import defaultdict

def pearson(a,b):
    ma=sum(a)/len(a); mb=sum(b)/len(b)
    n=sum((x-ma)*(y-mb) for x,y in zip(a,b))
    d=(sum((x-ma)**2 for x in a)*sum((y-mb)**2 for y in b))**.5
    return n/d if d else 0
def ranks(v):
    order=sorted(range(len(v)),key=lambda i:v[i]); r=[0.]*len(v); i=0
    while i<len(order):
        j=i+1
        while j<len(order) and v[order[j]]==v[order[i]]:j+=1
        q=(i+j-1)/2+1
        for k in range(i,j):r[order[k]]=q
        i=j
    return r
def metrics(rows,key):
    y=[float(r["human_mos"]) for r in rows]; p=[float(r[key]) for r in rows]
    e=[a-b for a,b in zip(p,y)]
    return {"n":len(rows),"pearson":pearson(p,y),"spearman":pearson(ranks(p),ranks(y)),
            "rmse":(sum(x*x for x in e)/len(e))**.5,
            "mae":sum(abs(x) for x in e)/len(e),"bias":sum(e)/len(e)}
def main():
    ap=argparse.ArgumentParser(); ap.add_argument("csv"); ap.add_argument("--out",required=True); a=ap.parse_args()
    with open(a.csv,newline="",encoding="utf-8") as f: rows=list(csv.DictReader(f))
    out={"utterance":{k:metrics(rows,k) for k in ["visqol_speech_mos","visqol_audio_mos"]}}
    if "condition_id" in rows[0]:
        groups=defaultdict(list)
        for r in rows: groups[r["condition_id"]].append(r)
        cr=[]
        for cid,g in groups.items():
            cr.append({"human_mos":sum(float(x["human_mos"]) for x in g)/len(g),
                       "visqol_speech_mos":sum(float(x["visqol_speech_mos"]) for x in g)/len(g),
                       "visqol_audio_mos":sum(float(x["visqol_audio_mos"]) for x in g)/len(g)})
        out["condition"]={k:metrics(cr,k) for k in ["visqol_speech_mos","visqol_audio_mos"]}
    open(a.out,"w").write(json.dumps(out,indent=2)); print(json.dumps(out,indent=2))
if __name__=="__main__":main()
