#!/usr/bin/env python3
"""Summarize Phase 6.3B learned-model behavior without inventing synthetic MOS targets."""
from __future__ import annotations
import argparse,csv,json,statistics
from collections import defaultdict
from pathlib import Path
import numpy as np

FEATURES=["missing","added","noisiness","lost_active_speech","active_coverage",
          "alignment_uncertainty","multi_resolution","temporal","modulation",
          "confidence_deficit","clock_drift_abs_ppm","clipping_ratio_raw"]

def median(v):return float(np.median(np.asarray(v,float))) if v else None

def main():
    ap=argparse.ArgumentParser();ap.add_argument("scored");ap.add_argument("features");ap.add_argument("--out",required=True);a=ap.parse_args()
    rows=list(csv.DictReader(open(a.scored,newline="",encoding="utf-8")))
    feats={r["filename"]:r for r in csv.DictReader(open(a.features,newline="",encoding="utf-8"))}
    if not rows:raise SystemExit("empty 6.3B score table")
    byref=defaultdict(list)
    for r in rows:byref[r["reference_id"]].append(r)
    blockers=[];invariance=[];per_reference_ordering=[]
    identities={}
    for rid,rr in sorted(byref.items()):
        ident=next(float(x["openvq_mos"]) for x in rr if x["family"]=="identity")
        identities[rid]=ident
        if ident<4.4:blockers.append(f"{rid}: identity {ident:.3f}<4.4")
        for fam,tol in (("delay",.20),("polarity",.20),("silence_padding",.20)):
            vals=[x for x in rr if x["family"]==fam]
            for x in vals:
                d=abs(float(x["openvq_mos"])-ident)
                invariance.append({"reference_id":rid,"family":fam,"label":x["label"],"abs_delta_mos":d,"tolerance":tol})
                if d>tol:blockers.append(f"{rid}:{fam}:{x['label']} delta {d:.3f}>{tol:.2f}")
    ordered=["noise","resample_roundtrip","attenuation","clipping","burst_loss","repeated_segment","clock_drift","time_scale"]
    blocking_ordered={"noise","attenuation","clipping","burst_loss","repeated_segment","clock_drift","time_scale"}
    aggregate={}
    for fam in ordered:
        famrows=[r for r in rows if r["family"]==fam]
        levels=sorted(set(float(r["level"]) for r in famrows))
        medrows=[]
        for level in levels:
            q=[r for r in famrows if float(r["level"])==level]
            medrows.append({"level":level,"labels":sorted(set(r["label"] for r in q)),
                            "median_mos":median([float(r["openvq_mos"]) for r in q]),"n":len(q)})
        reversals=sum(b["median_mos"]>a0["median_mos"]+.12 for a0,b in zip(medrows,medrows[1:]))
        aggregate[fam]={"rows":medrows,"aggregate_reversals_gt_0.12_mos":reversals}
        if reversals and fam in blocking_ordered:
            blockers.append(f"{fam}: {reversals} aggregate severity reversals >0.12 MOS")
        for rid,rr in sorted(byref.items()):
            q=sorted([x for x in rr if x["family"]==fam],key=lambda x:float(x["level"]))
            if len(q)>1:
                n=sum(float(b["openvq_mos"])>float(a0["openvq_mos"])+.12 for a0,b in zip(q,q[1:]))
                per_reference_ordering.append({"reference_id":rid,"family":fam,"reversals_gt_0.12_mos":n})
    mild={}
    for label in ("snr60","snr40"):
        q=[r for r in rows if r["family"]=="noise" and r["label"]==label]
        native=[]
        for r in q:
            f=feats[r["filename"]]
            native.append({k:float(f[k]) for k in FEATURES if k in f and f[k]!=" " and f[k]!=""})
        featmeans={}
        for k in FEATURES:
            vv=[x[k] for x in native if k in x]
            if vv:featmeans[k]=float(np.mean(vv))
        mild[label]={
          "n":len(q),"median_mos":median([float(r["openvq_mos"]) for r in q]),
          "mean_mos":float(np.mean([float(r["openvq_mos"]) for r in q])),
          "mean_identity_delta_mos":float(np.mean([identities[r["reference_id"]]-float(r["openvq_mos"]) for r in q])),
          "mean_seed_raw":[float(np.mean([float(r[f"openvq_seed{s}_raw"]) for r in q])) for s in (20260926,20260927,20260928)],
          "native_feature_means":featmeans,
          "interpretation":"diagnostic only; no synthetic human-MOS target is asserted",
        }
    silence=[float(r["openvq_mos"]) for r in rows if r["family"]=="silence_only"]
    result={
      "phase":"6.3B","references":len(byref),"rows":len(rows),
      "languages":sorted(set(r["language"] for r in rows)),
      "source_corpora":sorted(set(r["source_corpus"] for r in rows)),
      "criteria":{
        "identity_min_mos":4.4,
        "invariance_max_abs_delta_mos":0.20,
        "aggregate_ordering_reversal_tolerance_mos":0.12,
        "resample_roundtrip_status":"diagnostic only because original sample-rate availability differs by reference",
        "absolute_synthetic_mos_targets":"none",
      },
      "identity_mos_by_reference":identities,
      "invariance_checks":invariance,
      "aggregate_ordering":aggregate,
      "per_reference_ordering_diagnostic":per_reference_ordering,
      "mild_noise_diagnostic":mild,
      "silence_only_median_mos":median(silence),
      "blocking_failures":blockers,
      "passes_pre_reserve_engineering_screen":not blockers,
      "claim_boundary":"Ordering and invariance are engineering checks. Absolute transformed scores without human ratings are diagnostics only.",
    }
    Path(a.out).write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps({k:v for k,v in result.items() if k not in ("invariance_checks","per_reference_ordering_diagnostic","aggregate_ordering")},indent=2))
if __name__=="__main__":main()
