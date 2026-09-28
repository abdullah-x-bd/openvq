#!/usr/bin/env python3
"""Apply the historical scoped engineering gate to a scored Phase 6.3B-R1 table."""
import argparse,csv,json
from pathlib import Path
SCOPED={"dropout","dropout_count","noise","lowpass","clipping","mixed"}
def main():
    ap=argparse.ArgumentParser();ap.add_argument("scored");ap.add_argument("--out",required=True);a=ap.parse_args()
    rows=list(csv.DictReader(open(a.scored,newline="",encoding="utf-8")));fail=[];clean=float(next(r["openvq_mos"] for r in rows if r["family"]=="clean"))
    if clean<4.4:fail.append(f"identity MOS {clean:.3f}<4.4")
    delay=[float(r["openvq_mos"]) for r in rows if r["family"]=="delay"];dd=max(abs(x-clean) for x in delay)
    if dd>.20:fail.append(f"pure delay max delta {dd:.3f}>0.20")
    fam={}
    for name in sorted(SCOPED):
        rr=sorted([r for r in rows if r["family"]==name],key=lambda z:float(z["level"]))
        n=sum(float(b["openvq_mos"])>float(x["openvq_mos"])+.12 for x,b in zip(rr,rr[1:]))
        fam[name]={"rows":[{"level":float(r["level"]),"label":r["label"],"mos":float(r["openvq_mos"])} for r in rr],"violations_gt_0.12_mos":n}
        if n:fail.append(f"{name}:{n} reversals")
    result={"phase":"6.3B-R1","identity_mos":clean,"delay_max_abs_delta_mos":dd,"scoped_monotonic":fam,"failures":fail,"passes":not fail,
      "claim_boundary":"historical engineering development gate, not untouched evidence"}
    Path(a.out).write_text(json.dumps(result,indent=2)+"\n");print(json.dumps(result,indent=2))
    if fail:raise SystemExit(2)
if __name__=="__main__":main()
