#!/usr/bin/env python3
"""Forensic analysis of the Phase 3 OpenACE failure."""
import argparse
import csv
import json
import math
from collections import defaultdict

import numpy as np

NATIVE = [
    "base","missing","added","coloration","noisiness","discontinuity",
    "loudness","clipping","bad_section","multi_resolution","temporal",
    "modulation","asymmetry","tilt","level","bad_interval","echo",
    "choppiness","residual",
]
EXPERTS = ["visqol_speech","visqol_audio"]

BIAS = 0.5326278543380228
TERMS = [
    (0,.45,.02480238598130599),(0,.6,.017059258090025623),(0,.75,.017059258090025623),
    (1,.3,.035387642252867176),(1,.45,.01763777437821818),(1,.6,.017059258090025623),(1,.75,.017059258090025623),
    (2,.75,.017083379508742114),(5,.6,.013856938059651935),(5,.75,.017059258090025623),
    (6,.6,.014189521111631355),(6,.75,.13274592731218304),
    (7,0,.017059258090025623),(7,.15,.017059258090025623),(7,.3,.017059258090025623),(7,.45,.017059258090025623),(7,.6,.017059258090025623),(7,.75,.017059258090025623),
    (8,.15,.005492562271632836),(8,.3,.013767355025200547),(8,.45,.017059258090025623),(8,.6,.017059258090025623),(8,.75,.017059258090025623),
    (9,.45,.017059258090025623),(9,.6,.017059258090025623),(9,.75,.017059258090025623),
    (10,.45,.017059258090025623),(10,.6,.017059258090025623),(10,.75,.017059258090025623),
    (11,.3,.017059258090025623),(11,.45,.017059258090025623),(11,.6,.017059258090025623),(11,.75,.017059258090025623),
    (12,.75,.013145693128172993),(13,.45,.017059258090025623),(13,.6,.017059258090025623),(13,.75,.017059258090025623),
    (15,.6,.014663449735516018),(15,.75,.017059258090025623),
    (16,0,1.3777553446812958),
    (17,.3,.1650553953987244),(17,.45,.092858293549331),(17,.6,.027310951711285853),(17,.75,.017059258090025623),
    (18,0,.21996814385977154),
    (19,0,1.519440424439323),(19,.15,1.265923728647842),
    (20,0,.3636430453066157),(20,.6,.022247608993292367),(20,.75,.017059258090025623),
    (23,0,.0597106958891576),(23,.15,.017059258090025623),(23,.3,.017059258090025623),(23,.45,.017059258090025623),(23,.6,.017059258090025623),(23,.75,.017059258090025623),
    (24,.15,.09401772247293266),(24,.3,.018471737439116814),(24,.45,.017059258090025623),(24,.6,.017059258090025623),(24,.75,.017059258090025623),
    (26,0,.017059258090025623),(26,.15,.017059258090025623),(26,.3,.017059258090025623),(26,.45,.017059258090025623),(26,.6,.017059258090025623),(26,.75,.017059258090025623),
    (27,.45,.017059258090025623),(27,.6,.017059258090025623),(27,.75,.017059258090025623),
]

def rank(x):
    order=np.argsort(x,kind="mergesort")
    out=np.empty(len(x),float)
    i=0
    while i<len(x):
        j=i+1
        while j<len(x) and x[order[j]]==x[order[i]]:
            j+=1
        out[order[i:j]]=(i+j-1)/2+1
        i=j
    return out

def corr(a,b):
    a=np.asarray(a,float); b=np.asarray(b,float)
    if len(a)<2 or np.std(a)==0 or np.std(b)==0: return None
    return float(np.corrcoef(a,b)[0,1])

def metrics(y,p):
    return {"n":len(y),"pearson":corr(y,p),"spearman":corr(rank(y),rank(p))}

def phase3_parts(row):
    base=[float(row[n]) for n in NATIVE+EXPERTS]
    s=sorted(base,reverse=True)
    v=base+[s[0],sum(s[:3])/3,base[16]*base[0],base[17]*base[15],
            base[18]*base[4],base[7]*base[15],base[19]*base[0]]
    native=speech=audio=0.0
    for idx,k,w in TERMS:
        c=w*max(0.0,v[idx]-k)
        if idx in (19,27): speech+=c
        elif idx==20: audio+=c
        else: native+=c
    mos=max(1.0,min(5.0,5.0-BIAS-native-speech-audio))
    native_mos=max(1.0,min(5.0,5.0-BIAS-native))
    return mos,native_mos,native,speech,audio

def ridge_cv(rows, columns, alpha=10.0):
    speakers=sorted(set(r["speaker"] for r in rows))
    pred=np.empty(len(rows),float)
    y=np.array([float(r["human_mushra"]) for r in rows])
    X=np.array([[float(r[c]) for c in columns] for r in rows],float)
    for sp in speakers:
        test=np.array([r["speaker"]==sp for r in rows])
        train=~test
        mu=X[train].mean(0); sd=X[train].std(0); sd[sd<1e-9]=1
        Xt=(X[train]-mu)/sd
        Xv=(X[test]-mu)/sd
        ym=y[train].mean()
        yc=y[train]-ym
        w=np.linalg.solve(Xt.T@Xt+alpha*np.eye(Xt.shape[1]),Xt.T@yc)
        pred[test]=ym+Xv@w
    return metrics(y,pred)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("csv")
    ap.add_argument("--out",required=True)
    args=ap.parse_args()
    with open(args.csv,newline="",encoding="utf-8") as f:
        rows=list(csv.DictReader(f))
    y=np.array([float(r["human_mushra"]) for r in rows])

    assoc={}
    for c in NATIVE+EXPERTS+["visqol_speech_mos","visqol_audio_mos","published_visqol_score"]:
        x=np.array([float(r[c]) for r in rows])
        assoc[c]=metrics(y,x)

    paired=[r for r in rows if str(r.get("polqa_score","")).strip()]
    assoc["polqa_score"]=metrics(
        np.array([float(r["human_mushra"]) for r in paired]),
        np.array([float(r["polqa_score"]) for r in paired]),
    )

    parts=[phase3_parts(r) for r in rows]
    phase3=np.array([x[0] for x in parts])
    native_mos=np.array([x[1] for x in parts])
    native_pen=np.array([x[2] for x in parts])
    speech_pen=np.array([x[3] for x in parts])
    audio_pen=np.array([x[4] for x in parts])

    by_codec={}
    for codec in sorted(set(r["codec"] for r in rows)):
        idx=np.array([r["codec"]==codec for r in rows])
        by_codec[codec]={
            "n":int(idx.sum()),
            "human_mushra_mean":float(y[idx].mean()),
            "phase3_mos_mean":float(phase3[idx].mean()),
            "native_only_phase3_mos_mean":float(native_mos[idx].mean()),
            "speech_penalty_mean":float(speech_pen[idx].mean()),
            "audio_penalty_mean":float(audio_pen[idx].mean()),
        }

    out={
        "n":len(rows),
        "feature_associations":assoc,
        "phase3_reconstructed":metrics(y,phase3),
        "phase3_native_terms_only":metrics(y,native_mos),
        "phase3_penalty_components":{
            "native_mean":float(native_pen.mean()),
            "speech_expert_mean":float(speech_pen.mean()),
            "audio_expert_mean":float(audio_pen.mean()),
            "speech_share_of_variable_penalty":float(speech_pen.sum()/(native_pen+speech_pen+audio_pen).sum()),
            "audio_share_of_variable_penalty":float(audio_pen.sum()/(native_pen+speech_pen+audio_pen).sum()),
        },
        "leave_one_speaker_out_ridge_forensics":{
            "native_only":ridge_cv(rows,NATIVE),
            "experts_only":ridge_cv(rows,EXPERTS),
            "native_plus_experts":ridge_cv(rows,NATIVE+EXPERTS),
        },
        "by_codec":by_codec,
        "warning":"Ridge results are diagnostic upper-bound evidence on OpenACE, not untouched validation and not a Phase 4 model claim.",
    }
    with open(args.out,"w",encoding="utf-8") as f:
        json.dump(out,f,indent=2,allow_nan=False); f.write("\n")
    print(json.dumps(out,indent=2,allow_nan=False))

if __name__=="__main__":
    main()
