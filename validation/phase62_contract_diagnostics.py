#!/usr/bin/env python3
"""Phase 6.2D training-contract diagnostics.

This script does not train or alter a model. It measures two properties of the
current sequence contract:

1. whether an utterance's inference changes when zero-padding is introduced by
   a longer utterance in the same batch;
2. the numerical scale spread of the frozen rich-v3 global feature vector.
"""
import argparse,csv,json
from pathlib import Path
import numpy as np
import torch

from phase6_feature_schema import RICH_V3
from phase6_train_sequence import Model,SeqDataset,collate,validate_trace_rows

MODEL_SEEDS=[17,23,37]
MODES=["native_temporal","learned_bands","hybrid"]
MOS_TOL=1e-4

def score(model,batch):
    (ref,deg,ext,mask,glob,y),meta=collate(batch)
    model.eval()
    with torch.no_grad():
        return model(ref,deg,ext,mask,glob).cpu().numpy()

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("sequences")
    ap.add_argument("--out",required=True)
    a=ap.parse_args()

    torch.set_num_threads(1)
    rows=list(csv.DictReader(open(a.sequences,newline="",encoding="utf-8")))
    validate_trace_rows(rows)
    ds=SeqDataset(rows)

    frames=np.asarray([int(r["trace_frames"]) for r in rows])
    longest=int(np.argmax(frames))
    by_dataset={}
    for d in sorted(set(r["dataset"] for r in rows)):
        idx=[i for i,r in enumerate(rows) if r["dataset"]==d]
        idx=sorted(idx,key=lambda i:int(rows[i]["trace_frames"]))
        by_dataset[d]=[idx[0],idx[len(idx)//2]]

    g=np.stack([np.load(r["trace_path"])["global_features"].astype(np.float64) for r in rows])
    std=g.std(axis=0)
    positive=std[std>1e-12]
    scale_report={
      "rows":len(rows),
      "feature_order":RICH_V3,
      "std_ratio_max_to_min_nonzero":float(positive.max()/positive.min()) if len(positive) else 0.0,
      "features":[{
        "name":name,
        "mean":float(g[:,i].mean()),
        "std":float(std[i]),
        "min":float(g[:,i].min()),
        "max":float(g[:,i].max()),
      } for i,name in enumerate(RICH_V3)]
    }

    checks=[]
    max_delta={m:0.0 for m in MODES}
    violations={m:0 for m in MODES}
    gdim=g.shape[1]
    long_item=ds[longest]
    for mode in MODES:
        for seed in MODEL_SEEDS:
            torch.manual_seed(seed)
            model=Model(mode,gdim)
            for dataset,indices in by_dataset.items():
                for i in indices:
                    item=ds[i]
                    alone=float(score(model,[item])[0])
                    mixed=float(score(model,[item,long_item])[0])
                    delta=abs(alone-mixed)*4.0
                    max_delta[mode]=max(max_delta[mode],delta)
                    bad=delta>MOS_TOL
                    violations[mode]+=int(bad)
                    checks.append({
                      "mode":mode,"model_seed":seed,"dataset":dataset,
                      "filename":rows[i]["filename"],
                      "frames":int(rows[i]["trace_frames"]),
                      "paired_long_frames":int(rows[longest]["trace_frames"]),
                      "alone_raw":alone,"mixed_batch_raw":mixed,
                      "abs_mos_delta":delta,"passes":not bad
                    })

    result={
      "experiment_id":"phase62d-contract-diagnostics-v1",
      "trace_schema_id":rows[0]["trace_schema_id"],
      "trace_implementation_id":rows[0]["trace_implementation_id"],
      "batch_context_tolerance_mos":MOS_TOL,
      "batch_context_max_abs_mos_delta":max_delta,
      "batch_context_violations":violations,
      "batch_context_passes":{m:violations[m]==0 for m in MODES},
      "global_feature_scale":scale_report,
      "checks":checks
    }
    Path(a.out).parent.mkdir(parents=True,exist_ok=True)
    Path(a.out).write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps({k:v for k,v in result.items() if k not in ("checks","global_feature_scale")},indent=2))
    print(json.dumps({"std_ratio_max_to_min_nonzero":scale_report["std_ratio_max_to_min_nonzero"]},indent=2))

if __name__=="__main__":main()
