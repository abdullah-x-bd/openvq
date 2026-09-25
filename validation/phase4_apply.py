#!/usr/bin/env python3
"""Apply a Phase-4 robust fusion candidate to an extracted feature table."""
import argparse,csv,json
import numpy as np

def main():
    ap=argparse.ArgumentParser();ap.add_argument("features");ap.add_argument("model");ap.add_argument("output")
    a=ap.parse_args()
    rows=list(csv.DictReader(open(a.features,newline="",encoding="utf-8")))
    m=json.load(open(a.model,encoding="utf-8"))
    names=m["native_features"]
    w=np.asarray([m["native_weights"][n] for n in names],float)
    cap=float(m["expert_delta_cap_mos"]);alpha=float(m["expert_alpha"])
    out=[]
    for r in rows:
        x=np.asarray([float(r[n]) for n in names],float)
        native=float(np.clip(5.0-m["native_bias"]-x@w,1.0,5.0))
        speech=5.0-4.0*float(r["visqol_speech"])
        audio=5.0-4.0*float(r["visqol_audio"])
        median=float(np.median([native,speech,audio]))
        delta=float(np.clip(median-native,-cap,cap))
        q=dict(r)
        q["phase4_native_mos"]=native
        q["phase4_expert_median_mos"]=median
        q["phase4_mos"]=float(np.clip(native+alpha*delta,1.0,5.0))
        q["phase4_model_id"]=m["model_id"]
        out.append(q)
    with open(a.output,"w",newline="",encoding="utf-8") as f:
        wr=csv.DictWriter(f,fieldnames=list(out[0]));wr.writeheader();wr.writerows(out)

if __name__=="__main__":main()
