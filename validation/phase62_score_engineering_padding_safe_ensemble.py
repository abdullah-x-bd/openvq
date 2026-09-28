#!/usr/bin/env python3
"""Apply the Phase 6.2F engineering gate to the three-seed ONNX ensemble."""
import argparse,csv,json
from pathlib import Path
import numpy as np
import onnxruntime as ort

SCOPED={"dropout","dropout_count","noise","lowpass","clipping","mixed"}

def tensor(path):
    z=np.load(path)
    r=np.clip((z["reference_bands_db"].astype("float32")+120)/140,0,1)
    d=np.clip((z["degraded_bands_db"].astype("float32")+120)/140,0,1)
    e=z["frame_extras"].astype("float32").copy()
    e[:,5]=np.clip((e[:,5]+120)/140,0,1)
    e[:,6]=np.clip((e[:,6]+120)/140,0,1)
    e[:,7]=np.clip(e[:,7]/500,-4,4)
    return [x[None] for x in (r,d,e,np.ones(len(r),np.float32),z["global_features"].astype("float32"))]

def score(sess,path):
    arr=tensor(path);names=[x.name for x in sess.get_inputs()]
    return float(sess.run(None,{n:x for n,x in zip(names,arr)})[0].reshape(-1)[0])

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("sequences")
    ap.add_argument("--onnx",action="append",required=True)
    ap.add_argument("--out",required=True)
    a=ap.parse_args()
    if len(a.onnx)!=3:raise SystemExit("Phase 6.2F requires exactly three ONNX seed models")
    rows=list(csv.DictReader(open(a.sequences,newline="",encoding="utf-8")))
    sessions=[ort.InferenceSession(p,providers=["CPUExecutionProvider"]) for p in a.onnx]
    scored=[]
    for r in rows:
        raw=[score(s,r["trace_path"]) for s in sessions]
        q=float(np.mean(raw));m=1+4*min(1,max(0,q))
        scored.append({"family":r["family"],"level":float(r["level"]),"label":r["label"],
                       "seed_quality_raw":raw,"ensemble_quality_raw":q,"mos":m})
    clean=next(r["mos"] for r in scored if r["family"]=="clean")
    failures=[]
    if clean<4.4:failures.append(f"identity MOS {clean:.3f}<4.4")
    delay=[r for r in scored if r["family"]=="delay"]
    delay_delta=max(abs(r["mos"]-clean) for r in delay)
    if delay_delta>0.20:failures.append(f"pure delay max delta {delay_delta:.3f}>0.20 MOS")
    fam={}
    for name in sorted(SCOPED):
        rr=sorted([r for r in scored if r["family"]==name],key=lambda z:z["level"])
        n=sum(b["mos"]>a0["mos"]+.12 for a0,b in zip(rr,rr[1:]))
        fam[name]={"rows":rr,"violations_gt_0.12_mos":n}
        if n:failures.append(f"{name}:{n} reversals")
    result={
      "phase":"6.2F","model":"learned_bands_padding_safe","ensemble":"mean raw quality across three fixed seeds",
      "identity_mos":clean,"delay_max_abs_delta_mos":delay_delta,
      "scoped_monotonic":fam,"failures":failures,"passes":not failures
    }
    Path(a.out).write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps(result,indent=2))
    if failures:raise SystemExit(2)
if __name__=="__main__":main()
