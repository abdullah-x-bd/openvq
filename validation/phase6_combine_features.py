#!/usr/bin/env python3
"""Combine Phase 6 feature tables while preserving canonical source metadata."""
import argparse,csv
from pathlib import Path

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--input",action="append",required=True)
    ap.add_argument("--output",required=True)
    a=ap.parse_args()
    rows=[]
    fields=[]
    for path in a.input:
        rr=list(csv.DictReader(open(path,newline="",encoding="utf-8")))
        if not rr:continue
        for k in rr[0]:
            if k not in fields:fields.append(k)
        rows.extend(rr)
    if not rows:raise SystemExit("no feature rows")
    Path(a.output).parent.mkdir(parents=True,exist_ok=True)
    with open(a.output,"w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=fields,extrasaction="ignore");w.writeheader()
        for r in rows:w.writerow({k:r.get(k,"") for k in fields})
    print("combined feature rows",len(rows))
if __name__=="__main__":main()
