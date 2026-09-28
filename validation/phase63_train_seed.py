#!/usr/bin/env python3
"""Evaluate one Phase 6.3B-R1 seed with held-corpus-safe property fixtures."""
import argparse,csv,json
from pathlib import Path
import numpy as np
import torch
from phase6_train_sequence import metrics
from phase62_padding_safe import predict_padding_safe
from phase63_repaired_model import MODE_LABEL,fit_repaired
TRACE_SCHEMA="openvq-trace-v3-2026-09-29";TRACE_IMPL="openvq-trace-v3-transport-fallback-2026-09-29"
def validate(rows):
    if not rows:raise SystemExit("empty trace rows")
    if any(r.get("trace_schema_id")!=TRACE_SCHEMA for r in rows):raise SystemExit("Trace V3 schema mismatch")
    if any(r.get("trace_implementation_id")!=TRACE_IMPL for r in rows):raise SystemExit("Trace V3 implementation mismatch")
def main():
    ap=argparse.ArgumentParser();ap.add_argument("sequences");ap.add_argument("--clip",required=True);ap.add_argument("--invariance",required=True)
    ap.add_argument("--held",required=True);ap.add_argument("--seed",required=True,type=int);ap.add_argument("--out",required=True);ap.add_argument("--max-epochs",type=int,default=80);a=ap.parse_args()
    torch.set_num_threads(max(1,min(2,torch.get_num_threads())))
    rows=list(csv.DictReader(open(a.sequences,newline="",encoding="utf-8")));clips=list(csv.DictReader(open(a.clip,newline="",encoding="utf-8")));inv=list(csv.DictReader(open(a.invariance,newline="",encoding="utf-8")))
    validate(rows);validate(clips);validate(inv);train=[r for r in rows if r["dataset"]!=a.held];test=[r for r in rows if r["dataset"]==a.held]
    inv_allowed=[r for r in inv if r.get("property_corpus")!=a.held]
    if not train or not test or not inv_allowed:raise SystemExit("empty train/test/property split")
    model,info=fit_repaired(train,clips,inv_allowed,a.seed,torch.device("cpu"),a.max_epochs)
    pred=predict_padding_safe(model,test,torch.device("cpu"));yy=np.asarray([float(r["target_normalized"]) for r in test])
    items=[{"dataset":r["dataset"],"filename":r["filename"],"canonical_source_id":r["canonical_source_id"],"target_normalized":float(y),"prediction":float(p)} for r,p,y in zip(test,pred,yy)]
    result={"mode":MODE_LABEL,"held_corpus":a.held,"seed":a.seed,"train_rows":len(train),"test_rows":len(test),"property_rows":len(inv_allowed),"metrics":metrics(yy,pred),"fit_info":info,"items":items}
    Path(a.out).parent.mkdir(parents=True,exist_ok=True);Path(a.out).write_text(json.dumps(result,indent=2)+"\n");print(json.dumps({k:v for k,v in result.items() if k!="items"},indent=2))
if __name__=="__main__":main()
