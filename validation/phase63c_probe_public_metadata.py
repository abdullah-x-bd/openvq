#!/usr/bin/env python3
"""Inspect public URGENT Track-1 metadata without exposing subjective score fields."""
from __future__ import annotations
import argparse,json,urllib.parse,urllib.request
from pathlib import Path

DENY=("mos","label","score","rating","listener","cmos","preference")

def get_json(url):
    req=urllib.request.Request(url,headers={"User-Agent":"openvq-phase63c-preflight/1"})
    with urllib.request.urlopen(req,timeout=90) as r:
        return json.load(r)

def safe_key(k):
    q=k.lower()
    return not any(x in q for x in DENY)

def redact_row(row):
    return {k:v for k,v in row.items() if safe_key(k)}

def inspect_dataset(repo):
    enc=urllib.parse.quote(repo,safe="")
    splits=get_json(f"https://datasets-server.huggingface.co/splits?dataset={enc}")
    out={"repository":repo,"splits":[]}
    for s in splits.get("splits",[]):
        config=s["config"];split=s["split"]
        q=urllib.parse.urlencode({"dataset":repo,"config":config,"split":split})
        first=get_json("https://datasets-server.huggingface.co/first-rows?"+q)
        features=[x.get("name") for x in first.get("features",[]) if safe_key(x.get("name",""))]
        rows=[]
        for item in first.get("rows",[])[:100]:
            r=item.get("row",{})
            rows.append(redact_row(r))
        out["splits"].append({"config":config,"split":split,"safe_features":features,"safe_first_rows":rows})
    return out

def main():
    ap=argparse.ArgumentParser();ap.add_argument("--out",required=True);a=ap.parse_args()
    repos=["urgent-challenge/vmc2026-track1-meta","urgent-challenge/vmc2026-track1-test"]
    payload={"phase":"6.3C-public-metadata-preflight","subjective_repository_accessed":False,
             "score_fields_redacted":True,"datasets":[inspect_dataset(x) for x in repos]}
    Path(a.out).write_text(json.dumps(payload,indent=2,ensure_ascii=False)+"\n")
    print(json.dumps(payload,indent=2,ensure_ascii=False))
if __name__=="__main__":main()
