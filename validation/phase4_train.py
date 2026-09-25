#!/usr/bin/env python3
"""Train a dataset-balanced native-first Phase 4 development candidate."""
import argparse,csv,json,math
from pathlib import Path
import numpy as np

NATIVE=[
 "base","missing","added","coloration","noisiness","discontinuity","loudness",
 "clipping","bad_section","multi_resolution","temporal","modulation","asymmetry",
 "tilt","level","bad_interval","echo","choppiness","residual"
]
ALPHAS=[1.0,3.0,10.0,30.0,100.0,300.0]
BLENDS=[0.0,0.1,0.2,0.3,0.4]
FOLDS=5

def read(path):
    with open(path,newline="",encoding="utf-8") as f:return list(csv.DictReader(f))

def ranks(x):
    order=np.argsort(x,kind="mergesort"); out=np.empty(len(x),float); i=0
    while i<len(x):
        j=i+1
        while j<len(x) and x[order[j]]==x[order[i]]:j+=1
        out[order[i:j]]=(i+j-1)/2+1;i=j
    return out

def corr(a,b):
    if len(a)<2 or np.std(a)<1e-12 or np.std(b)<1e-12:return 0.0
    return float(np.corrcoef(a,b)[0,1])

def metrics(y,p):
    return {
      "n":int(len(y)),
      "pearson":corr(y,p),
      "spearman":corr(ranks(y),ranks(p)),
      "rmse_normalized":float(np.sqrt(np.mean((y-p)**2))),
      "bias_normalized":float(np.mean(p-y)),
    }

def basis(x):
    # Linear native features plus all degree-2 products, including squares.
    out=list(x)
    for i in range(len(x)):
        for j in range(i,len(x)):
            out.append(x[i]*x[j])
    return np.asarray(out,float)

def basis_names():
    out=list(NATIVE)
    for i,a in enumerate(NATIVE):
        for b in NATIVE[i:]:out.append(a+"*"+b)
    return out

def dataset_rows(tcd_paths,nisqa_path,openace_path):
    rows=[]
    for p in tcd_paths:
        for r in read(p):
            rows.append({
              "dataset":"tcd",
              "group":"tcd:"+r.get("family","")+":"+r["condition_id"],
              "target":(float(r["human_mos"])-1.0)/4.0,
              "native":[float(r[x]) for x in NATIVE],
              "speech_q":1.0-float(r["visqol_speech"]),
              "audio_q":1.0-float(r["visqol_audio"]),
            })
    for r in read(nisqa_path):
        rows.append({
          "dataset":"nisqa",
          "group":"nisqa:"+r["condition_id"],
          "target":(float(r["human_mos"])-1.0)/4.0,
          "native":[float(r[x]) for x in NATIVE],
          "speech_q":1.0-float(r["visqol_speech"]),
          "audio_q":1.0-float(r["visqol_audio"]),
        })
    for r in read(openace_path):
        rows.append({
          "dataset":"openace",
          # Hold out whole speakers so emotion/codec clips from one voice do
          # not leak into both train and validation folds.
          "group":"openace:"+r["speaker"],
          "target":float(r["human_mushra"])/100.0,
          "native":[float(r[x]) for x in NATIVE],
          "speech_q":1.0-float(r["visqol_speech"]),
          "audio_q":1.0-float(r["visqol_audio"]),
        })
    return rows

def assign_folds(rows):
    group_fold={}
    for ds in sorted(set(r["dataset"] for r in rows)):
        groups=sorted(set(r["group"] for r in rows if r["dataset"]==ds))
        for i,g in enumerate(groups):group_fold[g]=i%FOLDS
    return np.asarray([group_fold[r["group"]] for r in rows],int)

def fit(X,y,datasets,alpha):
    # Each development domain contributes equal total weight.
    w=np.zeros(len(y),float)
    for ds in sorted(set(datasets)):
        m=np.asarray([x==ds for x in datasets])
        w[m]=1.0/max(1,int(m.sum()))
    w=w/w.sum()*len(w)
    mu=np.average(X,axis=0,weights=w)
    sd=np.sqrt(np.average((X-mu)**2,axis=0,weights=w))
    sd[sd<1e-8]=1.0
    Z=(X-mu)/sd
    A=np.column_stack([np.ones(len(Z)),Z])
    sw=np.sqrt(w)
    Aw=A*sw[:,None]; yw=y*sw
    reg=np.sqrt(alpha)*np.eye(A.shape[1]);reg[0,0]=0
    coef=np.linalg.solve(Aw.T@Aw+reg.T@reg,Aw.T@yw)
    return mu,sd,coef

def predict_native(model,X):
    mu,sd,coef=model
    Z=(X-mu)/sd
    return np.clip(coef[0]+Z@coef[1:],0.0,1.0)

LEARNED_NATIVE_BLEND=0.20

def anchored_native(learned, rows):
    anchor=np.asarray([1.0-float(r["native"][0]) for r in rows],float)
    return np.clip((1.0-LEARNED_NATIVE_BLEND)*anchor + LEARNED_NATIVE_BLEND*learned,0.0,1.0)

def robust_hybrid(native,speech,audio,blend):
    consensus=np.median(np.vstack([native,speech,audio]),axis=0)
    return np.clip((1.0-blend)*native+blend*consensus,0.0,1.0)

def cv(rows,alpha,blend):
    X=np.vstack([basis(r["native"]) for r in rows])
    y=np.asarray([r["target"] for r in rows],float)
    ds=np.asarray([r["dataset"] for r in rows])
    speech=np.asarray([r["speech_q"] for r in rows])
    audio=np.asarray([r["audio_q"] for r in rows])
    folds=assign_folds(rows)
    pn=np.zeros(len(rows),float)
    for f in range(FOLDS):
        tr=folds!=f;va=folds==f
        model=fit(X[tr],y[tr],ds[tr],alpha)
        pn[va]=predict_native(model,X[va])
    pn=anchored_native(pn, rows)
    ph=robust_hybrid(pn,speech,audio,blend)
    by={}
    for name in sorted(set(ds)):
        m=ds==name
        by[name]={"native":metrics(y[m],pn[m]),"hybrid":metrics(y[m],ph[m])}
    scores=[]
    for name in by:
        scores.extend([by[name]["hybrid"]["pearson"],by[name]["hybrid"]["spearman"]])
    objective={"worst_correlation":float(min(scores)),"mean_correlation":float(np.mean(scores))}
    return by,objective,pn,ph

def emit_cpp(path,model):
    mu,sd,coef=model["mean"],model["scale"],model["coef"]
    def arr(name,v):
        vals=",\n    ".join(f"{float(x):.17g}" for x in v)
        return f"inline constexpr std::array<double, {len(v)}> {name} = {{{{\n    {vals}\n}}}};\n"
    s="#pragma once\n#include <array>\n\nnamespace openvq::phase4_model {\n"
    s+=f'inline constexpr const char* kModelId = "{model["model_id"]}";\n'
    s+=f"inline constexpr double kExpertBlend = {model['expert_blend']:.17g};\n"
    s+=f"inline constexpr double kLearnedNativeBlend = {model['learned_native_blend']:.17g};\n"
    s+=f"inline constexpr double kIntercept = {coef[0]:.17g};\n"
    s+=arr("kMean",mu)+arr("kScale",sd)+arr("kWeights",coef[1:])
    s+="}\n"
    Path(path).write_text(s,encoding="utf-8")

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--tcd-train",required=True);ap.add_argument("--tcd-dev",required=True);ap.add_argument("--tcd-test",required=True)
    ap.add_argument("--nisqa",required=True);ap.add_argument("--openace",required=True)
    ap.add_argument("--out",required=True);ap.add_argument("--cpp-out",required=True)
    args=ap.parse_args()
    rows=dataset_rows([args.tcd_train,args.tcd_dev,args.tcd_test],args.nisqa,args.openace)
    grid=[]
    best=None
    for alpha in ALPHAS:
        for blend in BLENDS:
            by,obj,_,_=cv(rows,alpha,blend)
            item={"alpha":alpha,"expert_blend":blend,"objective":obj,"by_dataset":by}
            grid.append(item)
            key=(obj["worst_correlation"],obj["mean_correlation"],-blend,-alpha)
            if best is None or key>best[0]:best=(key,item)
    selected=best[1]
    X=np.vstack([basis(r["native"]) for r in rows])
    y=np.asarray([r["target"] for r in rows],float)
    ds=np.asarray([r["dataset"] for r in rows])
    mu,sd,coef=fit(X,y,ds,selected["alpha"])
    model_id="phase4-native-poly2-balanced-2026-09-25-v1"
    result={
      "model_id":model_id,
      "status":"development candidate, not external validation",
      "feature_order":NATIVE,
      "basis_order":basis_names(),
      "target_mapping":{"tcd_nisqa":"(MOS-1)/4","openace":"MUSHRA/100"},
      "dataset_counts":{d:sum(r["dataset"]==d for r in rows) for d in sorted(set(ds))},
      "selection_rule":"80 percent engineered native anchor plus 20 percent learned quadratic correction; then maximize weakest Pearson/Spearman across development domains with optional experts capped at 40 percent via median consensus",
      "selected":selected,
      "grid":grid,
      "native_model":{
        "alpha":selected["alpha"],
        "mean":mu.tolist(),"scale":sd.tolist(),"coef":coef.tolist(),
      },
      "learned_native_blend":LEARNED_NATIVE_BLEND,
      "expert_blend":selected["expert_blend"],
      "warning":"TCD, NISQA P501 and OpenACE are all development data for this candidate. A new untouched subjective corpus is required before any generalization or POLQA-parity claim."
    }
    Path(args.out).write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    emit_cpp(args.cpp_out,{
      "model_id":model_id,"expert_blend":selected["expert_blend"],
      "learned_native_blend":LEARNED_NATIVE_BLEND,
      "mean":mu.tolist(),"scale":sd.tolist(),"coef":coef.tolist()
    })
    print(json.dumps({
      "model_id":model_id,
      "dataset_counts":result["dataset_counts"],
      "selected":selected,
    },indent=2))

if __name__=="__main__":main()
