#!/usr/bin/env python3
"""Build the Phase 6 canonical paired-data registry.

Canonical source identity is the SHA-256 of the exact reference waveform bytes.
This catches exact source reuse across dataset names and condition IDs.
"""
import argparse,csv,hashlib,json
from pathlib import Path
import yaml

def sha256(path):
    h=hashlib.sha256()
    with open(path,"rb") as f:
        for b in iter(lambda:f.read(1024*1024),b""):h.update(b)
    return h.hexdigest()

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--registry",required=True)
    ap.add_argument("--dataset",action="append",required=True,help="NAME=manifest.csv")
    ap.add_argument("--out",required=True)
    ap.add_argument("--splits-out",required=True)
    a=ap.parse_args()
    cfg=yaml.safe_load(Path(a.registry).read_text())
    specs=dict(x.split("=",1) for x in a.dataset)
    out=[]
    missing=[]
    for name,path in specs.items():
        if name not in cfg["datasets"]:raise SystemExit(f"dataset {name} absent from registry")
        dc=cfg["datasets"][name]
        rows=list(csv.DictReader(open(path,newline="",encoding="utf-8")))
        for idx,r in enumerate(rows):
            ref=Path(r["reference"]);deg=Path(r["degraded"])
            if not ref.is_file() or not deg.is_file():
                missing.append({"dataset":name,"row":idx,"reference":str(ref),"degraded":str(deg)})
                continue
            rh=sha256(ref);dh=sha256(deg)
            target=float(r[dc["target_field"]])
            norm=(target-1)/4 if dc["target_scale"]=="mos1to5" else target/100
            system=(r.get(dc.get("system_field","condition_id")) or r.get("family","")).strip()
            speaker=(r.get(dc.get("speaker_field","")) or "").strip() if dc.get("speaker_field") else ""
            out.append({
              "dataset":name,"ancestry":dc["ancestry"],"role":dc["role"],
              "protocol":dc["protocol"],"reference":str(ref),"degraded":str(deg),
              "reference_sha256":rh,"degraded_sha256":dh,
              "canonical_source_id":rh,"speaker_id":speaker,
              "system_id":system,"family":r.get("family",""),
              "condition_id":r.get("condition_id",""),
              "filename":r.get("filename",r.get("distorted_file","")),
              "target_raw":target,"target_normalized":norm,
              "listener_count":r.get("listener_count",r.get("listener_n","")),
            })
    if missing:
        raise SystemExit("missing audio in registry build: "+json.dumps(missing[:5]))
    Path(a.out).parent.mkdir(parents=True,exist_ok=True)
    with open(a.out,"w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=list(out[0]));w.writeheader();w.writerows(out)
    # Folds are defined by source hashes, not dataset labels.
    sources=sorted(set(r["canonical_source_id"] for r in out))
    folds={s:i%5 for i,s in enumerate(sources)}
    split={
      "schema_version":1,
      "grouping_unit":"exact reference waveform SHA-256",
      "source_count":len(sources),
      "folds":folds,
      "ancestry_rule":"a held ancestry excludes all rows with that ancestry",
    }
    Path(a.splits_out).write_text(json.dumps(split,indent=2)+"\n")
    print(json.dumps({
      "rows":len(out),"unique_sources":len(sources),
      "datasets":{d:sum(r["dataset"]==d for r in out) for d in sorted(specs)}
    },indent=2))
if __name__=="__main__":main()
