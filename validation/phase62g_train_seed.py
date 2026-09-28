#!/usr/bin/env python3
"""Evaluate one Phase 6.2G held-corpus seed."""
import argparse,csv,json
from pathlib import Path
import numpy as np
import torch

from phase6_train_sequence import validate_trace_rows,metrics
from phase62_padding_safe import predict_padding_safe
from phase62g_clipping_regularized import MODE_LABEL,fit_clipping_regularized

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("sequences")
    ap.add_argument("--constraints",required=True)
    ap.add_argument("--held",required=True)
    ap.add_argument("--seed",required=True,type=int)
    ap.add_argument("--out",required=True)
    ap.add_argument("--device",default="cpu")
    ap.add_argument("--max-epochs",type=int,default=80)
    a=ap.parse_args()
    torch.set_num_threads(max(1,min(2,torch.get_num_threads())))
    rows=list(csv.DictReader(open(a.sequences,newline="",encoding="utf-8")))
    constraints=list(csv.DictReader(open(a.constraints,newline="",encoding="utf-8")))
    validate_trace_rows(rows);validate_trace_rows(constraints)
    train=[r for r in rows if r["dataset"]!=a.held]
    test=[r for r in rows if r["dataset"]==a.held]
    if not train or not test:raise SystemExit("empty train/test split")
    model,info=fit_clipping_regularized(train,constraints,a.seed,torch.device(a.device),a.max_epochs)
    pred=predict_padding_safe(model,test,torch.device(a.device))
    yy=np.asarray([float(r["target_normalized"]) for r in test])
    items=[{"dataset":r["dataset"],"filename":r["filename"],
            "canonical_source_id":r["canonical_source_id"],
            "target_normalized":float(y),"prediction":float(p)}
           for r,p,y in zip(test,pred,yy)]
    result={"mode":MODE_LABEL,"held_corpus":a.held,"seed":a.seed,
            "train_rows":len(train),"test_rows":len(test),
            "metrics":metrics(yy,pred),"fit_info":info,"items":items}
    Path(a.out).parent.mkdir(parents=True,exist_ok=True)
    Path(a.out).write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps({k:v for k,v in result.items() if k!="items"},indent=2))
if __name__=="__main__":main()
