#!/usr/bin/env python3
"""Score Trace V3 rows with exactly three Phase 6.3B-R1 ONNX seed models."""
import argparse,csv,math
import numpy as np
import onnxruntime as ort
TRACE_SCHEMA="openvq-trace-v3-2026-09-29";TRACE_IMPL="openvq-trace-v3-transport-fallback-2026-09-29"
def tensors(path):
    z=np.load(path);ref=np.clip((z["reference_bands_db"].astype("float32")+120)/140,0,1);deg=np.clip((z["degraded_bands_db"].astype("float32")+120)/140,0,1)
    ext=z["frame_extras"].astype("float32").copy();ext[:,5]=np.clip((ext[:,5]+120)/140,0,1);ext[:,6]=np.clip((ext[:,6]+120)/140,0,1);ext[:,7]=np.clip(ext[:,7]/500,-4,4)
    glob=z["global_features"].astype("float32");mask=np.ones(len(ref),np.float32)
    return dict(zip(["reference_bands","degraded_bands","frame_extras","mask","global_features"],[x[None] for x in (ref,deg,ext,mask,glob)]))
def main():
    ap=argparse.ArgumentParser();ap.add_argument("sequences");ap.add_argument("--onnx",action="append",required=True);ap.add_argument("--out",required=True);a=ap.parse_args()
    if len(a.onnx)!=3:raise SystemExit("exactly three ONNX models required")
    rows=list(csv.DictReader(open(a.sequences,newline="",encoding="utf-8")))
    if any(r.get("trace_schema_id")!=TRACE_SCHEMA or r.get("trace_implementation_id")!=TRACE_IMPL for r in rows):raise SystemExit("Trace V3 contract mismatch")
    ss=[ort.InferenceSession(p,providers=["CPUExecutionProvider"]) for p in a.onnx];names=[[x.name for x in s.get_inputs()] for s in ss];out=[]
    for n,r in enumerate(rows,1):
        arr=tensors(r["trace_path"]);raw=[]
        for s,nn in zip(ss,names):
            q=float(s.run(None,{k:arr[k] for k in nn})[0].reshape(-1)[0])
            if not math.isfinite(q):raise SystemExit("non-finite ONNX output")
            raw.append(q)
        mean=float(np.mean(raw));q=float(np.clip(mean,0,1));mos=1+4*q;x=dict(r)
        x.update({"openvq_seed20260926_raw":raw[0],"openvq_seed20260927_raw":raw[1],"openvq_seed20260928_raw":raw[2],"openvq_quality_raw":mean,"openvq_quality":q,"openvq_mos":mos});out.append(x)
        if n%50==0 or n==len(rows):print("scored",n,"/",len(rows),flush=True)
    fields=[]
    for r in out:
        for k in r:
            if k not in fields:fields.append(k)
    with open(a.out,"w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(out)
if __name__=="__main__":main()
