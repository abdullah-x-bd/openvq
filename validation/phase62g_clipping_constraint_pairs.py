#!/usr/bin/env python3
"""Build Phase 6.2G clipping-order fixtures that are separate from the protected gate."""
import argparse,csv,hashlib,json,math,random
from pathlib import Path

from engineering_matrix import SR,clip_signal,write_wav

THRESHOLDS=[0.85,0.65,0.45,0.30,0.18,0.11]
PROTECTED_THRESHOLDS={0.95,0.50,0.25,0.08}
SOURCE_SPECS=[
    (62031,5.2,121.0,2.15),
    (62047,6.4,137.0,1.91),
    (62063,7.1,109.0,2.43),
]

def speech_variant(seed,seconds,f0,syll_rate):
    rng=random.Random(seed)
    ratios=[1.0,1.63,2.91,5.77,11.8,22.4,40.6,72.0]
    amps=[0.16,0.145,0.12,0.092,0.066,0.044,0.027,0.014]
    phases=[rng.random()*2*math.pi for _ in ratios]
    n=int(SR*seconds);out=[]
    for i in range(n):
        t=i/SR
        syll=0.24+0.76*max(0.0,math.sin(2*math.pi*syll_rate*t+0.2))**0.72
        phrase=1.0 if (i//int((0.74+0.03*(seed%5))*SR))%6!=5 else 0.11
        flutter=0.91+0.09*math.sin(2*math.pi*(0.29+0.01*(seed%7))*t)
        s=sum(a*math.sin(2*math.pi*(f0*r)*t+p) for a,r,p in zip(amps,ratios,phases))
        s=s*syll*phrase*flutter+0.009*math.sin(2*math.pi*43*t+phases[0])
        out.append(s)
    peak=max(abs(v) for v in out)
    return [0.92*v/peak for v in out]

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("outdir")
    ap.add_argument("manifest")
    a=ap.parse_args()
    if set(THRESHOLDS)&PROTECTED_THRESHOLDS:
        raise SystemExit("training clipping thresholds overlap protected engineering gate")
    out=Path(a.outdir);out.mkdir(parents=True,exist_ok=True)
    rows=[];refs=[]
    for idx,(seed,seconds,f0,syll_rate) in enumerate(SOURCE_SPECS,1):
        base=speech_variant(seed,seconds,f0,syll_rate)
        ref=out/f"constraint_ref_{idx}.wav";write_wav(ref,base)
        refs.append({"source_id":f"phase62g-ref-{idx}","file":ref.name,"sha256":sha(ref)})
        for threshold in THRESHOLDS:
            tag=str(threshold).replace(".","p")
            deg=out/f"constraint_ref_{idx}_thr_{tag}.wav"
            write_wav(deg,clip_signal(base,threshold))
            rows.append({
                "dataset":"phase62g_clipping",
                "reference":str(ref.resolve()),
                "degraded":str(deg.resolve()),
                "filename":deg.name,
                "canonical_source_id":f"phase62g-ref-{idx}",
                "group_id":f"phase62g-ref-{idx}",
                "condition_id":f"clip-{threshold:.2f}",
                "family":"clipping_constraint",
                "level":1.0-threshold,
                "label":f"train_thr{threshold:.2f}",
                "placeholder_mos":1.0,
                "target_normalized":0.0,
            })
    with open(a.manifest,"w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    prov={
      "phase":"6.2G",
      "purpose":"pairwise clipping-order property regularization only; no subjective target use",
      "rows":len(rows),
      "source_count":len(SOURCE_SPECS),
      "training_thresholds":THRESHOLDS,
      "protected_gate_thresholds":sorted(PROTECTED_THRESHOLDS,reverse=True),
      "threshold_sets_disjoint":True,
      "references":refs,
      "manifest_sha256":sha(a.manifest),
    }
    (out/"constraint-provenance.json").write_text(json.dumps(prov,indent=2)+"\n")
    print(json.dumps(prov,indent=2))
if __name__=="__main__":main()
