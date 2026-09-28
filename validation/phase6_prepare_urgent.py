#!/usr/bin/env python3
"""Prepare the frozen full-reference URGENT 2026 ACR reserve after model freeze."""
import argparse,csv,hashlib,json
from pathlib import Path
import numpy as np
import soundfile as sf
from datasets import load_dataset

def sha(p):
    h=hashlib.sha256()
    with open(p,"rb") as f:
        for b in iter(lambda:f.read(1<<20),b""):h.update(b)
    return h.hexdigest()
def audio_array(audio):
    if hasattr(audio,"get_all_samples"):
        x=audio.get_all_samples()
        data=x.data
        if hasattr(data,"cpu"):data=data.cpu().numpy()
        data=np.asarray(data)
        if data.ndim>1:data=data.mean(axis=0)
        return data.astype("float32"),int(x.sample_rate)
    if isinstance(audio,dict):
        arr=np.asarray(audio["array"])
        if arr.ndim>1:arr=arr.mean(axis=0)
        return arr.astype("float32"),int(audio["sampling_rate"])
    raise RuntimeError(f"unsupported HF audio object {type(audio)}")
def main():
    ap=argparse.ArgumentParser();ap.add_argument("--reference-map",required=True)
    ap.add_argument("--expected-map-sha256",required=True);ap.add_argument("--outdir",required=True)
    ap.add_argument("--output",required=True)
    a=ap.parse_args();mp=Path(a.reference_map)
    got=sha(mp)
    if got!=a.expected_map_sha256:raise SystemExit(f"reference map hash mismatch {got}")
    refs={}
    for r in csv.DictReader(mp.open(newline="",encoding="utf-8")):
        p=Path(r["reference"])
        if not p.is_absolute():p=(mp.parent/p).resolve()
        if not p.is_file():raise SystemExit(f"missing reference {p}")
        refs[r["utterance_id"]]=p
    ds=load_dataset("urgent-challenge/urgent2026-sqa","acr",split="test")
    outdir=Path(a.outdir);audio_dir=outdir/"degraded";audio_dir.mkdir(parents=True,exist_ok=True)
    rows=[];excluded=[]
    for r in ds:
        if not bool(r["is_simulated"]):continue
        uid=str(r["utterance_id"]);ref=refs.get(uid)
        if ref is None:
            excluded.append({"sample_id":r["sample_id"],"utterance_id":uid,"reason":"no_verified_reference"});continue
        arr,sr=audio_array(r["audio"]);deg=audio_dir/(str(r["sample_id"])+".wav");sf.write(deg,arr,sr,subtype="PCM_16")
        rows.append({"sample_id":r["sample_id"],"reference":str(ref),"degraded":str(deg.resolve()),
          "human_mos":float(r["mos"]),"group_id":uid,"condition_id":str(r["system_id"]),
          "system_id":str(r["system_id"]),"speaker_id":str(r["speaker_id"]),
          "language":str(r["language"]),"family":"URGENT2026_ACR_SIMULATED",
          "filename":deg.name,"listener_count":len(r["listener_scores"])})
    if not rows:raise SystemExit("no verified full-reference URGENT rows")
    with open(a.output,"w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    with open(outdir/"exclusions.csv","w",newline="",encoding="utf-8") as f:
        fields=["sample_id","utterance_id","reason"];w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(excluded)
    print(json.dumps({"paired_rows":len(rows),"excluded_simulated":len(excluded),
      "unique_sources":len(set(r["group_id"] for r in rows)),"reference_map_sha256":got},indent=2))
if __name__=="__main__":main()
