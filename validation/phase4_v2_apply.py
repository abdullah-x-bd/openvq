#!/usr/bin/env python3
"""Apply a frozen-compatible Phase-4 v2 JSON model to a feature CSV."""
import argparse,csv,json
import numpy as np

def base_values(row,native):
    v={k:float(row[k]) for k in native}
    v["speech_q"]=1.0-float(row["visqol_speech"])
    v["audio_q"]=1.0-float(row["visqol_audio"])
    v["expert_mean_q"]=(v["speech_q"]+v["audio_q"])/2.0
    v["expert_min_q"]=min(v["speech_q"],v["audio_q"])
    v["expert_max_q"]=max(v["speech_q"],v["audio_q"])
    v["expert_absdiff_q"]=abs(v["speech_q"]-v["audio_q"])
    return v

def vector(row,m):
    v=base_values(row,m["native_features"])
    native=m["native_features"];selected=m["selected_interaction_native_features"]
    x=[v[c] for c in native]
    x += [v[c] for c in ("speech_q","audio_q","expert_mean_q","expert_min_q","expert_max_q","expert_absdiff_q")]
    x += [v[c]*v[c] for c in native]
    x += [v[e]*v[c] for e in ("speech_q","audio_q","expert_absdiff_q") for c in selected]
    return np.asarray(x,float)

def main():
    ap=argparse.ArgumentParser();ap.add_argument("features");ap.add_argument("model");ap.add_argument("output");a=ap.parse_args()
    m=json.load(open(a.model,encoding="utf-8"))
    mm=m["model"];mean=np.asarray(mm["feature_mean"]);scale=np.asarray(mm["feature_scale"]);coef=np.asarray(mm["coefficients"])
    rows=list(csv.DictReader(open(a.features,newline="",encoding="utf-8")))
    out=[]
    for r in rows:
        x=vector(r,m);q=float(np.clip(mm["intercept"]+((x-mean)/scale)@coef,0.0,1.0))
        z=dict(r);z["phase4_v2_q"]=q;z["phase4_v2_mos"]=1.0+4.0*q;z["phase4_v2_model_id"]=m["model_id"];out.append(z)
    with open(a.output,"w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=list(out[0]));w.writeheader();w.writerows(out)

if __name__=="__main__":main()
