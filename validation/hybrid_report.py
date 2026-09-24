#!/usr/bin/env python3
import argparse,csv,json,math
from collections import defaultdict
def pc(a,b):
 m=sum(a)/len(a);n=sum(b)/len(b);u=sum((x-m)*(y-n) for x,y in zip(a,b));d=(sum((x-m)**2 for x in a)*sum((y-n)**2 for y in b))**.5;return u/d if d else 0
def ranks(v):
 o=sorted(range(len(v)),key=lambda i:v[i]);r=[0.]*len(v);i=0
 while i<len(o):
  j=i+1
  while j<len(o) and v[o[j]]==v[o[i]]:j+=1
  q=(i+j-1)/2+1
  for k in range(i,j):r[o[k]]=q
  i=j
 return r
def met(rows):
 y=[float(r["human_mos"]) for r in rows];p=[float(r["hybrid_mos"]) for r in rows];e=[a-b for a,b in zip(p,y)]
 return {"n":len(y),"pearson":pc(p,y),"spearman":pc(ranks(p),ranks(y)),"rmse":(sum(x*x for x in e)/len(e))**.5,"mae":sum(abs(x) for x in e)/len(e),"bias":sum(e)/len(e)}
def main():
 ap=argparse.ArgumentParser();ap.add_argument("csv");ap.add_argument("--out",required=True);a=ap.parse_args();rows=list(csv.DictReader(open(a.csv,newline="",encoding="utf-8")))
 out={"utterance":met(rows)}
 if rows[0].get("condition_id",""):
  g=defaultdict(list)
  for r in rows:g[r["condition_id"]].append(r)
  c=[]
  for cid,z in g.items():c.append({"human_mos":sum(float(x["human_mos"]) for x in z)/len(z),"hybrid_mos":sum(float(x["hybrid_mos"]) for x in z)/len(z)})
  out["condition"]=met(c)
 open(a.out,"w").write(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
if __name__=="__main__":main()
