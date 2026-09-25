#!/usr/bin/env python3
"""Extract native OpenVQ features for OpenACE using frozen Phase-3 expert scores."""
import argparse,csv,json,os,subprocess,tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import numpy as np
import soundfile as sf

def clamp(x,lo=0.0,hi=1.0):return max(lo,min(hi,float(x)))

def convert(src,dst):
    x,sr=sf.read(src,dtype="float64",always_2d=True)
    sf.write(dst,x.mean(axis=1).astype(np.float32),sr,subtype="PCM_16")

def main():
    ap=argparse.ArgumentParser();ap.add_argument("manifest");ap.add_argument("output")
    ap.add_argument("--cli",default="./build/openvq_cli");ap.add_argument("--jobs",type=int,default=4)
    a=ap.parse_args()
    rows=list(csv.DictReader(open(a.manifest,newline="",encoding="utf-8")))
    with tempfile.TemporaryDirectory(prefix="openvq-openace-phase4-") as td:
        td=Path(td);converted={}
        for r in rows:
            for k in ("reference","degraded"):
                if r[k] not in converted:converted[r[k]]=str(td/f"{len(converted):04d}.wav")
        for i,(src,dst) in enumerate(converted.items(),1):
            convert(src,dst)
            if i%48==0 or i==len(converted):print("PCM16",i,"/",len(converted),flush=True)
        def one(r):
            cmd=[a.cli,converted[r["reference"]],converted[r["degraded"]],
                 "--visqol-speech-score",r["visqol_speech_mos"],
                 "--visqol-audio-score",r["visqol_audio_mos"]]
            obj=json.loads(subprocess.check_output(cmd,text=True))
            d=obj["dimensions"];q=obj["advanced"]
            return {
              "speaker":r["speaker"],"emotion":r["emotion"],"codec":r["codec"],
              "filename":r["filename"],
              "human_mushra":float(r["distorted_mushra_rating"]),
              "polqa_mos":r.get("polqa_score",""),
              "published_visqol_mos":float(r["visqol_score"]),
              "phase3_mos":float(obj["mos"]),
              "base":clamp((5-float(obj["base_mos"]))/4),
              "missing":clamp(obj["missing_disturbance"]),
              "added":clamp(obj["added_disturbance"]),
              "coloration":clamp((5-float(d["coloration"]))/4),
              "noisiness":clamp((5-float(d["noisiness"]))/4),
              "discontinuity":clamp((5-float(d["discontinuity"]))/4),
              "loudness":clamp((5-float(d["loudness"]))/4),
              "clipping":clamp(float(obj["clipping_ratio"])*40),
              "bad_section":clamp(obj["bad_section_fraction"]),
              "multi_resolution":clamp(1-float(q["multi_resolution_similarity"])),
              "temporal":clamp(1-float(q["temporal_envelope_similarity"])),
              "modulation":clamp(1-float(q["modulation_similarity"])),
              "asymmetry":clamp(q["asymmetric_disturbance"]),
              "tilt":clamp(q["spectral_tilt_error"]),
              "level":clamp(float(q["active_level_delta_db"])/18),
              "bad_interval":clamp(q["bad_interval_severity"]),
              "echo":clamp(q.get("echo_score",0)),
              "choppiness":clamp(q.get("choppiness_score",0)),
              "residual":clamp(q.get("residual_intrusion",0)),
              "visqol_speech":clamp((5-float(r["visqol_speech_mos"]))/4),
              "visqol_audio":clamp((5-float(r["visqol_audio_mos"]))/4),
            }
        out=[]
        with ThreadPoolExecutor(max_workers=a.jobs) as pool:
            for i,x in enumerate(pool.map(one,rows),1):
                out.append(x)
                if i%24==0 or i==len(rows):print("features",i,"/",len(rows),flush=True)
    with open(a.output,"w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=list(out[0]));w.writeheader();w.writerows(out)

if __name__=="__main__":main()
