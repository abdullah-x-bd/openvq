#!/usr/bin/env python3
import argparse,csv,json,math
META={"human_mos","condition_id","family","filename"}
def derived(x):
    z=dict(x);v=sorted(x.values(),reverse=True);z["__max"]=v[0];z["__top3mean"]=sum(v[:3])/min(3,len(v))
    for a,b,n in [("echo","base","__echo_base"),("choppiness","bad_interval","__chop_bad"),("residual","noisiness","__res_noise"),("clipping","bad_interval","__clip_bad"),("visqol_speech","base","__visqol_base")]:
        if a in x and b in x:z[n]=x[a]*x[b]
    return z
def basis(x,names,knots):
    z=derived(x);return [max(0,z[n]-k) for n in names for k in knots]
def main():
    ap=argparse.ArgumentParser();ap.add_argument("features");ap.add_argument("model");ap.add_argument("output");a=ap.parse_args()
    m=json.load(open(a.model));rows=list(csv.DictReader(open(a.features,newline="",encoding="utf-8")))
    fields=list(rows[0])+["hybrid_mos"]
    with open(a.output,"w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader()
        for r in rows:
            x={k:max(0,min(1,float(r[k]))) for k in m["features"]}
            p=basis(x,m["derived_names"],m["knots"])
            mos=max(1,min(5,5-m["bias"]-sum(a*b for a,b in zip(m["weights"],p))))
            r["hybrid_mos"]=mos;w.writerow(r)
if __name__=="__main__":main()
