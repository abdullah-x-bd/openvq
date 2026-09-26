#!/usr/bin/env python3
"""Phase 5.1 fixed-evidence ablation and generalization evaluation.

This script deliberately separates:
1. grouped within-corpus transfer,
2. leave-corpus-out transfer,
3. processing-family transfer,
4. model-family ablation.

Only constrained linear/quadratic models are eligible for export. The small MLP
is a diagnostic representation test and cannot silently become the shipped
scorer.
"""
import argparse,csv,json,math
from collections import defaultdict
from pathlib import Path

import numpy as np
from scipy.optimize import LinearConstraint,minimize
from sklearn.neural_network import MLPRegressor
from sklearn.preprocessing import StandardScaler

from phase51_feature_schema import LEGACY19,RICH_V2

ALPHAS=[3.0,10.0,30.0,100.0,300.0,1000.0]
MODES=["linear","poly2"]
MONOTONIC=[
    "dropout","dropout_count","noise","lowpass","clipping","attenuation",
    "clock_drift","time_scale","mixed",
]
FOLDS=5
MODEL_ID="phase5.1-native-repaired-2026-09-26-v1"

def read_csv(path):
    with open(path,newline="",encoding="utf-8") as f:
        return list(csv.DictReader(f))

def ranks(v):
    v=np.asarray(v,float);o=np.argsort(v,kind="mergesort");r=np.empty(len(v));i=0
    while i<len(o):
        j=i+1
        while j<len(o) and v[o[j]]==v[o[i]]:j+=1
        r[o[i:j]]=(i+j-1)/2+1;i=j
    return r

def corr(a,b):
    a=np.asarray(a,float);b=np.asarray(b,float)
    if len(a)<2 or np.std(a)<1e-12 or np.std(b)<1e-12:return 0.0
    return float(np.corrcoef(a,b)[0,1])

def metrics(y,p):
    y=np.asarray(y,float);p=np.asarray(p,float);e=p-y
    return {
        "n":int(len(y)),
        "pearson":corr(y,p),
        "spearman":corr(ranks(y),ranks(p)),
        "rmse_normalized":float(np.sqrt(np.mean(e*e))),
        "rmse_mos_equivalent":float(4*np.sqrt(np.mean(e*e))),
        "mae_mos_equivalent":float(4*np.mean(np.abs(e))),
        "bias_mos_equivalent":float(4*np.mean(e)),
        "floor_fraction":float(np.mean(p<=1e-6)),
        "ceiling_fraction":float(np.mean(p>=1-1e-6)),
    }

def load(paths):
    rows=[]
    for spec in paths:
        name,path=spec.split("=",1)
        for r in read_csv(path):
            if r.get("dataset") and r["dataset"]!=name:
                raise SystemExit(f"dataset mismatch {name} vs {r['dataset']} in {path}")
            rr=dict(r);rr["dataset"]=name;rows.append(rr)
    return rows

def feature_matrix(rows,features,mode):
    x=np.asarray([[float(r[f]) for f in features] for r in rows],float)
    if mode=="linear":return x
    out=[x]
    products=[]
    for i in range(x.shape[1]):
        for j in range(i,x.shape[1]):
            products.append((x[:,i]*x[:,j])[:,None])
    return np.hstack([x]+products)

def basis_names(features,mode):
    if mode=="linear":return list(features)
    out=list(features)
    for i,a in enumerate(features):
        for b in features[i:]:out.append(a+"*"+b)
    return out

def targets(rows):return np.asarray([float(r["target_normalized"]) for r in rows],float)
def datasets(rows):return np.asarray([r["dataset"] for r in rows])
def groups(rows):return np.asarray([r["dataset"]+":"+r["group_id"] for r in rows])
def systems(rows):return np.asarray([r["dataset"]+":"+r["system_id"] for r in rows])

def equal_domain_weights(ds):
    w=np.zeros(len(ds),float)
    for d in sorted(set(ds)):
        m=ds==d;w[m]=1.0/max(1,int(m.sum()))
    return w/w.sum()*len(w)

def make_group_folds(rows,k=FOLDS):
    g=groups(rows);d=datasets(rows);mapping={}
    for ds in sorted(set(d)):
        unique=sorted(set(g[d==ds]))
        for i,x in enumerate(unique):mapping[x]=i%k
    return np.asarray([mapping[x] for x in g],int)

def engineering_basis(eng,features,mode):
    return feature_matrix(eng,features,mode)

def constraint_matrix(eng,features,mode,mean,scale):
    x=engineering_basis(eng,features,mode)
    z=(x-mean)/scale;a=np.column_stack([np.ones(len(z)),z])
    rr=[];lo=[];hi=[]
    ident=next(i for i,r in enumerate(eng) if r["family"]=="clean")
    rr.append(a[ident]);lo.append(.875);hi.append(np.inf)
    for i,r in enumerate(eng):
        if r["family"]=="sample_rate_identity":
            rr.append(a[i]);lo.append(.80);hi.append(np.inf)
        if r["family"]=="delay":
            rr.append(a[i]-a[ident]);lo.append(-.1125);hi.append(.1125)
    for fam in MONOTONIC:
        inds=sorted([i for i,r in enumerate(eng) if r["family"]==fam],
                    key=lambda i:float(eng[i]["level"]))
        for u,v in zip(inds,inds[1:]):
            rr.append(a[v]-a[u]);lo.append(-np.inf);hi.append(0.0)
    return np.asarray(rr),np.asarray(lo),np.asarray(hi)

def fit_constrained(rows,eng,features,mode,alpha):
    X=feature_matrix(rows,features,mode);y=targets(rows);ds=datasets(rows)
    w=equal_domain_weights(ds)
    mean=np.average(X,axis=0,weights=w)
    scale=np.sqrt(np.average((X-mean)**2,axis=0,weights=w));scale[scale<1e-8]=1.0
    z=(X-mean)/scale;a=np.column_stack([np.ones(len(z)),z])
    sw=np.sqrt(w);aw=a*sw[:,None];yw=y*sw
    reg=np.eye(a.shape[1]);reg[0,0]=0.0
    H=aw.T@aw+alpha*reg;g=aw.T@yw
    initial=np.linalg.solve(H,g)
    C,lo,hi=constraint_matrix(eng,features,mode,mean,scale)
    fun=lambda th:0.5*th@H@th-g@th
    jac=lambda th:H@th-g
    res=minimize(fun,initial,jac=jac,constraints=[LinearConstraint(C,lo,hi)],
                 method="SLSQP",options={"maxiter":1800,"ftol":1e-9,"disp":False})
    if not res.success:raise RuntimeError("constrained fit failed: "+res.message)
    return {"mean":mean,"scale":scale,"theta":res.x,"iterations":int(res.nit),
            "mode":mode,"alpha":alpha,"features":features}

def predict_constrained(model,rows):
    X=feature_matrix(rows,model["features"],model["mode"])
    z=(X-model["mean"])/model["scale"]
    return np.clip(model["theta"][0]+z@model["theta"][1:],0,1)

def objective(by_dataset):
    corrs=[]
    for m in by_dataset.values():corrs.extend([m["pearson"],m["spearman"]])
    return {
      "worst_correlation":float(min(corrs)),
      "mean_correlation":float(np.mean(corrs)),
      "worst_rmse_mos":float(max(m["rmse_mos_equivalent"] for m in by_dataset.values())),
    }

def grouped_cv(rows,eng,features,mode,alpha):
    ff=make_group_folds(rows);pred=np.zeros(len(rows));its=[]
    for f in range(FOLDS):
        tr=[r for i,r in enumerate(rows) if ff[i]!=f]
        va_idx=[i for i in range(len(rows)) if ff[i]==f]
        va=[rows[i] for i in va_idx]
        model=fit_constrained(tr,eng,features,mode,alpha);its.append(model["iterations"])
        pv=predict_constrained(model,va)
        for i,p in zip(va_idx,pv):pred[i]=p
    y=targets(rows);ds=datasets(rows);by={}
    for d in sorted(set(ds)):
        m=ds==d;by[d]=metrics(y[m],pred[m])
    return {"by_dataset":by,"objective":objective(by),"iterations":its}

def select_constrained(rows,eng,features):
    grid=[];best=None
    for mode in MODES:
        for alpha in ALPHAS:
            cv=grouped_cv(rows,eng,features,mode,alpha)
            item={"mode":mode,"alpha":alpha,**cv};grid.append(item)
            o=cv["objective"]
            key=(o["worst_correlation"],o["mean_correlation"],-o["worst_rmse_mos"],
                 1 if mode=="linear" else 0,-alpha)
            if best is None or key>best[0]:best=(key,item)
    return best[1],grid

def leave_corpus_out(rows,eng,features):
    out={}
    for held in sorted(set(r["dataset"] for r in rows)):
        train=[r for r in rows if r["dataset"]!=held]
        test=[r for r in rows if r["dataset"]==held]
        selected,_=select_constrained(train,eng,features)
        model=fit_constrained(train,eng,features,selected["mode"],selected["alpha"])
        out[held]={
            "selected":{"mode":selected["mode"],"alpha":selected["alpha"],
                        "inner_objective":selected["objective"]},
            "test":metrics(targets(test),predict_constrained(model,test)),
        }
    vals=[min(v["test"]["pearson"],v["test"]["spearman"]) for v in out.values()]
    return {"by_held_corpus":out,"worst_held_corpus_correlation":float(min(vals)),
            "mean_held_corpus_correlation":float(np.mean(vals))}

def processing_transfer(rows,eng,features,selected):
    out={}
    for ds in sorted(set(r["dataset"] for r in rows)):
        dr=[r for r in rows if r["dataset"]==ds]
        unique=sorted(set(r["system_id"] for r in dr if r["system_id"]))
        if len(unique)<2:continue
        # Exact leave-one-system-out for compact system sets. For highly
        # granular condition IDs, create five deterministic system folds.
        cases=[]
        if len(unique)<=20:
            cases=[([u],u) for u in unique]
        else:
            for f in range(5):
                hs=[u for i,u in enumerate(unique) if i%5==f]
                cases.append((hs,"fold"+str(f)))
        reports={}
        for held,label in cases:
            test=[r for r in dr if r["system_id"] in held]
            train=[r for r in rows if not (r["dataset"]==ds and r["system_id"] in held)]
            if len(test)<4 or len(train)<20:continue
            model=fit_constrained(train,eng,features,selected["mode"],selected["alpha"])
            reports[label]=metrics(targets(test),predict_constrained(model,test))
        if reports:
            vals=[min(x["pearson"],x["spearman"]) for x in reports.values()]
            out[ds]={"systems":len(unique),"reports":reports,
                     "worst_correlation":float(min(vals)),
                     "mean_correlation":float(np.mean(vals))}
    return out

def mlp_cv(rows,features):
    ff=make_group_folds(rows)
    configs=[((16,),0.01),((32,16),0.01),((32,16),0.1),((48,24),0.1)]
    grid=[];best=None
    X=np.asarray([[float(r[f]) for f in features] for r in rows],float)
    y=targets(rows);ds=datasets(rows)
    for hidden,alpha in configs:
        pred=np.zeros(len(rows))
        for f in range(FOLDS):
            tr=ff!=f;va=ff==f
            scaler=StandardScaler().fit(X[tr])
            model=MLPRegressor(hidden_layer_sizes=hidden,activation="relu",
                alpha=alpha,max_iter=1200,random_state=20260926,
                early_stopping=True,validation_fraction=0.15,n_iter_no_change=40)
            model.fit(scaler.transform(X[tr]),y[tr])
            pred[va]=np.clip(model.predict(scaler.transform(X[va])),0,1)
        by={}
        for d in sorted(set(ds)):
            m=ds==d;by[d]=metrics(y[m],pred[m])
        obj=objective(by)
        item={"hidden":hidden,"alpha":alpha,"by_dataset":by,"objective":obj}
        grid.append(item)
        key=(obj["worst_correlation"],obj["mean_correlation"],-obj["worst_rmse_mos"])
        if best is None or key>best[0]:best=(key,item)
    return best[1],grid

def engineering_report(model,eng):
    p=predict_constrained(model,eng)
    rows=[]
    for r,v in zip(eng,p):
        rows.append({"family":r["family"],"level":float(r["level"]),"label":r["label"],
                     "mos":1+4*float(v)})
    families={}
    failures=[]
    clean=next(x["mos"] for x in rows if x["family"]=="clean")
    delay=[x["mos"] for x in rows if x["family"]=="delay"]
    max_delay=max(abs(x-clean) for x in delay)
    if clean<4.5:failures.append(f"clean MOS {clean:.3f} < 4.5")
    if max_delay>0.45+1e-9:failures.append(f"delay delta {max_delay:.3f} > 0.45")
    for fam in MONOTONIC:
        rr=sorted([x for x in rows if x["family"]==fam],key=lambda x:x["level"])
        if len(rr)>1:
            violations=sum(b["mos"]>a["mos"]+1e-8 for a,b in zip(rr,rr[1:]))
            families[fam]={"rows":rr,"local_increase_violations":violations}
            if violations:failures.append(f"{fam} has {violations} local reversals")
    return {"clean_mos":clean,"delay_max_delta":max_delay,"families":families,
            "failures":failures}

def emit_cpp(path,model):
    th=model["theta"];mean=model["mean"];scale=model["scale"]
    def arr(name,v):
        return f"inline constexpr std::array<double,{len(v)}> {name}={{{{"+",".join(f"{float(x):.17g}" for x in v)+"}}};\n"
    s="#pragma once\n#include <array>\nnamespace openvq::phase51_model {\n"
    s+=f'inline constexpr const char* kModelId="{MODEL_ID}";\n'
    s+=f'inline constexpr const char* kBasis="{model["mode"]}";\n'
    s+=f"inline constexpr double kIntercept={float(th[0]):.17g};\n"
    s+=arr("kMean",mean)+arr("kScale",scale)+arr("kWeights",th[1:])+"}\n"
    Path(path).write_text(s,encoding="utf-8")

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--dataset",action="append",required=True,
                    help="NAME=feature.csv")
    ap.add_argument("--engineering",required=True)
    ap.add_argument("--out",required=True)
    ap.add_argument("--cpp-out",required=True)
    a=ap.parse_args()
    rows=load(a.dataset);eng=read_csv(a.engineering)

    legacy_sel,legacy_grid=select_constrained(rows,eng,LEGACY19)
    rich_sel,rich_grid=select_constrained(rows,eng,RICH_V2)
    rich_model=fit_constrained(rows,eng,RICH_V2,rich_sel["mode"],rich_sel["alpha"])
    mlp_sel,mlp_grid=mlp_cv(rows,RICH_V2)

    result={
      "model_id":MODEL_ID,
      "status":"Phase 5.1 development result; no untouched external claim",
      "dataset_counts":{d:sum(r["dataset"]==d for r in rows)
                        for d in sorted(set(r["dataset"] for r in rows))},
      "ablations":{
        "legacy19_constrained":{"selected":legacy_sel,"grid":legacy_grid},
        "rich_v2_constrained":{"selected":rich_sel,"grid":rich_grid},
        "rich_v2_mlp_diagnostic":{"selected":mlp_sel,"grid":mlp_grid},
      },
      "leave_corpus_out":{
        "legacy19":leave_corpus_out(rows,eng,LEGACY19),
        "rich_v2":leave_corpus_out(rows,eng,RICH_V2),
      },
      "processing_transfer":processing_transfer(rows,eng,RICH_V2,rich_sel),
      "engineering_exported_model":engineering_report(rich_model,eng),
      "selected_export":{
        "feature_schema":"rich_v2","mode":rich_sel["mode"],"alpha":rich_sel["alpha"],
        "basis_names":basis_names(RICH_V2,rich_sel["mode"]),
      },
      "warning":"All five subjective corpora are development evidence. URGENT 2026 remains untouched.",
    }
    Path(a.out).write_text(json.dumps(result,indent=2,allow_nan=False)+"\n",encoding="utf-8")
    emit_cpp(a.cpp_out,rich_model)
    print(json.dumps({
      "model_id":MODEL_ID,
      "legacy_objective":legacy_sel["objective"],
      "rich_objective":rich_sel["objective"],
      "mlp_objective":mlp_sel["objective"],
      "leave_corpus_out_rich":result["leave_corpus_out"]["rich_v2"],
      "engineering_failures":result["engineering_exported_model"]["failures"],
    },indent=2,allow_nan=False))

if __name__=="__main__":main()
