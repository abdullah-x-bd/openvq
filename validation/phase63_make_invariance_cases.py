#!/usr/bin/env python3
"""Build identity and exact-invariance property fixtures from primary development references."""
import argparse,csv,hashlib,json
from pathlib import Path
import numpy as np
import soundfile as sf
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def read(path):
    x,sr=sf.read(path,dtype="float32",always_2d=True);return x.mean(axis=1).astype(np.float32),int(sr)
def write(path,x,sr):
    path.parent.mkdir(parents=True,exist_ok=True);sf.write(path,np.clip(x,-.999969,.999969),sr,subtype="PCM_16")
def delay(x,sr,ms):return np.concatenate([np.zeros(round(sr*ms/1000),np.float32),x])
def pad(x,sr,sec,where):
    z=np.zeros(round(sr*sec),np.float32);return np.concatenate([z,x]) if where=="prefix" else np.concatenate([x,z])
def main():
    ap=argparse.ArgumentParser();ap.add_argument("references");ap.add_argument("outdir");ap.add_argument("manifest");a=ap.parse_args()
    refs=list(csv.DictReader(open(a.references,newline="",encoding="utf-8")));out=Path(a.outdir);out.mkdir(parents=True,exist_ok=True);rows=[]
    for r in refs:
        x,sr=read(r["reference"]);ref=Path(r["reference"]).resolve()
        cases=[("identity","identity",0.0,x),("invariance","delay200",1.0,delay(x,sr,200)),
          ("invariance","delay800",2.0,delay(x,sr,800)),("invariance","polarity",3.0,-x),
          ("invariance","silence_prefix_0p5s",4.0,pad(x,sr,.5,"prefix")),
          ("invariance","silence_suffix_1s",5.0,pad(x,sr,1.0,"suffix"))]
        for kind,label,level,y in cases:
            p=out/f'{r["reference_id"]}__{label}.wav';write(p,y,sr)
            rows.append({"dataset":"phase63_invariance_property","reference":str(ref),"degraded":str(p.resolve()),
              "filename":p.name,"canonical_source_id":r["reference_sha256"],"group_id":r["reference_id"],
              "condition_id":label,"family":"identity_invariance_property","level":level,"label":label,
              "property_kind":kind,"property_corpus":r["property_corpus"],"source_corpus":r["source_corpus"],
              "language":r["language"],"reference_id":r["reference_id"],"placeholder_mos":1.0,
              "target_normalized":0.0,"degraded_sha256":sha(p)})
    with open(a.manifest,"w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    prov={"phase":"6.3B-R1","purpose":"identity floor and exact transport/polarity/silence invariance constraints",
      "rows":len(rows),"references":len(refs),"human_mos_role":"none","identity_floor_raw":0.85,
      "invariance_margin_raw":0.05,"manifest_sha256":sha(a.manifest)}
    (out/"property-provenance.json").write_text(json.dumps(prov,indent=2)+"\n");print(json.dumps(prov,indent=2))
if __name__=="__main__":main()
