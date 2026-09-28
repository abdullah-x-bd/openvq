#!/usr/bin/env python3
"""Aggregate three Phase 6E seed predictions into the canonical held-corpus fold result."""
import argparse,json
from pathlib import Path
import numpy as np
from phase6_train_sequence import SEEDS,metrics

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--seed-report",action="append",required=True)
    ap.add_argument("--out",required=True)
    a=ap.parse_args()
    rr=[json.loads(Path(p).read_text()) for p in a.seed_report]
    rr=sorted(rr,key=lambda x:x["seed"])
    if [x["seed"] for x in rr]!=SEEDS:
        raise SystemExit(f"seed set mismatch: {[x['seed'] for x in rr]} != {SEEDS}")
    mode=rr[0]["mode"];held=rr[0]["held_corpus"]
    if any(x["mode"]!=mode or x["held_corpus"]!=held for x in rr):raise SystemExit("fold identity mismatch")
    keys=[(x["dataset"],x["filename"],x["canonical_source_id"]) for x in rr[0]["items"]]
    for x in rr[1:]:
        if [(q["dataset"],q["filename"],q["canonical_source_id"]) for q in x["items"]]!=keys:
            raise SystemExit("test item ordering mismatch across seeds")
    yy=np.asarray([q["target_normalized"] for q in rr[0]["items"]],float)
    pp=np.mean([[q["prediction"] for q in x["items"]] for x in rr],axis=0)
    result={
      "mode":mode,"held_corpus":held,"seeds":SEEDS,
      "train_rows":rr[0]["train_rows"],"test_rows":rr[0]["test_rows"],
      "test":metrics(yy,pp),
      "fit_info":[x["fit_info"] for x in rr],
      "per_seed_metrics":[x["metrics"] for x in rr],
    }
    Path(a.out).write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps(result,indent=2))
if __name__=="__main__":main()
