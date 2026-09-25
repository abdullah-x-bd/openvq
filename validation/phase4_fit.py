#!/usr/bin/env python3
"""Fit the provisional Phase-4 robust fusion without using OpenACE labels."""
import argparse,csv,json,math
from pathlib import Path
import numpy as np
from scipy.optimize import lsq_linear

NATIVE=[
    "base","missing","added","coloration","noisiness","discontinuity","loudness",
    "clipping","bad_section","multi_resolution","temporal","modulation",
    "asymmetry","tilt","level","bad_interval","echo","choppiness","residual",
]
RIDGE=0.03
EXPERT_DELTA_CAP=0.60
ALPHAS=[i/20 for i in range(21)]

def read(path):
    with open(path,newline="",encoding="utf-8") as f:return list(csv.DictReader(f))

def arr(rows,col):return np.asarray([float(r[col]) for r in rows],dtype=float)

def fit_native(datasets):
    xs=[];ys=[];ws=[]
    for rows in datasets:
        x=np.asarray([[float(r[c]) for c in NATIVE] for r in rows])
        y=5.0-arr(rows,"human_mos")
        xs.append(x);ys.append(y)
        # Equal total weight per development corpus.
        ws.extend([1.0/len(rows)]*len(rows))
    x=np.vstack(xs);y=np.concatenate(ys)
    w=np.asarray(ws);w/=w.mean()
    a=np.column_stack([np.ones(len(x)),x])
    aw=a*np.sqrt(w)[:,None];yw=y*np.sqrt(w)
    reg=np.sqrt(RIDGE)*np.eye(a.shape[1]);reg[0,0]=0.0
    res=lsq_linear(np.vstack([aw,reg]),np.concatenate([yw,np.zeros(a.shape[1])]),
                   bounds=(0.0,np.inf))
    return res.x

def metrics(y,p):
    y=np.asarray(y);p=np.asarray(p);e=p-y
    def ranks(v):
        order=np.argsort(v,kind="mergesort");out=np.empty(len(v),float);i=0
        while i<len(v):
            j=i+1
            while j<len(v) and v[order[j]]==v[order[i]]:j+=1
            out[order[i:j]]=(i+j-1)/2+1;i=j
        return out
    def corr(a,b):
        aa=a-a.mean();bb=b-b.mean()
        den=math.sqrt(float(aa@aa)*float(bb@bb))
        return float(aa@bb/den) if den else 0.0
    return {
        "n":len(y),"pearson":corr(y,p),"spearman":corr(ranks(y),ranks(p)),
        "rmse":float(np.sqrt(np.mean(e*e))),"mae":float(np.mean(np.abs(e))),
        "bias":float(np.mean(e)),
    }

def predict(rows,coef,alpha):
    x=np.asarray([[float(r[c]) for c in NATIVE] for r in rows])
    native=np.clip(5.0-coef[0]-x@coef[1:],1.0,5.0)
    speech=5.0-4.0*arr(rows,"visqol_speech")
    audio=5.0-4.0*arr(rows,"visqol_audio")
    median=np.median(np.vstack([native,speech,audio]),axis=0)
    delta=np.clip(median-native,-EXPERT_DELTA_CAP,EXPERT_DELTA_CAP)
    final=np.clip(native+alpha*delta,1.0,5.0)
    return native,speech,audio,median,final

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--nisqa",required=True)
    ap.add_argument("--tcd",required=True)
    ap.add_argument("--out",required=True)
    a=ap.parse_args()
    nisqa=read(a.nisqa);tcd=read(a.tcd)
    coef=fit_native([nisqa,tcd])

    trials=[]
    for alpha in ALPHAS:
        reports={}
        rmses=[]
        for name,rows in [("nisqa_p501",nisqa),("tcd_test",tcd)]:
            final=predict(rows,coef,alpha)[-1]
            m=metrics(arr(rows,"human_mos"),final)
            reports[name]=m;rmses.append(m["rmse"])
        trials.append((sum(rmses)/len(rmses),alpha,reports))
    trials.sort(key=lambda x:(x[0],x[1]))
    objective,alpha,reports=trials[0]

    model={
      "model_id":"phase4-provisional-robust-fusion-v1",
      "status":"development candidate; not a frozen final model",
      "training_rule":"Fit only on previously observed TCD test and NISQA TEST P501 Phase-3 feature tables. OpenACE labels are not used for fitting.",
      "native_features":NATIVE,
      "native_ridge":RIDGE,
      "native_bias":float(coef[0]),
      "native_weights":{k:float(v) for k,v in zip(NATIVE,coef[1:])},
      "expert_rule":"median(native_anchor, ViSQOL speech MOS, ViSQOL audio MOS), then bounded movement from native anchor",
      "expert_delta_cap_mos":EXPERT_DELTA_CAP,
      "expert_alpha":alpha,
      "selection_objective":"minimum equal-corpus mean utterance RMSE on the two Phase-4 development corpora",
      "selection_objective_value":objective,
      "development_metrics":reports,
      "provenance":{
        "phase3_artifact_run":36089410545,
        "phase3_artifact_id":10847922836,
        "openace_not_used_for_fit":True
      }
    }
    Path(a.out).parent.mkdir(parents=True,exist_ok=True)
    Path(a.out).write_text(json.dumps(model,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(model,indent=2))

if __name__=="__main__":main()
