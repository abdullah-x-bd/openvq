#!/usr/bin/env python3
"""Fit one full-development Phase 6.2G seed after subjective guardrails pass."""
import argparse,csv,json
from pathlib import Path
import torch

from phase6_train_sequence import SEEDS,validate_trace_rows
from phase62g_clipping_regularized import MODE_LABEL,fit_clipping_regularized

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("sequences")
    ap.add_argument("--constraints",required=True)
    ap.add_argument("--seed",required=True,type=int)
    ap.add_argument("--outdir",required=True)
    ap.add_argument("--device",default="cpu")
    ap.add_argument("--max-epochs",type=int,default=80)
    a=ap.parse_args()
    if a.seed not in SEEDS:raise SystemExit(f"seed {a.seed} not in frozen seed set {SEEDS}")
    rows=list(csv.DictReader(open(a.sequences,newline="",encoding="utf-8")))
    constraints=list(csv.DictReader(open(a.constraints,newline="",encoding="utf-8")))
    validate_trace_rows(rows);validate_trace_rows(constraints)
    model,info=fit_clipping_regularized(rows,constraints,a.seed,torch.device(a.device),a.max_epochs)
    out=Path(a.outdir);out.mkdir(parents=True,exist_ok=True)
    state=out/f"learned-bands-padding-safe-clipreg-seed{a.seed}.pt"
    report=out/f"learned-bands-padding-safe-clipreg-seed{a.seed}.json"
    torch.save(model.state_dict(),state)
    payload={"phase":"6.2G","mode":MODE_LABEL,"seed":a.seed,"rows":len(rows),
             "constraint_rows":len(constraints),"fit_info":info,"state_file":state.name,
             "status":"development qualification candidate; URGENT untouched"}
    report.write_text(json.dumps(payload,indent=2)+"\n")
    print(json.dumps(payload,indent=2))
if __name__=="__main__":main()
