#!/usr/bin/env python3
"""Train the preselected Phase 6 sequence architecture on all development evidence."""
import argparse,csv,json
from pathlib import Path
import torch
from phase6_train_sequence import Model,fit

FINAL_SEED=20260926

def main():
    ap=argparse.ArgumentParser();ap.add_argument("sequences");ap.add_argument("--selection",required=True)
    ap.add_argument("--outdir",required=True);ap.add_argument("--max-epochs",type=int,default=80);ap.add_argument("--device",default="cpu")
    a=ap.parse_args();rows=list(csv.DictReader(open(a.sequences,newline="",encoding="utf-8")))
    sel=json.loads(Path(a.selection).read_text());mode=sel["selected_mode"]
    device=torch.device(a.device);model,info=fit(rows,mode,FINAL_SEED,device,a.max_epochs)
    out=Path(a.outdir);out.mkdir(parents=True,exist_ok=True);state=out/f"{mode}-final-seed{FINAL_SEED}.pt"
    torch.save(model.state_dict(),state)
    result={"mode":mode,"seed":FINAL_SEED,"rows":len(rows),"fit_info":info,
            "state_file":str(state),"selection_report":str(Path(a.selection)),
            "status":"development candidate; external reserve untouched"}
    (out/"phase6e-final.json").write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps(result,indent=2))
if __name__=="__main__":main()
