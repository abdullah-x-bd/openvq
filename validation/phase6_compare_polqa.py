#!/usr/bin/env python3
"""Paired Phase 6 OpenVQ/POLQA comparison on identical human-rated rows."""
import argparse,csv,json
from collections import defaultdict
from pathlib import Path
import numpy as np

def rmse(y,p):return float(np.sqrt(np.mean((np.asarray(p)-np.asarray(y))**2)))
def main():
    ap=argparse.ArgumentParser();ap.add_argument("openvq_scored");ap.add_argument("polqa_csv")
    ap.add_argument("--out",required=True);ap.add_argument("--margin",type=float,default=.10)
    ap.add_argument("--bootstrap",type=int,default=10000);ap.add_argument("--seed",type=int,default=20260926)
    a=ap.parse_args()
    oq={r["sample_id"]:r for r in csv.DictReader(open(a.openvq_scored,newline="",encoding="utf-8"))}
    pq={r["sample_id"]:r for r in csv.DictReader(open(a.polqa_csv,newline="",encoding="utf-8"))}
    ids=sorted(set(oq)&set(pq))
    if not ids:raise SystemExit("no identical sample_id overlap")
    rows=[]
    for i in ids:
        r=oq[i];p=pq[i]
        rows.append((i,r["group_id"],float(r["human_mos"]),float(r["openvq_mos"]),float(p["polqa_mos"])))
    y=[r[2] for r in rows];ov=[r[3] for r in rows];po=[r[4] for r in rows]
    delta=rmse(y,ov)-rmse(y,po)
    groups=defaultdict(list)
    for r in rows:groups[r[1]].append(r)
    keys=sorted(groups);rng=np.random.default_rng(a.seed);bd=[]
    for _ in range(a.bootstrap):
        kk=rng.choice(keys,len(keys),replace=True);s=[r for k in kk for r in groups[k]]
        yy=[r[2] for r in s];oo=[r[3] for r in s];pp=[r[4] for r in s]
        bd.append(rmse(yy,oo)-rmse(yy,pp))
    lo,hi=np.quantile(bd,[.025,.975])
    result={"n":len(rows),"rmse_openvq":rmse(y,ov),"rmse_polqa":rmse(y,po),
      "delta_rmse_openvq_minus_polqa":delta,"delta_95":[float(lo),float(hi)],
      "noninferiority_margin":a.margin,"noninferior":float(hi)<a.margin,
      "superiority_evidence":float(hi)<0.0,
      "cluster_unit":"source/utterance","bootstrap_resamples":a.bootstrap,
      "note":"Project statistical criterion only; does not establish ITU conformance."}
    Path(a.out).write_text(json.dumps(result,indent=2)+"\n");print(json.dumps(result,indent=2))
if __name__=="__main__":main()
