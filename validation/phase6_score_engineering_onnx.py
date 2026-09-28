#!/usr/bin/env python3
"""Model-specific Phase 6 engineering report for frozen ONNX inference."""
import argparse,csv,json
from pathlib import Path
import numpy as np
import onnxruntime as ort

SCOPED={"dropout","dropout_count","noise","lowpass","clipping","mixed"}
def tensor(path):
    z=np.load(path);r=np.clip((z["reference_bands_db"].astype("float32")+120)/140,0,1)
    d=np.clip((z["degraded_bands_db"].astype("float32")+120)/140,0,1);e=z["frame_extras"].astype("float32").copy()
    e[:,5]=np.clip((e[:,5]+120)/140,0,1);e[:,6]=np.clip((e[:,6]+120)/140,0,1);e[:,7]=np.clip(e[:,7]/500,-4,4)
    return [x[None] for x in (r,d,e,np.ones(len(r),np.float32),z["global_features"].astype("float32"))]
def main():
    ap=argparse.ArgumentParser();ap.add_argument("sequences");ap.add_argument("--onnx",required=True);ap.add_argument("--out",required=True);a=ap.parse_args()
    rows=list(csv.DictReader(open(a.sequences,newline="",encoding="utf-8")));s=ort.InferenceSession(a.onnx,providers=["CPUExecutionProvider"]);names=[x.name for x in s.get_inputs()]
    scored=[]
    for r in rows:
        q=float(s.run(None,{n:x for n,x in zip(names,tensor(r["trace_path"]))})[0].reshape(-1)[0]);m=1+4*min(1,max(0,q))
        scored.append({"family":r["family"],"level":float(r["level"]),"label":r["label"],"quality_raw":q,"mos":m})
    clean=next(r["mos"] for r in scored if r["family"]=="clean");fail=[]
    if clean<4.4:fail.append(f"identity MOS {clean:.3f}<4.4")
    delay=[r for r in scored if r["family"]=="delay"]
    if max(abs(r["mos"]-clean) for r in delay)>0.20:fail.append("pure delay exceeds 0.20 MOS")
    fam={}
    for name in sorted(SCOPED):
        rr=sorted([r for r in scored if r["family"]==name],key=lambda z:z["level"])
        n=sum(b["mos"]>a["mos"]+.12 for a,b in zip(rr,rr[1:]));fam[name]={"rows":rr,"violations_gt_0.12_mos":n}
        if n:fail.append(f"{name}:{n} reversals")
    result={"identity_mos":clean,"delay_max_abs_delta_mos":max(abs(r["mos"]-clean) for r in delay),
            "scoped_monotonic":fam,"failures":fail}
    Path(a.out).write_text(json.dumps(result,indent=2)+"\n");print(json.dumps(result,indent=2))
    if fail:raise SystemExit(2)
if __name__=="__main__":main()
