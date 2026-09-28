#!/usr/bin/env python3
"""Check trained Phase 6.2G models for mask-safe padding and duration behavior."""
import argparse,csv,json
from pathlib import Path
import numpy as np
from phase63_bundle_runtime import FrozenEnsemble,trace_tensors,validate_sequence_row

def padded(arr,extra):
    ref,deg,ext,mask,glob=arr
    if extra<=0:return arr
    def padtime(x,shape):
        return np.concatenate([x,np.zeros(shape,dtype=x.dtype)],axis=1)
    r=padtime(ref,(1,extra,ref.shape[2]))
    d=padtime(deg,(1,extra,deg.shape[2]))
    e=padtime(ext,(1,extra,ext.shape[2]))
    m=np.concatenate([mask,np.zeros((1,extra),dtype=mask.dtype)],axis=1)
    return [r,d,e,m,glob]

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--bundle",required=True);ap.add_argument("--candidate-dir",required=True)
    ap.add_argument("--expected-bundle-sha256",required=True);ap.add_argument("--sequences",required=True)
    ap.add_argument("--out",required=True);ap.add_argument("--max-samples",type=int,default=32)
    ap.add_argument("--tol-mos",type=float,default=1e-4)
    a=ap.parse_args()
    rows=list(csv.DictReader(open(a.sequences,newline="",encoding="utf-8")))
    rows=sorted(rows,key=lambda r:int(r.get("trace_frames","0")))
    if len(rows)>a.max_samples:
        rows=[rows[int(i)] for i in np.linspace(0,len(rows)-1,a.max_samples,dtype=int)]
    ens=FrozenEnsemble(a.bundle,a.candidate_dir,a.expected_bundle_sha256)
    diffs=[];items=[]
    for r in rows:
        validate_sequence_row(r);arr=trace_tensors(r["trace_path"])
        _,q0,_,m0=ens.predict_arrays(arr)
        for extra in (1,17,257):
            _,q1,_,m1=ens.predict_arrays(padded(arr,extra))
            dif=abs(m1-m0);diffs.append(dif)
            items.append({"dataset":r.get("dataset"),"filename":r.get("filename"),
                          "frames":arr[0].shape[1],"extra_padded_frames":extra,
                          "base_raw":q0,"padded_raw":q1,"abs_mos_difference":dif})
    result={"phase":"6.3A","samples":len(rows),"checks":len(items),
            "batch_size_contract":1,"max_abs_mos_difference":max(diffs,default=0.0),
            "tolerance_mos":a.tol_mos,"passes":max(diffs,default=0.0)<=a.tol_mos,
            "items":items}
    Path(a.out).write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps({k:v for k,v in result.items() if k!="items"},indent=2))
    if not result["passes"]:raise SystemExit(2)
if __name__=="__main__":main()
