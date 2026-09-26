#!/usr/bin/env python3
"""Evaluate one Phase 6 sequence architecture on one completely held corpus."""
import argparse,csv,json
from pathlib import Path
import numpy as np
import torch
from phase6_train_sequence import SEEDS,MODES,fit,predict,metrics

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("sequences")
    ap.add_argument("--mode",required=True,choices=MODES)
    ap.add_argument("--held",required=True)
    ap.add_argument("--out",required=True)
    ap.add_argument("--device",default="cpu")
    ap.add_argument("--max-epochs",type=int,default=80)
    a=ap.parse_args()
    torch.set_num_threads(max(1,min(2,torch.get_num_threads())))
    rows=list(csv.DictReader(open(a.sequences,newline="",encoding="utf-8")))
    train=[r for r in rows if r["dataset"]!=a.held]
    test=[r for r in rows if r["dataset"]==a.held]
    if not train or not test:raise SystemExit("empty train/test split")
    preds=[];fits=[]
    for seed in SEEDS:
        print("fit",a.mode,"held",a.held,"seed",seed,flush=True)
        m,info=fit(train,a.mode,seed,torch.device(a.device),a.max_epochs)
        preds.append(predict(m,test,torch.device(a.device)))
        fits.append(info)
    pred=np.mean(preds,axis=0)
    yy=np.asarray([float(r["target_normalized"]) for r in test])
    result={
      "mode":a.mode,"held_corpus":a.held,"seeds":SEEDS,
      "train_rows":len(train),"test_rows":len(test),
      "test":metrics(yy,pred),"fit_info":fits,
      "per_seed_metrics":[metrics(yy,p) for p in preds],
    }
    Path(a.out).parent.mkdir(parents=True,exist_ok=True)
    Path(a.out).write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps(result,indent=2))
if __name__=="__main__":main()
