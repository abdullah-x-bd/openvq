#!/usr/bin/env python3
"""Compare PyTorch and ONNX Phase 6 inference on cached traces."""
import argparse,csv,json
from pathlib import Path
import numpy as np
import onnxruntime as ort
import torch
from phase6_train_sequence import Model

def tensors(path):
    z=np.load(path);ref=np.clip((z["reference_bands_db"].astype("float32")+120)/140,0,1)
    deg=np.clip((z["degraded_bands_db"].astype("float32")+120)/140,0,1)
    ext=z["frame_extras"].astype("float32").copy()
    ext[:,5]=np.clip((ext[:,5]+120)/140,0,1);ext[:,6]=np.clip((ext[:,6]+120)/140,0,1)
    ext[:,7]=np.clip(ext[:,7]/500,-4,4)
    glob=z["global_features"].astype("float32")
    mask=np.ones(len(ref),np.float32)
    return [x[None] for x in (ref,deg,ext,mask,glob)]
def main():
    ap=argparse.ArgumentParser();ap.add_argument("--mode",required=True);ap.add_argument("--state",required=True)
    ap.add_argument("--onnx",required=True);ap.add_argument("--sequences",required=True);ap.add_argument("--out",required=True)
    ap.add_argument("--max-samples",type=int,default=32);ap.add_argument("--mos-tol",type=float,default=1e-4)
    a=ap.parse_args();rows=list(csv.DictReader(open(a.sequences,newline="",encoding="utf-8")))[:a.max_samples]
    gdim=len(np.load(rows[0]["trace_path"])["global_features"]);m=Model(a.mode,gdim)
    m.load_state_dict(torch.load(a.state,map_location="cpu"));m.eval()
    sess=ort.InferenceSession(a.onnx,providers=["CPUExecutionProvider"]);names=[x.name for x in sess.get_inputs()]
    diffs=[];items=[]
    for r in rows:
        arr=tensors(r["trace_path"])
        with torch.no_grad():
            pt=float(m(*(torch.from_numpy(x) for x in arr)).item())
        ox=float(sess.run(None,{n:x for n,x in zip(names,arr)})[0].reshape(-1)[0])
        dm=abs(pt-ox)*4;diffs.append(dm);items.append({"dataset":r["dataset"],"filename":r["filename"],
            "pytorch_quality":pt,"onnx_quality":ox,"abs_mos_difference":dm})
    result={"samples":len(items),"max_abs_mos_difference":max(diffs),"tolerance":a.mos_tol,
            "passes":max(diffs)<=a.mos_tol,"items":items}
    Path(a.out).write_text(json.dumps(result,indent=2)+"\n");print(json.dumps(result,indent=2))
    if not result["passes"]:raise SystemExit(2)
if __name__=="__main__":main()
