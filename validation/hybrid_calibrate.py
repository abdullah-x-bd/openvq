#!/usr/bin/env python3
"""Fit a monotonic additive hinge model for OpenVQ MOS.

Every input is a degradation variable in [0,1]. Each feature is expanded into
non-decreasing hinge bases. All learned coefficients and the global bias are
projected non-negative, so worsening any single measured degradation cannot
increase predicted MOS.
"""
import argparse,csv,json,math,random

META={"human_mos","condition_id","family","filename"}
KNOTS=[0.0,0.15,0.30,0.45,0.60,0.75]
L2_GRID=[0.0005,0.001,0.003,0.01,0.03,0.1]

def load(path):
    with open(path,newline="",encoding="utf-8") as f:
        rows=list(csv.DictReader(f))
    feats=[k for k in rows[0] if k not in META]
    data=[({k:max(0,min(1,float(r[k]))) for k in feats},max(1,min(5,float(r["human_mos"])))) for r in rows]
    return feats,data

def derived(x):
    # Explicit monotone interactions for compounded severe impairments.
    z=dict(x)
    vals=sorted(x.values(),reverse=True)
    z["__max"]=vals[0]
    z["__top3mean"]=sum(vals[:3])/min(3,len(vals))
    for a,b,name in [
        ("echo","base","__echo_base"),
        ("choppiness","bad_interval","__chop_bad"),
        ("residual","noisiness","__res_noise"),
        ("clipping","bad_interval","__clip_bad"),
        ("visqol_speech","base","__visqol_base"),
    ]:
        if a in x and b in x:z[name]=x[a]*x[b]
    return z

def basis(x,names):
    z=derived(x); out=[]
    for name in names:
        v=z[name]
        for knot in KNOTS:out.append(max(0.0,v-knot))
    return out

def names_for(feats):
    dummy={k:0. for k in feats}
    return list(derived(dummy).keys())

def pred(phi,bias,w):
    return max(1,min(5,5-bias-sum(a*b for a,b in zip(w,phi))))

def train(feats,data,l2,epochs=12000,lr=.018):
    names=names_for(feats)
    phis=[basis(x,names) for x,_ in data]
    y=[t for _,t in data]
    w=[0.02]*len(phis[0]);bias=.02
    for ep in range(epochs):
        gb=0.;gw=[0.]*len(w)
        for p,t in zip(phis,y):
            raw=5-bias-sum(a*b for a,b in zip(w,p))
            q=max(1,min(5,raw))
            if raw<=1 or raw>=5:continue
            e=q-t;gb+=-2*e
            for i,v in enumerate(p):gw[i]+=-2*e*v
        n=len(y);bias=max(0,bias-lr*gb/n)
        for i in range(len(w)):
            w[i]=max(0,w[i]-lr*(gw[i]/n+2*l2*w[i]))
        if ep and ep%3000==0:lr*=.72
    return names,bias,w

def metrics(feats,data,names,bias,w):
    ys=[];ps=[]
    for x,y in data:ys.append(y);ps.append(pred(basis(x,names),bias,w))
    rmse=(sum((a-b)**2 for a,b in zip(ps,ys))/len(ys))**.5
    ma=sum(ys)/len(ys);mb=sum(ps)/len(ps)
    num=sum((a-ma)*(b-mb) for a,b in zip(ys,ps))
    den=(sum((a-ma)**2 for a in ys)*sum((b-mb)**2 for b in ps))**.5
    return {"rmse":rmse,"pearson":num/den if den else 0,"bias":sum(a-b for a,b in zip(ps,ys))/len(ys)}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("train");ap.add_argument("--dev",required=True);ap.add_argument("--out",required=True)
    a=ap.parse_args()
    feats,tr=load(a.train);feats2,dv=load(a.dev)
    if feats!=feats2:raise SystemExit("feature mismatch")
    trials=[]
    for l2 in L2_GRID:
        names,bias,w=train(feats,tr,l2)
        m=metrics(feats,dv,names,bias,w);trials.append((m["rmse"],l2,m))
        print("l2",l2,"dev",m,flush=True)
    _,best,devm=min(trials,key=lambda x:x[0])
    names,bias,w=train(feats,tr+dv,best,epochs=16000)
    model={"version":1,"features":feats,"derived_names":names,"knots":KNOTS,
           "bias":bias,"weights":w,"selected_l2":best,"dev_metrics":devm}
    open(a.out,"w").write(json.dumps(model,indent=2))
    print(json.dumps({"selected_l2":best,"dev_metrics":devm},indent=2))
if __name__=="__main__":main()
