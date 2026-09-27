#!/usr/bin/env python3
"""Prove Phase 6.2E padding-context invariance before training."""
import argparse,csv,json
from pathlib import Path
import numpy as np
import torch

from phase6_train_sequence import SeqDataset,collate,validate_trace_rows
from phase62_padding_safe import PaddingSafeLearnedBands

MODEL_SEEDS=[17,23,37]
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
    long_item=ds[longest]

    indices=[]
    for d in sorted(set(r["dataset"] for r in rows)):
        ii=[i for i,r in enumerate(rows) if r["dataset"]==d]
        ii=sorted(ii,key=lambda i:int(rows[i]["trace_frames"]))
        indices.extend([ii[0],ii[len(ii)//2],ii[-1]])

    gdim=len(np.load(rows[0]["trace_path"])["global_features"])
    checks=[]
    max_delta=0.0
    violations=0
    for seed in MODEL_SEEDS:
        torch.manual_seed(seed)
        model=PaddingSafeLearnedBands(gdim)
        for i in indices:
            item=ds[i]
            alone=float(score(model,[item])[0])
            mixed=float(score(model,[item,long_item])[0])
            delta=abs(alone-mixed)*4.0
            max_delta=max(max_delta,delta)
            bad=delta>MOS_TOL
            violations+=int(bad)
            checks.append({
                "model_seed":seed,
                "dataset":rows[i]["dataset"],
                "filename":rows[i]["filename"],
                "frames":int(rows[i]["trace_frames"]),
                "paired_long_frames":int(rows[longest]["trace_frames"]),
                "alone_raw":alone,
                "mixed_batch_raw":mixed,
                "abs_mos_delta":delta,
                "passes":not bad,
            })

    result={
        "experiment_id":"phase62e-padding-invariance-v1",
        "trace_schema_id":rows[0]["trace_schema_id"],
        "trace_implementation_id":rows[0]["trace_implementation_id"],
        "model":"learned_bands_padding_safe",
        "model_seeds":MODEL_SEEDS,
        "samples_per_seed":len(indices),
        "tolerance_mos":MOS_TOL,
        "max_abs_mos_delta":max_delta,
        "violations":violations,
        "passes":violations==0,
        "checks":checks,
    }
    Path(a.out).parent.mkdir(parents=True,exist_ok=True)
    Path(a.out).write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps({k:v for k,v in result.items() if k!="checks"},indent=2))
    if violations:
        raise SystemExit(2)

if __name__=="__main__":
    main()
