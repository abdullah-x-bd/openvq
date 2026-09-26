#!/usr/bin/env python3
"""Aggregate Phase 6E held-corpus results and freeze architecture selection."""
import argparse,json
from collections import defaultdict
from pathlib import Path

def main():
    ap=argparse.ArgumentParser();ap.add_argument("--report",action="append",required=True);ap.add_argument("--out",required=True);a=ap.parse_args()
    modes=defaultdict(dict)
    for p in a.report:
        r=json.loads(Path(p).read_text());m=r["mode"];h=r["held_corpus"];modes[m][h]=r
    expected={"nisqa_p501","nisqa_test_for","openace","tcd","tmhint"}
    summary={}
    for mode,by in modes.items():
        if set(by)!=expected:raise SystemExit(f"{mode}: held corpora {sorted(by)} != {sorted(expected)}")
        vals=[min(x["test"]["pearson"],x["test"]["spearman"]) for x in by.values()]
        summary[mode]={
          "by_held_corpus":by,
          "worst_held_corpus_correlation":min(vals),
          "mean_held_corpus_correlation":sum(vals)/len(vals),
          "worst_rmse_normalized":max(x["test"]["rmse_normalized"] for x in by.values()),
        }
    selected=max(summary,key=lambda m:(summary[m]["worst_held_corpus_correlation"],
                                       summary[m]["mean_held_corpus_correlation"],
                                       -summary[m]["worst_rmse_normalized"]))
    result={
      "experiment_id":"phase6e-sequence-loco-v1",
      "selection_rule":"maximize weakest held-corpus Pearson/Spearman, then mean held-corpus correlation, then lower worst normalized RMSE",
      "modes":summary,"selected_mode":selected,
      "selected_objective":{
        "worst_held_corpus_correlation":summary[selected]["worst_held_corpus_correlation"],
        "mean_held_corpus_correlation":summary[selected]["mean_held_corpus_correlation"],
        "worst_rmse_normalized":summary[selected]["worst_rmse_normalized"],
      },
      "urgent_consumed":False,
    }
    Path(a.out).write_text(json.dumps(result,indent=2)+"\n");print(json.dumps(result,indent=2))
if __name__=="__main__":main()
