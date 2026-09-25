#!/usr/bin/env python3
"""Fit Phase-4 v2 on three observed subjective domains with grouped CV.

Data roles:
- TCD-VoIP: development
- NISQA TEST P501: development
- EARS-EMO-OpenACE: development after the frozen Phase-3 external failure

No Phase-4 final holdout is read by this script.
"""
import argparse,csv,json,math
from pathlib import Path
import numpy as np

NATIVE=[
    "base","missing","added","coloration","noisiness","discontinuity","loudness",
    "clipping","bad_section","multi_resolution","temporal","modulation",
    "asymmetry","tilt","level","bad_interval","echo","choppiness","residual",
]
SELECTED_NATIVE=[
    "base","missing","added","coloration","noisiness","discontinuity","loudness",
    "bad_section","tilt","level","echo","choppiness","residual",
]
ALPHAS=[0.1,0.3,1.0,3.0,10.0,30.0,100.0]
FOLDS=5

def read(path):
    with open(path,newline="",encoding="utf-8") as f:return list(csv.DictReader(f))

def ranks(x):
    order=sorted(range(len(x)),key=lambda i:x[i]);out=[0.0]*len(x);i=0
    while i<len(order):
        j=i+1
        while j<len(order) and x[order[j]]==x[order[i]]:j+=1
        r=(i+j-1)/2+1
        for k in range(i,j):out[order[k]]=r
        i=j
    return out

def corr(a,b):
    a=np.asarray(a,float);b=np.asarray(b,float)
    aa=a-a.mean();bb=b-b.mean()
    den=math.sqrt(float(aa@aa)*float(bb@bb))
    return float(aa@bb/den) if den else 0.0

def metrics(y,p):
    y=np.asarray(y,float);p=np.asarray(p,float);e=p-y
    return {
      "n":len(y),"pearson":corr(y,p),"spearman":corr(ranks(list(y)),ranks(list(p))),
      "rmse_q":float(np.sqrt(np.mean(e*e))),
      "mae_q":float(np.mean(np.abs(e))),
      "bias_q":float(np.mean(e)),
    }

def normalized_row(row,dataset):
    if dataset=="openace":
        target=float(row["human_mushra"])/100.0
        group=f'{row["speaker"]}|{row["emotion"]}'
    else:
        target=(float(row["human_mos"])-1.0)/4.0
        if dataset=="tcd":
            group=f'{row.get("family","")}|{row.get("condition_id","")}'
        else:
            group=row.get("condition_id","")
    vals={k:float(row[k]) for k in NATIVE}
    vals["speech_q"]=1.0-float(row["visqol_speech"])
    vals["audio_q"]=1.0-float(row["visqol_audio"])
    vals["expert_mean_q"]=(vals["speech_q"]+vals["audio_q"])/2.0
    vals["expert_min_q"]=min(vals["speech_q"],vals["audio_q"])
    vals["expert_max_q"]=max(vals["speech_q"],vals["audio_q"])
    vals["expert_absdiff_q"]=abs(vals["speech_q"]-vals["audio_q"])
    return vals,target,group

def feature_names():
    names=list(NATIVE)
    names += ["speech_q","audio_q","expert_mean_q","expert_min_q","expert_max_q","expert_absdiff_q"]
    names += [f"{c}^2" for c in NATIVE]
    names += [f"{e}*{c}" for e in ("speech_q","audio_q","expert_absdiff_q") for c in SELECTED_NATIVE]
    return names

FEATURE_NAMES=feature_names()

def vector(v):
    x=[v[c] for c in NATIVE]
    x += [v[c] for c in ("speech_q","audio_q","expert_mean_q","expert_min_q","expert_max_q","expert_absdiff_q")]
    x += [v[c]*v[c] for c in NATIVE]
    x += [v[e]*v[c] for e in ("speech_q","audio_q","expert_absdiff_q") for c in SELECTED_NATIVE]
    return x

def dataset(rows,name):
    xs=[];ys=[];groups=[]
    for r in rows:
        v,y,g=normalized_row(r,name)
        xs.append(vector(v));ys.append(y);groups.append(g)
    return {"x":np.asarray(xs,float),"y":np.asarray(ys,float),"groups":groups}

def corpus_weights(data,mask=None):
    n=len(data["y"]) if mask is None else int(np.asarray(mask,bool).sum())
    return np.repeat(1.0/max(1,n),n)

def fit_ridge(parts,alpha):
    xs=[];ys=[];weights=[]
    for x,y in parts:
        xs.append(x);ys.append(y);weights.append(np.repeat(1.0/len(y),len(y)))
    x=np.vstack(xs);y=np.concatenate(ys);w=np.concatenate(weights);w/=w.mean()
    mean=x.mean(axis=0);scale=x.std(axis=0)
    scale=np.where(scale<1e-12,1.0,scale)
    z=(x-mean)/scale
    a=np.column_stack([np.ones(len(z)),z])
    reg=np.eye(a.shape[1]);reg[0,0]=0.0
    lhs=a.T@(w[:,None]*a)+alpha*reg
    rhs=a.T@(w*y)
    beta=np.linalg.solve(lhs,rhs)
    return {"mean":mean,"scale":scale,"intercept":float(beta[0]),"coef":beta[1:]}

def predict(model,x):
    z=(x-model["mean"])/model["scale"]
    return np.clip(model["intercept"]+z@model["coef"],0.0,1.0)

def fold_ids(groups):
    uniq=sorted(set(groups))
    assignment={g:i%FOLDS for i,g in enumerate(uniq)}
    return np.asarray([assignment[g] for g in groups],int)

def cv(all_data,alpha):
    preds={k:np.full(len(v["y"]),np.nan) for k,v in all_data.items()}
    folds={k:fold_ids(v["groups"]) for k,v in all_data.items()}
    for f in range(FOLDS):
        parts=[]
        val=[]
        for name,d in all_data.items():
            tr=folds[name]!=f;va=folds[name]==f
            parts.append((d["x"][tr],d["y"][tr]))
            val.append((name,np.where(va)[0],d["x"][va]))
        model=fit_ridge(parts,alpha)
        for name,idx,x in val:preds[name][idx]=predict(model,x)
    reports={k:metrics(v["y"],preds[k]) for k,v in all_data.items()}
    objective=float(np.mean([reports[k]["rmse_q"] for k in sorted(reports)]))
    return objective,reports

def serial_model(m):
    return {
      "feature_mean":[float(x) for x in m["mean"]],
      "feature_scale":[float(x) for x in m["scale"]],
      "intercept":float(m["intercept"]),
      "coefficients":[float(x) for x in m["coef"]],
    }

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--nisqa",required=True)
    ap.add_argument("--tcd",required=True)
    ap.add_argument("--openace",required=True)
    ap.add_argument("--out",required=True)
    a=ap.parse_args()

    data={
      "nisqa_p501":dataset(read(a.nisqa),"nisqa"),
      "tcd_test":dataset(read(a.tcd),"tcd"),
      "openace":dataset(read(a.openace),"openace"),
    }
    trials=[]
    for alpha in ALPHAS:
        objective,reports=cv(data,alpha)
        trials.append({"alpha":alpha,"objective":objective,"metrics":reports})
    selected=min(trials,key=lambda x:(x["objective"],x["alpha"]))
    full=fit_ridge([(v["x"],v["y"]) for v in data.values()],selected["alpha"])
    dev={k:metrics(v["y"],predict(full,v["x"])) for k,v in data.items()}

    out={
      "model_id":"phase4-v2-multidomain-ridge-2026-09-25",
      "status":"development candidate; freeze only after the declared development gate is checked",
      "output":"normalized subjective quality q in [0,1]; reported MOS = 1 + 4*q",
      "data_roles":{
        "TCD-VoIP":"development",
        "NISQA TEST P501":"development",
        "EARS-EMO-OpenACE":"development after Phase-3 external failure",
        "NISQA TEST FOR":"untouched Phase-4 holdout",
        "NISQA TEST NSC":"untouched Phase-4 holdout"
      },
      "target_mapping":{
        "TCD-VoIP":"q=(MOS-1)/4",
        "NISQA TEST P501":"q=(MOS-1)/4",
        "EARS-EMO-OpenACE":"q=MUSHRA/100"
      },
      "feature_names":FEATURE_NAMES,
      "native_features":NATIVE,
      "selected_interaction_native_features":SELECTED_NATIVE,
      "ridge_candidates":ALPHAS,
      "cv_folds":FOLDS,
      "cv_grouping":{
        "NISQA TEST P501":"condition_id",
        "TCD-VoIP":"family + condition_id",
        "EARS-EMO-OpenACE":"speaker + emotion"
      },
      "selection_objective":"minimum equal-corpus mean grouped-CV RMSE on normalized subjective quality",
      "selected_alpha":selected["alpha"],
      "selected_cv_objective":selected["objective"],
      "selected_cv_metrics":selected["metrics"],
      "development_fit_metrics":dev,
      "model":serial_model(full),
      "development_gate":{
        "requirements":[
          "grouped-CV Pearson >= 0.70 on every development corpus",
          "equal-corpus mean grouped-CV RMSE_q <= 0.16"
        ],
        "passed":bool(
          selected["objective"]<=0.16 and
          all(v["pearson"]>=0.70 for v in selected["metrics"].values())
        )
      },
      "provenance":{
        "phase3_artifact_run":36089410545,
        "phase3_artifact_id":10847922836,
        "openace_artifact_run":36104456276,
        "openace_feature_artifact_id":10850816520,
        "final_holdouts_read":False
      }
    }
    Path(a.out).parent.mkdir(parents=True,exist_ok=True)
    Path(a.out).write_text(json.dumps(out,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(out,indent=2))

if __name__=="__main__":main()
