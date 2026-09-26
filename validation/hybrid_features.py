#!/usr/bin/env python3
"""Extract phase-3 hybrid degradation features from a ViSQOL-augmented manifest."""
import argparse,csv,json,os,subprocess
from concurrent.futures import ThreadPoolExecutor

def clamp(x,lo=0.0,hi=1.0):return max(lo,min(hi,x))

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("manifest");ap.add_argument("output")
    ap.add_argument("--cli",default="./build/openvq_cli")
    ap.add_argument("--jobs",type=int,default=max(1,min(4,os.cpu_count() or 1)))
    a=ap.parse_args()
    with open(a.manifest,newline="",encoding="utf-8") as f: rows=list(csv.DictReader(f))
    def one(row):
        obj=json.loads(subprocess.check_output([a.cli,row["reference"],row["degraded"]],text=True))
        d=obj["dimensions"];q=obj["advanced"]
        return {
          "human_mos":float(row["human_mos"]),
          "condition_id":row.get("condition_id",""),
          "family":row.get("family",""),
          "filename":row.get("filename",""),
          "anchor_mos":float(obj["mos"]),
          "base":clamp((5-float(obj["base_mos"]))/4),
          "missing":clamp(float(obj["missing_disturbance"])),
          "added":clamp(float(obj["added_disturbance"])),
          "coloration":clamp((5-float(d["coloration"]))/4),
          "noisiness":clamp((5-float(d["noisiness"]))/4),
          "discontinuity":clamp((5-float(d["discontinuity"]))/4),
          "loudness":clamp((5-float(d["loudness"]))/4),
          "clipping":clamp(float(obj["clipping_ratio"])*40),
          "bad_section":clamp(float(obj["bad_section_fraction"])),
          "multi_resolution":clamp(1-float(q["multi_resolution_similarity"])),
          "temporal":clamp(1-float(q["temporal_envelope_similarity"])),
          "modulation":clamp(1-float(q["modulation_similarity"])),
          "asymmetry":clamp(float(q["asymmetric_disturbance"])),
          "tilt":clamp(float(q["spectral_tilt_error"])),
          "level":clamp(float(q["active_level_delta_db"])/18),
          "bad_interval":clamp(float(q["bad_interval_severity"])),
          "echo":clamp(float(q.get("echo_score",0))),
          "choppiness":clamp(float(q.get("choppiness_score",0))),
          "residual":clamp(float(q.get("residual_intrusion",0))),
          "visqol_speech":clamp((5-float(row["visqol_speech_mos"]))/4),
          "visqol_audio":clamp((5-float(row["visqol_audio_mos"]))/4),
        }
    out=[]
    with ThreadPoolExecutor(max_workers=a.jobs) as p:
        for i,x in enumerate(p.map(one,rows),1):
            out.append(x)
            if i%25==0:print("hybrid features",i,"/",len(rows),flush=True)
    with open(a.output,"w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=list(out[0].keys()));w.writeheader();w.writerows(out)
if __name__=="__main__":main()
