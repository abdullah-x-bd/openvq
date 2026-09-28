#!/usr/bin/env python3
"""Fit one full-development Phase 6.3B-R1 seed after held-corpus guardrails pass."""
import argparse,csv,json
from pathlib import Path
import torch
from phase6_train_sequence import SEEDS
from phase63_train_seed import validate
from phase63_repaired_model import MODE_LABEL,fit_repaired
def main():
    ap=argparse.ArgumentParser();ap.add_argument("sequences");ap.add_argument("--clip",required=True);ap.add_argument("--invariance",required=True)
    ap.add_argument("--seed",required=True,type=int);ap.add_argument("--outdir",required=True);ap.add_argument("--max-epochs",type=int,default=80);a=ap.parse_args()
    if a.seed not in SEEDS:raise SystemExit("seed outside frozen set")
    rows=list(csv.DictReader(open(a.sequences,newline="",encoding="utf-8")));clips=list(csv.DictReader(open(a.clip,newline="",encoding="utf-8")));inv=list(csv.DictReader(open(a.invariance,newline="",encoding="utf-8")))
    validate(rows);validate(clips);validate(inv);model,info=fit_repaired(rows,clips,inv,a.seed,torch.device("cpu"),a.max_epochs)
    out=Path(a.outdir);out.mkdir(parents=True,exist_ok=True);state=out/f"phase63b-r1-seed{a.seed}.pt";report=out/f"phase63b-r1-seed{a.seed}.json"
    torch.save(model.state_dict(),state);payload={"phase":"6.3B-R1","mode":MODE_LABEL,"seed":a.seed,"human_rows":len(rows),"clip_rows":len(clips),"invariance_rows":len(inv),"fit_info":info,"state_file":state.name,"reserve_consumed":False}
    report.write_text(json.dumps(payload,indent=2)+"\n");print(json.dumps(payload,indent=2))
if __name__=="__main__":main()
