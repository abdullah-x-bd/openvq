#!/usr/bin/env python3
"""Codec encode/decode laboratory using real FFmpeg codec implementations."""
from __future__ import annotations
import argparse, array, json, math, subprocess, tempfile, wave
from pathlib import Path

SR=48000

def speech(seconds=6):
    x=[]
    for i in range(SR*seconds):
        t=i/SR
        env=0.25+0.75*max(0.0,math.sin(2*math.pi*2.4*t))**0.7
        s=(.20*math.sin(2*math.pi*170*t)+.13*math.sin(2*math.pi*690*t)
           +.075*math.sin(2*math.pi*2600*t)+.045*math.sin(2*math.pi*6200*t)
           +.025*math.sin(2*math.pi*12000*t))
        x.append(max(-.98,min(.98,1.65*env*s)))
    return x

def write(path,x,sr=SR):
    a=array.array("h",[int(max(-.999,min(.999,v))*32767) for v in x])
    with wave.open(str(path),"wb") as w:
        w.setnchannels(1);w.setsampwidth(2);w.setframerate(sr);w.writeframes(a.tobytes())

def sh(cmd):
    subprocess.check_call(cmd,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)

def score(cli,ref,deg):
    return json.loads(subprocess.check_output([cli,str(ref),str(deg)],text=True))

def transcode(inp,encoded,decoded,encode_args,input_args=None):
    sh(["ffmpeg","-nostdin","-y","-loglevel","error","-i",str(inp),*encode_args,str(encoded)])
    sh(["ffmpeg","-nostdin","-y","-loglevel","error",*(input_args or []),"-i",str(encoded),
        "-ac","1","-ar",str(SR),"-c:a","pcm_s16le",str(decoded)])

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--cli",default="./build/openvq_cli")
    ap.add_argument("--out",default="codec-results.json")
    args=ap.parse_args()
    results=[]
    with tempfile.TemporaryDirectory() as td:
        td=Path(td); ref=td/"ref.wav"; write(ref,speech())
        clean=score(args.cli,ref,ref)
        results.append({"codec":"pcm48","setting":"clean","mos":clean["mos"],"result":clean})

        cases=[
            ("g711","mulaw",["-ac","1","-ar","8000","-c:a","pcm_mulaw"],".wav",None),
            ("g711","alaw",["-ac","1","-ar","8000","-c:a","pcm_alaw"],".wav",None),
            ("g722","64k",["-ac","1","-ar","16000","-c:a","g722"],".g722",["-f","g722","-ar","16000"]),
            ("opus","8k",["-ac","1","-ar","48000","-c:a","libopus","-b:a","8k","-vbr","off"],".ogg",None),
            ("opus","12k",["-ac","1","-ar","48000","-c:a","libopus","-b:a","12k","-vbr","off"],".ogg",None),
            ("opus","24k",["-ac","1","-ar","48000","-c:a","libopus","-b:a","24k","-vbr","off"],".ogg",None),
            ("opus","48k",["-ac","1","-ar","48000","-c:a","libopus","-b:a","48k","-vbr","off"],".ogg",None),
        ]
        for idx,(codec,setting,enc_args,suffix,input_args) in enumerate(cases):
            enc=td/f"c{idx}{suffix}"; dec=td/f"c{idx}.wav"
            try:
                transcode(ref,enc,dec,enc_args,input_args)
                q=score(args.cli,ref,dec)
                results.append({"codec":codec,"setting":setting,"available":True,"mos":q["mos"],"result":q})
                print(codec,setting,q["mos"],flush=True)
            except subprocess.CalledProcessError as e:
                results.append({"codec":codec,"setting":setting,"available":False,"error":str(e)})
                print("unavailable",codec,setting,flush=True)

        # A real two-stage transcode chain.
        op=td/"stage1.ogg"; opwav=td/"stage1.wav"
        transcode(ref,op,opwav,["-ac","1","-ar","48000","-c:a","libopus","-b:a","12k"],".ogg" if False else None)
        mu=td/"stage2.wav"; final=td/"stage2-dec.wav"
        transcode(opwav,mu,final,["-ac","1","-ar","8000","-c:a","pcm_mulaw"],None)
        q=score(args.cli,ref,final)
        results.append({"codec":"transcode","setting":"opus12k_to_g711u","available":True,"mos":q["mos"],"result":q})

    available=[r for r in results if r.get("available",True)]
    if results[0]["mos"]<4.5: raise SystemExit("identity score unexpectedly low")
    Path(args.out).write_text(json.dumps({"results":results},indent=2),encoding="utf-8")

if __name__=="__main__": main()
