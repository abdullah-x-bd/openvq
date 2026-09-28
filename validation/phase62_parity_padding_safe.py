#!/usr/bin/env python3
"""Check Phase 6.2F padding-safe PyTorch/ONNX parity over varied lengths."""
import argparse,csv,json
from pathlib import Path
import numpy as np
import onnxruntime as ort
import torch

from phase62_padding_safe import PaddingSafeLearnedBands

def tensors(path):
    z=np.load(path)
    ref=np.clip((z["reference_bands_db"].astype("float32")+120)/140,0,1)
    deg=np.clip((z["degraded_bands_db"].astype("float32")+120)/140,0,1)
    ext=z["frame_extras"].astype("float32").copy()
    ext[:,5]=np.clip((ext[:,5]+120)/140,0,1)
    ext[:,6]=np.clip((ext[:,6]+120)/140,0,1)
    ext[:,7]=np.clip(ext[:,7]/500,-4,4)
    glob=z["global_features"].astype("float32")
    mask=np.ones(len(ref),np.float32)
    return [x[None] for x in (ref,deg,ext,mask,glob)]

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--state",required=True)
    ap.add_argument("--onnx",required=True)
    ap.add_argument("--sequences",required=True)
    ap.add_argument("--out",required=True)
    ap.add_argument("--max-samples",type=int,default=64)
    ap.add_argument("--mos-tol",type=float,default=1e-4)
    a=ap.parse_args()
    rows=list(csv.DictReader(open(a.sequences,newline="",encoding="utf-8")))
    rows=sorted(rows,key=lambda r:int(r.get("trace_frames","0")))
    if len(rows)>a.max_samples:
        idx=np.linspace(0,len(rows)-1,a.max_samples,dtype=int)
        rows=[rows[int(i)] for i in idx]
    gdim=len(np.load(rows[0]["trace_path"])["global_features"])
    model=PaddingSafeLearnedBands(gdim)
    model.load_state_dict(torch.load(a.state,map_location="cpu"));model.eval()
    sess=ort.InferenceSession(a.onnx,providers=["CPUExecutionProvider"])
    names=[x.name for x in sess.get_inputs()]
    diffs=[];items=[]
    for r in rows:
        arr=tensors(r["trace_path"])
        with torch.no_grad():
            pt=float(model(*(torch.from_numpy(x) for x in arr)).item())
        feed={n:x for n,x in zip(names,arr)}
        ox=float(sess.run(None,feed)[0].reshape(-1)[0])
        dm=abs(pt-ox)*4
        diffs.append(dm)
        items.append({"dataset":r["dataset"],"filename":r["filename"],"frames":len(arr[0][0]),
                      "pytorch_quality":pt,"onnx_quality":ox,"abs_mos_difference":dm})
    result={"samples":len(items),"max_abs_mos_difference":max(diffs),"tolerance":a.mos_tol,
            "passes":max(diffs)<=a.mos_tol,"items":items}
    Path(a.out).write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps({k:v for k,v in result.items() if k!="items"},indent=2))
    if not result["passes"]:raise SystemExit(2)
if __name__=="__main__":main()
