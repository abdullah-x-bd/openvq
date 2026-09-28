#!/usr/bin/env python3
"""Predeclared Phase 6.3B-R1 no-regression screen against Phase 6.2G."""
import argparse,json
from pathlib import Path
BASE={"worst":0.32806753383097176,"mean":0.48870422565004407,"rmse":0.291897149568309}
FLOOR={"worst":0.29526078044787457,"mean":0.46426901436754187,"rmse":0.3064920070467244}
def main():
    ap=argparse.ArgumentParser();ap.add_argument("selection");ap.add_argument("--out",required=True);a=ap.parse_args()
    r=json.loads(Path(a.selection).read_text());mode=r["selected_mode"];o=r["selected_objective"];fail=[]
    if o["worst_held_corpus_correlation"]<FLOOR["worst"]:fail.append("worst correlation below 90% of Phase 6.2G")
    if o["mean_held_corpus_correlation"]<FLOOR["mean"]:fail.append("mean correlation below 95% of Phase 6.2G")
    if o["worst_rmse_normalized"]>FLOOR["rmse"]:fail.append("worst nRMSE above 105% of Phase 6.2G")
    for held,x in r["modes"][mode]["by_held_corpus"].items():
        if x["test"]["pearson"]<=0 or x["test"]["spearman"]<=0:fail.append(f"{held}: non-positive correlation")
    out={"phase":"6.3B-R1","baseline":"6.2G","baseline_objective":BASE,"guardrails":FLOOR,"observed":o,"failures":fail,"passes":not fail,"reserve_consumed":False}
    Path(a.out).write_text(json.dumps(out,indent=2)+"\n");print(json.dumps(out,indent=2))
    if fail:raise SystemExit(2)
if __name__=="__main__":main()
