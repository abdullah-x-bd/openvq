#!/usr/bin/env python3
"""Enforce predeclared Phase 6.2G subjective no-regression guardrails."""
import argparse,json
from pathlib import Path

BASE={
  "worst_held_corpus_correlation":0.18997017896619228,
  "mean_held_corpus_correlation":0.4550500829454453,
  "worst_rmse_normalized":0.30620986251810384,
}
FLOORS={
  "worst_held_corpus_correlation":0.90*BASE["worst_held_corpus_correlation"],
  "mean_held_corpus_correlation":0.95*BASE["mean_held_corpus_correlation"],
  "worst_rmse_normalized":1.05*BASE["worst_rmse_normalized"],
}

def main():
    ap=argparse.ArgumentParser();ap.add_argument("selection");ap.add_argument("--out",required=True);a=ap.parse_args()
    r=json.loads(Path(a.selection).read_text());mode=r["selected_mode"];obj=r["selected_objective"]
    failures=[]
    if obj["worst_held_corpus_correlation"]<FLOORS["worst_held_corpus_correlation"]:
        failures.append("worst held-corpus correlation below 90% of Phase 6.2E")
    if obj["mean_held_corpus_correlation"]<FLOORS["mean_held_corpus_correlation"]:
        failures.append("mean held-corpus correlation below 95% of Phase 6.2E")
    if obj["worst_rmse_normalized"]>FLOORS["worst_rmse_normalized"]:
        failures.append("worst normalized RMSE exceeds 105% of Phase 6.2E")
    by=r["modes"][mode]["by_held_corpus"]
    for held,x in sorted(by.items()):
        if x["test"]["pearson"]<=0 or x["test"]["spearman"]<=0:
            failures.append(f"{held}: non-positive held-corpus correlation")
    result={"phase":"6.2G","baseline":"Phase 6.2E padding-safe three-seed ensemble",
            "baseline_objective":BASE,"guardrails":FLOORS,"observed":obj,
            "all_held_correlations_must_be_positive":True,
            "failures":failures,"passes":not failures}
    Path(a.out).write_text(json.dumps(result,indent=2)+"\n");print(json.dumps(result,indent=2))
    if failures:raise SystemExit(2)
if __name__=="__main__":main()
