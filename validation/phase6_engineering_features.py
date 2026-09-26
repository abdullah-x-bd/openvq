#!/usr/bin/env python3
"""Convert Phase 6 engineering JSON to the rich-v3 feature schema."""
import argparse,csv,json
from pathlib import Path
from phase6_feature_schema import RICH_V3,from_result

def main():
    ap=argparse.ArgumentParser();ap.add_argument("input");ap.add_argument("output");a=ap.parse_args()
    payload=json.loads(Path(a.input).read_text())
    out=[]
    for case in payload["cases"]:
        f=from_result(case["result"])
        out.append({"family":case["family"],"level":case["level"],"label":case["label"],
                    **{k:f[k] for k in RICH_V3}})
    with open(a.output,"w",newline="",encoding="utf-8") as fh:
        w=csv.DictWriter(fh,fieldnames=list(out[0]));w.writeheader();w.writerows(out)
    print("phase6 engineering feature rows",len(out))
if __name__=="__main__":main()
