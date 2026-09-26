#!/usr/bin/env python3
"""Score cached Phase 6 traces with a frozen ONNX model."""
import argparse,csv,json
from pathlib import Path
import numpy as np
import onnxruntime as ort

def tensors(path):
    z=np.load(path);ref=np.clip((z["reference_bands_db"].astype("float32")+120)/140,0,1)
    deg=np.clip((z["degraded_bands_db"].astype("float32")+120)/140,0,1)
    ext=z["frame_extras"].astype("float32").copy()
    ext[:,5]=np.clip((ext[:,5]+120)/140,0,1);ext[:,6]=np.clip((ext[:,6]+120)/140,0,1)
    ext[:,7]=np.clip(ext[:,7]/500,-4,4);mask=np.ones(len(ref),np.float32);glob=z["global_features"].astype("float32")
    return [x[None] for x in (ref,deg,ext,mask,glob)]
def main():
    ap=argparse.ArgumentParser();ap.add_argument("sequences");ap.add_argument("--onnx",required=True);ap.add_argument("--out",required=True)
    a=ap.parse_args();rows=list(csv.DictReader(open(a.sequences,newline="",encoding="utf-8")))
    sess=ort.InferenceSession(a.onnx,providers=["CPUExecutionProvider"]);names=[x.name for x in sess.get_inputs()]
    out=[]
    for i,r in enumerate(rows,1):
        arr=tensors(r["trace_path"]);q=float(sess.run(None,{n:x for n,x in zip(names,arr)})[0].reshape(-1)[0])
        out.append({**r,"openvq_quality_raw":q,"openvq_quality":min(1,max(0,q)),"openvq_mos":1+4*min(1,max(0,q))})
        if i%25==0 or i==len(rows):print("scored",i,"/",len(rows),flush=True)
    with open(a.out,"w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=list(out[0]));w.writeheader();w.writerows(out)
if __name__=="__main__":main()
