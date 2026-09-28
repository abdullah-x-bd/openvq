#!/usr/bin/env python3
"""Phase 6B fair summary-model experiment.

This evaluator gives the small ANN the evaluation Phase 5.1 did not:
- corpus-balanced fitting,
- fixed seeds,
- group-respecting inner early stopping,
- nested leave-corpus-out selection,
- per-candidate engineering reports,
- unclipped and clipped saturation reporting.

The Phase 5.1 evaluator remains unchanged for historical reproduction.
"""
import argparse,csv,copy,json,math,warnings
from collections import defaultdict
from pathlib import Path
import numpy as np
from sklearn.linear_model import Ridge
from sklearn.neural_network import MLPRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.exceptions import ConvergenceWarning
from phase6_feature_schema import RICH_V3
import phase51_evaluate as constrained

SEEDS=[20260926,20260927,20260928]
ALPHAS=[0.03,0.1,0.3]
HIDDEN=(48,24)
FOLDS=5
SCOPED_MONOTONIC={"dropout","dropout_count","noise","lowpass","clipping","mixed"}

def read(path):
    return list(csv.DictReader(open(path,newline="",encoding="utf-8")))

def load(specs):
    rows=[]
    for spec in specs:
        name,path=spec.split("=",1)
        for r in read(path):
            rr=dict(r);rr["dataset"]=name
            for f in RICH_V3:
                if f not in rr: raise SystemExit(f"missing {f} in {path}")
            rows.append(rr)
    return rows

def x(rows):return np.asarray([[float(r[f]) for f in RICH_V3] for r in rows],float)
def y(rows):return np.asarray([float(r["target_normalized"]) for r in rows],float)
def ds(rows):return np.asarray([r["dataset"] for r in rows])
def gid(r):return r["dataset"]+":"+(r.get("canonical_source_id") or r.get("group_id") or r.get("filename",""))
def sid(r):return r.get("system_id","")
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
def metrics(yy,pp_raw):
    yy=np.asarray(yy,float);raw=np.asarray(pp_raw,float);pp=np.clip(raw,0,1);e=pp-yy
    return {
      "n":len(yy),"pearson":corr(yy,pp),"spearman":corr(ranks(yy),ranks(pp)),
      "rmse_normalized":float(np.sqrt(np.mean(e*e))),
      "mae_normalized":float(np.mean(np.abs(e))),"bias_normalized":float(np.mean(e)),
      "floor_fraction":float(np.mean(pp<=1e-6)),"ceiling_fraction":float(np.mean(pp>=1-1e-6)),
      "near_floor_fraction":float(np.mean(pp<=0.05)),"near_ceiling_fraction":float(np.mean(pp>=0.95)),
      "raw_below_zero_fraction":float(np.mean(raw<0)),"raw_above_one_fraction":float(np.mean(raw>1)),
    }
def objective(by):
    vals=[]
    for m in by.values():vals += [m["pearson"],m["spearman"]]
    return {"worst_correlation":float(min(vals)),"mean_correlation":float(np.mean(vals)),
            "worst_rmse_normalized":float(max(m["rmse_normalized"] for m in by.values()))}
def corpus_weights(rows):
    d=ds(rows);w=np.zeros(len(rows))
    for name in sorted(set(d)):
        m=d==name;w[m]=1/max(1,int(m.sum()))
    return w/w.sum()*len(rows)
def folds(rows,k=FOLDS):
    groups=defaultdict(list)
    for r in rows:groups[r["dataset"]].append(gid(r))
    mapping={}
    for d,gg in groups.items():
        for i,g in enumerate(sorted(set(gg))):mapping[g]=i%k
    return np.asarray([mapping[gid(r)] for r in rows])
def poly2(z):
    cols=[z]
    for i in range(z.shape[1]):
        for j in range(i,z.shape[1]):cols.append((z[:,i]*z[:,j])[:,None])
    return np.hstack(cols)
def balanced_resample(rows,seed):
    rng=np.random.default_rng(seed);d=ds(rows);target=max(int(np.sum(d==q)) for q in set(d));idx=[]
    for q in sorted(set(d)):
        ii=np.where(d==q)[0]
        idx.extend(rng.choice(ii,target,replace=len(ii)<target).tolist())
    rng.shuffle(idx);return np.asarray(idx,int)
def split_groups(rows,seed,fraction=.15):
    tr=[];va=[]
    for d in sorted(set(r["dataset"] for r in rows)):
        gg=sorted(set(gid(r) for r in rows if r["dataset"]==d))
        rng=np.random.default_rng(seed+sum(map(ord,d)));rng.shuffle(gg)
        n=max(1,int(round(len(gg)*fraction))) if len(gg)>2 else 1
        vg=set(gg[:n])
        for i,r in enumerate(rows):
            if r["dataset"]!=d:continue
            (va if gid(r) in vg else tr).append(i)
    return np.asarray(tr),np.asarray(va)
def fit_mlp(rows,alpha,seed,balanced):
    X=x(rows);Y=y(rows);tr,va=split_groups(rows,seed)
    scaler=StandardScaler().fit(X[tr])
    if balanced:
        br=balanced_resample([rows[i] for i in tr],seed)
        train_idx=tr[br]
    else:
        train_idx=tr
    model=MLPRegressor(hidden_layer_sizes=HIDDEN,activation="relu",solver="adam",
        alpha=alpha,batch_size=min(128,len(train_idx)),learning_rate_init=1e-3,
        max_iter=1,warm_start=True,shuffle=True,random_state=seed)
    best=None;best_rmse=float("inf");bad=0;best_epoch=1
    warnings.filterwarnings("ignore",category=ConvergenceWarning)
    for epoch in range(1,501):
        model.fit(scaler.transform(X[train_idx]),Y[train_idx])
        pv=model.predict(scaler.transform(X[va]))
        # equal total validation weight per corpus
        ww=corpus_weights([rows[i] for i in va])
        rmse=float(np.sqrt(np.average((pv-Y[va])**2,weights=ww)))
        if rmse<best_rmse-1e-5:
            best_rmse=rmse;best=copy.deepcopy(model);best_epoch=epoch;bad=0
        else:
            bad+=1
            if bad>=35:break
    # Refit on all allowed training rows for the selected epoch count.
    scaler=StandardScaler().fit(X)
    idx=balanced_resample(rows,seed) if balanced else np.arange(len(rows))
    final=MLPRegressor(hidden_layer_sizes=HIDDEN,activation="relu",solver="adam",
        alpha=alpha,batch_size=min(128,len(idx)),learning_rate_init=1e-3,
        max_iter=max(1,best_epoch),shuffle=True,random_state=seed)
    final.fit(scaler.transform(X[idx]),Y[idx])
    return {"scaler":scaler,"model":final,"epochs":best_epoch}
def pred_mlp(m,rows):
    return m["model"].predict(m["scaler"].transform(x(rows)))
def fit_ridge(rows,alpha=10.0,degree=1):
    X=x(rows);Y=y(rows);W=corpus_weights(rows)
    scaler=StandardScaler().fit(X,sample_weight=W)
    Z=scaler.transform(X);Z=poly2(Z) if degree==2 else Z
    m=Ridge(alpha=alpha).fit(Z,Y,sample_weight=W)
    return {"scaler":scaler,"model":m,"degree":degree}
def pred_ridge(m,rows):
    Z=m["scaler"].transform(x(rows));Z=poly2(Z) if m["degree"]==2 else Z
    return m["model"].predict(Z)
def by_dataset(rows,pred):
    Y=y(rows);D=ds(rows);return {d:metrics(Y[D==d],np.asarray(pred)[D==d]) for d in sorted(set(D))}
def grouped_mlp(rows,alpha,balanced,seeds=SEEDS):
    ff=folds(rows);p=np.zeros(len(rows))
    epochs=[]
    for f in range(FOLDS):
        tr=[r for i,r in enumerate(rows) if ff[i]!=f];vi=[i for i in range(len(rows)) if ff[i]==f];va=[rows[i] for i in vi]
        fold_preds=[]
        for seed in seeds:
            m=fit_mlp(tr,alpha,seed,balanced);epochs.append(m["epochs"]);fold_preds.append(pred_mlp(m,va))
        avg=np.mean(fold_preds,axis=0)
        for i,v in zip(vi,avg):p[i]=v
    bd=by_dataset(rows,p)
    return {"by_dataset":bd,"objective":objective(bd),"epochs":epochs}
def grouped_ridge(rows,alpha,degree):
    ff=folds(rows);p=np.zeros(len(rows))
    for f in range(FOLDS):
        tr=[r for i,r in enumerate(rows) if ff[i]!=f];vi=[i for i in range(len(rows)) if ff[i]==f];va=[rows[i] for i in vi]
        m=fit_ridge(tr,alpha,degree)
        for i,v in zip(vi,pred_ridge(m,va)):p[i]=v
    bd=by_dataset(rows,p);return {"by_dataset":bd,"objective":objective(bd)}
def select_mlp(rows,balanced):
    grid=[];best=None
    for a in ALPHAS:
        cv=grouped_mlp(rows,a,balanced,SEEDS);item={"alpha":a,**cv};grid.append(item)
        o=cv["objective"];key=(o["worst_correlation"],o["mean_correlation"],-o["worst_rmse_normalized"])
        if best is None or key>best[0]:best=(key,item)
    return best[1],grid
def engineering_report(predict,eng):
    raw=np.asarray(predict(eng),float);mos=1+4*np.clip(raw,0,1)
    rows=[{"family":r["family"],"level":float(r["level"]),"label":r["label"],
           "quality_raw":float(q),"mos":float(m)} for r,q,m in zip(eng,raw,mos)]
    failures=[];clean=next(x["mos"] for x in rows if x["family"]=="clean")
    if clean<4.4:failures.append(f"identity {clean:.3f}<4.4")
    delays=[x["mos"] for x in rows if x["family"]=="delay"]
    if delays and max(abs(v-clean) for v in delays)>0.20:
        failures.append("pure delay exceeds 0.20 MOS")
    fam={}
    for name in sorted(SCOPED_MONOTONIC):
        rr=sorted([x for x in rows if x["family"]==name],key=lambda z:z["level"])
        if len(rr)>1:
            n=sum(b["mos"]>a["mos"]+0.12 for a,b in zip(rr,rr[1:]))
            fam[name]={"violations_gt_0.12_mos":n}
            if n:failures.append(f"{name}:{n} reversals")
    return {"clean_mos":clean,"families":fam,"failures":failures}
def nested_loco(rows,eng,balanced):
    out={}
    for held in sorted(set(r["dataset"] for r in rows)):
        train=[r for r in rows if r["dataset"]!=held];test=[r for r in rows if r["dataset"]==held]
        selected,_=select_mlp(train,balanced)
        preds=[];engineering=[]
        for seed in SEEDS:
            m=fit_mlp(train,selected["alpha"],seed,balanced);preds.append(pred_mlp(m,test))
            engineering.append(engineering_report(lambda rr,m=m:pred_mlp(m,rr),eng))
        avg=np.mean(preds,axis=0)
        out[held]={"selected_alpha":selected["alpha"],"inner_objective":selected["objective"],
                   "test":metrics(y(test),avg),
                   "engineering_failures_by_seed":[x["failures"] for x in engineering]}
    vals=[min(v["test"]["pearson"],v["test"]["spearman"]) for v in out.values()]
    return {"by_held_corpus":out,"worst_held_corpus_correlation":float(min(vals)),
            "mean_held_corpus_correlation":float(np.mean(vals))}
def processing_transfer_mlp(rows,eng,balanced):
    out={}
    for d in sorted(set(r["dataset"] for r in rows)):
        fams=sorted(set(sid(r) for r in rows if r["dataset"]==d and sid(r)))
        if len(fams)<2:continue
        reports={}
        cases=[[u] for u in fams] if len(fams)<=20 else [[u for i,u in enumerate(fams) if i%5==f] for f in range(5)]
        for n,held in enumerate(cases):
            test=[r for r in rows if r["dataset"]==d and sid(r) in held]
            train=[r for r in rows if not (r["dataset"]==d and sid(r) in held)]
            if len(test)<4 or len(train)<20:continue
            sel,_=select_mlp(train,balanced)
            pp=[]
            for seed in SEEDS:
                m=fit_mlp(train,sel["alpha"],seed,balanced);pp.append(pred_mlp(m,test))
            reports[";".join(held) if len(held)<=3 else f"fold{n}"]=metrics(y(test),np.mean(pp,axis=0))
        if reports:
            vals=[min(v["pearson"],v["spearman"]) for v in reports.values()]
            out[d]={"reports":reports,"worst_correlation":float(min(vals))}
    return out
def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--dataset",action="append",required=True)
    ap.add_argument("--engineering",required=True)
    ap.add_argument("--out",required=True)
    a=ap.parse_args();rows=load(a.dataset);eng=read(a.engineering)

    # Exact-style historical ANN treatment: unbalanced, one seed, alpha .1.
    historical=grouped_mlp(rows,0.1,False,[20260926])
    ridge=grouped_ridge(rows,10.0,1)
    poly=grouped_ridge(rows,30.0,2)
    constrained_sel,constrained_grid=constrained.select_constrained(rows,eng,RICH_V3)
    constrained_loco=constrained.leave_corpus_out(rows,eng,RICH_V3)
    balanced_sel,balanced_grid=select_mlp(rows,True)

    # Full-data engineering report for each balanced seed.
    full_engineering=[]
    for seed in SEEDS:
        m=fit_mlp(rows,balanced_sel["alpha"],seed,True)
        full_engineering.append(engineering_report(lambda rr,m=m:pred_mlp(m,rr),eng))

    result={
      "experiment_id":"phase6b-summary-models-v1",
      "feature_schema":"openvq-rich-v3-2026-09-26-v1",
      "seeds":SEEDS,
      "dataset_counts":{d:sum(r["dataset"]==d for r in rows) for d in sorted(set(r["dataset"] for r in rows))},
      "arms":{
        "balanced_ridge":ridge,
        "balanced_unconstrained_poly2":poly,
        "balanced_constrained_linear_or_poly2":{"selected":constrained_sel,"grid":constrained_grid},
        "historical_unweighted_mlp_48_24":historical,
        "balanced_mlp_48_24":{"selected":balanced_sel,"grid":balanced_grid,
          "engineering_by_seed":full_engineering},
      },
      "nested_leave_corpus_out_constrained":constrained_loco,
      "nested_leave_corpus_out_balanced_mlp":nested_loco(rows,eng,True),
      "nested_processing_transfer_balanced_mlp":processing_transfer_mlp(rows,eng,True),
      "decision_rule":"advance a summary ANN only if unseen-domain ordering/error improves materially and model-specific engineering behavior remains acceptable; otherwise sequence modeling has a demonstrated problem to solve",
    }
    Path(a.out).write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps({
      "ridge":ridge["objective"],"poly2":poly["objective"],
      "constrained":constrained_sel["objective"],
      "historical_mlp":historical["objective"],
      "balanced_mlp":balanced_sel["objective"],
      "balanced_mlp_loco":result["nested_leave_corpus_out_balanced_mlp"],
      "engineering_failures":[x["failures"] for x in full_engineering],
    },indent=2))
if __name__=="__main__":main()
