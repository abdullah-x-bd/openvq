#!/usr/bin/env python3
"""Materialize independent Phase 6 model-engineering waveform pairs."""
import argparse,csv
from pathlib import Path
from engineering_matrix import (SR,speech_like,write_wav,delay,dropout,repeated_dropouts,
    add_noise,one_pole_lowpass,clip_signal,gain)

def main():
    ap=argparse.ArgumentParser();ap.add_argument("outdir");ap.add_argument("manifest");a=ap.parse_args()
    out=Path(a.outdir);out.mkdir(parents=True,exist_ok=True);base=speech_like();ref=out/"reference.wav";write_wav(ref,base)
    cases=[("clean",0,"identity",base)]
    cases += [("delay",ms,f"{ms}ms",delay(base,SR,ms)) for ms in (40,120,250,500)]
    cases += [("dropout",ms,f"{ms}ms",dropout(base,SR,ms)) for ms in (20,80,320,640)]
    cases += [("dropout_count",n,f"{n}x80ms",repeated_dropouts(base,SR,80,n)) for n in (1,2,3,5)]
    cases += [("noise",50-snr,f"snr{snr}",add_noise(base,snr)) for snr in (40,20,10,0)]
    cases += [("lowpass",20000-c,f"{c}hz",one_pole_lowpass(base,SR,c)) for c in (18000,10000,4000,2200)]
    cases += [("clipping",1-t,f"thr{t}",clip_signal(base,t)) for t in (.95,.5,.25,.08)]
    mixes=[
      ("mild",add_noise(dropout(base,SR,20),30)),
      ("moderate",add_noise(dropout(one_pole_lowpass(base,SR,7000),SR,80),18)),
      ("severe",add_noise(dropout(one_pole_lowpass(gain(base,-8),SR,3400),SR,320),8)),
    ]
    cases += [("mixed",i,name,x) for i,(name,x) in enumerate(mixes,1)]
    rows=[]
    for i,(fam,level,label,x) in enumerate(cases):
        p=out/f"{i:03d}_{fam}_{label}.wav";write_wav(p,x)
        rows.append({"reference":str(ref.resolve()),"degraded":str(p.resolve()),"human_mos":5.0,
                     "group_id":"engineering","condition_id":fam,"family":fam,"filename":p.name,
                     "level":level,"label":label,"dataset":"engineering",
                     "canonical_source_id":"engineering-reference","target_normalized":1.0})
    with open(a.manifest,"w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    print("engineering waveform pairs",len(rows))
if __name__=="__main__":main()
