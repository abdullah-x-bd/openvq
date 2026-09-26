#!/usr/bin/env python3
"""Convert a Phase 5.1 engineering JSON run to both feature schemas."""
import argparse,csv,json
from pathlib import Path
from phase51_feature_schema import LEGACY19,RICH_EXTRA,from_result

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("input");ap.add_argument("output")
    a=ap.parse_args()
    payload=json.loads(Path(a.input).read_text(encoding="utf-8"))
    out=[]
    for c in payload["cases"]:
        feats=from_result(c["result"])
        out.append({
            "family":c["family"],"level":c["level"],"label":c["label"],
            **{k:feats[k] for k in LEGACY19+RICH_EXTRA},
        })
    with open(a.output,"w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=list(out[0]));w.writeheader();w.writerows(out)
    print("engineering feature rows",len(out))
if __name__=="__main__":main()
