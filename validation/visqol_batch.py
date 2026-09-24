#!/usr/bin/env python3
"""Score a manifest with upstream Google ViSQOL v3.3.3.

Produces both the 16 kHz speech-mode lattice MOS and the 48 kHz audio-mode
SVR MOS. OpenVQ can then decide empirically whether either expert adds
out-of-dataset value.
"""
import argparse, csv, os, wave
import numpy as np
from scipy.signal import resample_poly
from visqol import visqol_lib_py
from visqol.pb2 import visqol_config_pb2

def read_wav(path):
    import soundfile as sf
    x,sr=sf.read(path,dtype="float64",always_2d=True)
    x=x.mean(axis=1)
    return x,sr

def resample(x,sr,target):
    if sr==target:return x
    import math
    g=math.gcd(sr,target)
    return resample_poly(x,target//g,sr//g).astype(np.float64)

def api_for(mode):
    cfg=visqol_config_pb2.VisqolConfig()
    if mode=="speech":
        cfg.audio.sample_rate=16000
        cfg.options.use_speech_scoring=True
        model="lattice_tcditugenmeetpackhref_ls2_nl60_lr12_bs2048_learn.005_ep2400_train1_7_raw.tflite"
    else:
        cfg.audio.sample_rate=48000
        cfg.options.use_speech_scoring=False
        model="libsvm_nu_svr_model.txt"
    cfg.options.svr_model_path=os.path.join(os.path.dirname(visqol_lib_py.__file__),"model",model)
    api=visqol_lib_py.VisqolApi(); api.Create(cfg)
    return api

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("manifest")
    ap.add_argument("output")
    args=ap.parse_args()
    speech=api_for("speech")
    audio=api_for("audio")
    with open(args.manifest,newline="",encoding="utf-8") as f:
        rows=list(csv.DictReader(f))
    fields=list(rows[0].keys())+["visqol_speech_mos","visqol_audio_mos"]
    with open(args.output,"w",newline="",encoding="utf-8") as g:
        w=csv.DictWriter(g,fieldnames=fields); w.writeheader()
        for i,row in enumerate(rows,1):
            r,rs=read_wav(row["reference"]); d,ds=read_wav(row["degraded"])
            r16=resample(r,rs,16000); d16=resample(d,ds,16000)
            r48=resample(r,rs,48000); d48=resample(d,ds,48000)
            row["visqol_speech_mos"]=float(speech.Measure(r16,d16).moslqo)
            row["visqol_audio_mos"]=float(audio.Measure(r48,d48).moslqo)
            w.writerow(row)
            if i%25==0: print("visqol",i,"/",len(rows),flush=True)

if __name__=="__main__": main()
