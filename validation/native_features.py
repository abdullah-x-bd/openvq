#!/usr/bin/env python3
"""Extract the native OpenVQ feature vector from a full-reference manifest."""
import argparse,csv,json,os,subprocess
from concurrent.futures import ThreadPoolExecutor

def clamp(x,lo=0.0,hi=1.0):
    return max(lo,min(hi,float(x)))

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("manifest");ap.add_argument("output")
    ap.add_argument("--cli",default="./build/openvq_cli")
    ap.add_argument("--jobs",type=int,default=max(1,min(4,os.cpu_count() or 1)))
    a=ap.parse_args()
    rows=list(csv.DictReader(open(a.manifest,newline="",encoding="utf-8")))
    def one(r):
        obj=json.loads(subprocess.check_output([a.cli,r["reference"],r["degraded"]],text=True))
        d=obj["dimensions"];q=obj["advanced"]
        out={
          "human_mos":float(r["human_mos"]),
          "group_id":r.get("group_id",""),
          "condition_id":r.get("condition_id",""),
          "family":r.get("family",""),
          "filename":r.get("filename",""),
          "anchor_mos":float(obj["mos"]),
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
        }
        return out
    out=[]
    with ThreadPoolExecutor(max_workers=a.jobs) as p:
        for i,row in enumerate(p.map(one,rows),1):
            out.append(row)
            if i%40==0 or i==len(rows):
                print("native features",i,"/",len(rows),flush=True)
    with open(a.output,"w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=list(out[0].keys()));w.writeheader();w.writerows(out)
if __name__=="__main__":main()
