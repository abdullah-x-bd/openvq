#!/usr/bin/env python3
"""Phase 5 native-only cross-domain trainer."""
import argparse,csv,json
from pathlib import Path
import numpy as np
from scipy.optimize import LinearConstraint,minimize

FEATURES=[
 "base","missing","added","coloration","noisiness","discontinuity","loudness",
 "clipping","bad_section","multi_resolution","temporal","modulation","asymmetry",
 "tilt","level","bad_interval","echo","choppiness","residual",
]
ALPHAS=[1.0,3.0,10.0,30.0,100.0,300.0,1000.0]
BASIS_MODES=["linear","poly2"]
FOLDS=5
MONOTONIC=[
 "dropout","dropout_count","noise","lowpass","clipping","attenuation",
 "clock_drift","time_scale","mixed",
]
MODEL_ID="phase5-native-crossdomain-2026-09-26-v1"

def read(p):
    with open(p,newline="",encoding="utf-8") as f:return list(csv.DictReader(f))
def clamp(x):return max(0.0,min(1.0,float(x)))
def vec(r):return np.asarray([float(r[x]) for x in FEATURES],float)
def basis(x,mode):
    if mode=="linear":return np.asarray(x,float)
    z=list(x)
    for i in range(len(x)):
        for j in range(i,len(x)):z.append(x[i]*x[j])
    return np.asarray(z,float)
def basis_names(mode):
    if mode=="linear":return list(FEATURES)
    z=list(FEATURES)
    for i,a in enumerate(FEATURES):
        for b in FEATURES[i:]:z.append(a+"*"+b)
    return z
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
    e=np.asarray(p)-np.asarray(y)
    return {"n":int(len(y)),"pearson":corr(y,p),"spearman":corr(ranks(y),ranks(p)),
            "rmse":float(np.sqrt(np.mean(e*e))),"bias":float(np.mean(e))}
def add_rows(rows,path,dataset,target_kind,group_kind):
    for r in read(path):
        if target_kind=="mushra":
            target=float(r["human_mushra"])/100.0
        else:
            target=(float(r["human_mos"])-1.0)/4.0
        if group_kind=="speaker":
            group=r["speaker"]
        elif group_kind=="source":
            group=r.get("group_id","") or r["filename"].split("_TMHINT_",1)[-1]
        elif group_kind=="condition":
            group=r.get("condition_id","") or r.get("filename","")
        else:
            group=r.get("filename","")
        rows.append({"dataset":dataset,"group":dataset+":"+group,
                     "target":target,"native":vec(r)})
def domain_weights(ds):
    w=np.zeros(len(ds))
    for d in sorted(set(ds)):
        m=ds==d;w[m]=1.0/max(1,int(m.sum()))
    return w/w.sum()*len(w)
def eng_native(obj):
    d=obj["dimensions"];q=obj["advanced"]
    return np.asarray([
      clamp((5-float(obj["base_mos"]))/4),clamp(obj["missing_disturbance"]),
      clamp(obj["added_disturbance"]),clamp((5-float(d["coloration"]))/4),
      clamp((5-float(d["noisiness"]))/4),clamp((5-float(d["discontinuity"]))/4),
      clamp((5-float(d["loudness"]))/4),clamp(float(obj["clipping_ratio"])*40),
      clamp(obj["bad_section_fraction"]),clamp(1-float(q["multi_resolution_similarity"])),
      clamp(1-float(q["temporal_envelope_similarity"])),clamp(1-float(q["modulation_similarity"])),
      clamp(q["asymmetric_disturbance"]),clamp(q["spectral_tilt_error"]),
      clamp(float(q["active_level_delta_db"])/18),clamp(q["bad_interval_severity"]),
      clamp(q.get("echo_score",0)),clamp(q.get("choppiness_score",0)),
      clamp(q.get("residual_intrusion",0))
    ],float)
def eng_rows(path):
    p=json.loads(Path(path).read_text())
    return [{"family":c["family"],"level":float(c["level"]),"label":c["label"],
             "native":eng_native(c["result"])} for c in p["cases"]]
def folds(rows):
    out={}
    for d in sorted(set(r["dataset"] for r in rows)):
        gs=sorted(set(r["group"] for r in rows if r["dataset"]==d))
        for i,g in enumerate(gs):out[g]=i%FOLDS
    return np.asarray([out[r["group"]] for r in rows])
def constraints(engineering,mode,mean,scale):
    x=np.vstack([basis(r["native"],mode) for r in engineering])
    z=(x-mean)/scale;a=np.column_stack([np.ones(len(z)),z])
    rr=[];lo=[];hi=[]
    ident=next(i for i,r in enumerate(engineering) if r["family"]=="clean")
    rr.append(a[ident]);lo.append(.875);hi.append(np.inf)
    for i,r in enumerate(engineering):
        if r["family"]=="sample_rate_identity":
            rr.append(a[i]);lo.append(.80);hi.append(np.inf)
        if r["family"]=="delay":
            rr.append(a[i]-a[ident]);lo.append(-.1125);hi.append(.1125)
    for fam in MONOTONIC:
        inds=sorted([i for i,r in enumerate(engineering) if r["family"]==fam],
                    key=lambda i:engineering[i]["level"])
        for u,v in zip(inds,inds[1:]):
            rr.append(a[v]-a[u]);lo.append(-np.inf);hi.append(0.0)
    return np.asarray(rr),np.asarray(lo),np.asarray(hi)
def fit(X,y,ds,engineering,mode,alpha):
    w=domain_weights(ds);mu=np.average(X,axis=0,weights=w)
    sd=np.sqrt(np.average((X-mu)**2,axis=0,weights=w));sd[sd<1e-8]=1
    z=(X-mu)/sd;a=np.column_stack([np.ones(len(z)),z])
    sw=np.sqrt(w);aw=a*sw[:,None];yw=y*sw
    reg=np.eye(a.shape[1]);reg[0,0]=0
    H=aw.T@aw+alpha*reg;g=aw.T@yw
    initial=np.linalg.solve(H,g)
    C,lo,hi=constraints(engineering,mode,mu,sd)
    fun=lambda th:0.5*th@H@th-g@th
    jac=lambda th:H@th-g
    res=minimize(fun,initial,jac=jac,constraints=[LinearConstraint(C,lo,hi)],
                 method="SLSQP",options={"maxiter":1500,"ftol":1e-9,"disp":False})
    if not res.success:raise RuntimeError(res.message)
    return mu,sd,res.x,int(res.nit)
def predict(model,X):
    mu,sd,th,_=model
    return np.clip(th[0]+((X-mu)/sd)@th[1:],0,1)
def cv(rows,engineering,mode,alpha):
    X=np.vstack([basis(r["native"],mode) for r in rows]);y=np.asarray([r["target"] for r in rows])
    ds=np.asarray([r["dataset"] for r in rows]);ff=folds(rows);p=np.zeros(len(rows))
    its=[]
    for f in range(FOLDS):
        tr=ff!=f;va=ff==f
        m=fit(X[tr],y[tr],ds[tr],engineering,mode,alpha);its.append(m[3]);p[va]=predict(m,X[va])
    by={}
    vals=[]
    for d in sorted(set(ds)):
        m=ds==d;by[d]=metrics(y[m],p[m])
        vals += [by[d]["pearson"],by[d]["spearman"]]
    return by,{"worst_correlation":float(min(vals)),"mean_correlation":float(np.mean(vals)),
               "worst_rmse":float(max(v["rmse"] for v in by.values()))},its
def emit(path,model,mode):
    mu,sd,th,_=model
    def arr(n,v):
        return f"inline constexpr std::array<double,{len(v)}> {n}={{{{"+",".join(f"{float(x):.17g}" for x in v)+"}}};\n"
    s="#pragma once\n#include <array>\nnamespace openvq::phase5_model {\n"
    s+=f'inline constexpr const char* kModelId="{MODEL_ID}";\n'
    s+=f'inline constexpr const char* kBasis="{mode}";\n'
    s+=f"inline constexpr double kIntercept={th[0]:.17g};\n"
    s+=arr("kMean",mu)+arr("kScale",sd)+arr("kWeights",th[1:])+"}\n"
    Path(path).write_text(s)
def main():
    ap=argparse.ArgumentParser()
    for n in ["tcd_train","tcd_dev","tcd_test","p501","openace","test_for","tmhint","engineering"]:
        ap.add_argument("--"+n.replace("_","-"),dest=n,required=True)
    ap.add_argument("--out",required=True);ap.add_argument("--cpp-out",required=True)
    a=ap.parse_args();rows=[]
    for p in [a.tcd_train,a.tcd_dev,a.tcd_test]:add_rows(rows,p,"tcd","mos","condition")
    add_rows(rows,a.p501,"nisqa_p501","mos","condition")
    add_rows(rows,a.openace,"openace","mushra","speaker")
    add_rows(rows,a.test_for,"nisqa_test_for","mos","condition")
    add_rows(rows,a.tmhint,"tmhint_test","mos","source")
    eng=eng_rows(a.engineering)
    grid=[];best=None
    for mode in BASIS_MODES:
      for alpha in ALPHAS:
        by,obj,its=cv(rows,eng,mode,alpha)
        item={"basis":mode,"alpha":alpha,"by_dataset":by,"objective":obj,"iterations":its}
        grid.append(item)
        key=(obj["worst_correlation"],obj["mean_correlation"],-obj["worst_rmse"],
             1 if mode=="linear" else 0,-alpha)
        if best is None or key>best[0]:best=(key,item)
    sel=best[1]
    X=np.vstack([basis(r["native"],sel["basis"]) for r in rows]);y=np.asarray([r["target"] for r in rows])
    ds=np.asarray([r["dataset"] for r in rows])
    model=fit(X,y,ds,eng,sel["basis"],sel["alpha"])
    result={"model_id":MODEL_ID,"status":"development candidate; not externally validated",
      "dataset_counts":{d:int(sum(x==d for x in ds)) for d in sorted(set(ds))},
      "feature_order":FEATURES,"basis_order":basis_names(sel["basis"]),
      "selection_rule":"maximize weakest Pearson/Spearman across five development domains under fixed engineering constraints",
      "selected":sel,"grid":grid,"solver_iterations_full_fit":model[3],
      "warning":"NISQA TEST_FOR and TMHINT-QI test are development data after Phase 4 unblinding. They cannot validate Phase 5."}
    Path(a.out).write_text(json.dumps(result,indent=2)+"\n")
    emit(a.cpp_out,model,sel["basis"])
    print(json.dumps({"model_id":MODEL_ID,"dataset_counts":result["dataset_counts"],"selected":sel},indent=2))
if __name__=="__main__":main()
