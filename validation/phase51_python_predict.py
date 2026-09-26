#!/usr/bin/env python3
"""Reference Python predictor for an exported Phase 5.1 report."""
import argparse,csv,json
from pathlib import Path
import numpy as np

def basis(x,mode):
    x=np.asarray(x,float)
    if mode=="linear":return x
    out=list(x)
    for i in range(len(x)):
        for j in range(i,len(x)):out.append(x[i]*x[j])
    return np.asarray(out,float)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("report");ap.add_argument("features");ap.add_argument("output")
    a=ap.parse_args()
    model=json.loads(Path(a.report).read_text())["selected_export"]
    rows=list(csv.DictReader(open(a.features,newline="",encoding="utf-8")))
    mean=np.asarray(model["mean"],float);scale=np.asarray(model["scale"],float)
    theta=np.asarray(model["theta"],float)
    out=[]
    for r in rows:
        x=basis([float(r[f]) for f in model["features"]],model["mode"])
        q=float(np.clip(theta[0]+((x-mean)/scale)@theta[1:],0,1))
        out.append({**r,"phase51_quality":q,"phase51_mos":1+4*q})
    with open(a.output,"w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=list(out[0]));w.writeheader();w.writerows(out)
    print("predictions",len(out))
if __name__=="__main__":main()
