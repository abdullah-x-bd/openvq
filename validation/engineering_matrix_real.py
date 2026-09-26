#!/usr/bin/env python3
"""Locked real-speech engineering suite for Phase 5.1.

Unlike validation/engineering_matrix.py, this suite uses clean recordings from
the TCD corpus and is never supplied to the model fitter as inequality data.
It is an independent behavior check for the repaired measurement chain.
"""
import argparse,array,csv,json,math,random,subprocess,tempfile,wave
from collections import defaultdict
from pathlib import Path

def clamp(x,lo=-1.0,hi=1.0):return max(lo,min(hi,x))

def read_wav(path):
    with wave.open(str(path),"rb") as w:
        if w.getnchannels()!=1 or w.getsampwidth()!=2:
            raise SystemExit(f"real engineering suite expects mono PCM16: {path}")
        sr=w.getframerate()
        a=array.array("h");a.frombytes(w.readframes(w.getnframes()))
        return sr,[x/32768.0 for x in a]

def write_wav(path,samples,sr):
    a=array.array("h",[int(clamp(x,-0.999969,0.999969)*32768) for x in samples])
    with wave.open(str(path),"wb") as w:
        w.setnchannels(1);w.setsampwidth(2);w.setframerate(sr);w.writeframes(a.tobytes())

def delay(x,sr,ms):return [0.0]*int(sr*ms/1000)+list(x)
def gain(x,db):
    g=10**(db/20);return [clamp(v*g) for v in x]
def dropout(x,sr,ms,start_fraction=.45):
    y=list(x);n=int(sr*ms/1000);b=max(0,int(len(y)*start_fraction-n/2));e=min(len(y),b+n)
    for i in range(b,e):y[i]=0.0
    return y
def add_noise(x,snr,seed):
    rng=random.Random(seed);r=math.sqrt(sum(v*v for v in x)/max(1,len(x)))
    sigma=r/(10**(snr/20))
    return [clamp(v+rng.gauss(0,sigma)) for v in x]
def lowpass(x,sr,cutoff):
    a=math.exp(-2*math.pi*cutoff/sr);y=list(x)
    for _ in range(3):
        z=0;stage=[]
        for v in y:
            z=(1-a)*v+a*z;stage.append(z)
        y=stage
    return y

def run(cli,ref,deg):
    return json.loads(subprocess.check_output([cli,str(ref),str(deg)],text=True))

def spearman(xs,ys):
    def ranks(v):
        o=sorted(range(len(v)),key=lambda i:v[i]);r=[0.0]*len(v);i=0
        while i<len(o):
            j=i+1
            while j<len(o) and v[o[j]]==v[o[i]]:j+=1
            rr=(i+j-1)/2
            for k in range(i,j):r[o[k]]=rr
            i=j
        return r
    a,b=ranks(xs),ranks(ys);ma=sum(a)/len(a);mb=sum(b)/len(b)
    num=sum((x-ma)*(y-mb) for x,y in zip(a,b))
    den=math.sqrt(sum((x-ma)**2 for x in a)*sum((y-mb)**2 for y in b))
    return num/den if den else 0.0

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("manifest");ap.add_argument("--cli",default="./build/openvq_cli")
    ap.add_argument("--out",required=True);ap.add_argument("--references",type=int,default=6)
    a=ap.parse_args()
    rows=list(csv.DictReader(open(a.manifest,newline="",encoding="utf-8")))
    refs=sorted(set(r["reference"] for r in rows))
    # Deterministic spread across the available reference list.
    if len(refs)<a.references:raise SystemExit("not enough unique references")
    idx=[round(i*(len(refs)-1)/(a.references-1)) for i in range(a.references)]
    selected=[refs[i] for i in idx]

    results=[]
    with tempfile.TemporaryDirectory(prefix="openvq-real-eng-") as td:
        td=Path(td)
        for ri,ref_name in enumerate(selected):
            sr,x=read_wav(ref_name)
            rp=td/f"ref_{ri}.wav";write_wav(rp,x,sr)
            cases=[
                ("identity",0,"clean",x),
                *[("delay",ms,f"{ms}ms",delay(x,sr,ms)) for ms in [40,120,250,500]],
                *[("dropout",ms,f"{ms}ms",dropout(x,sr,ms)) for ms in [20,80,240,600]],
                *[("noise",-snr,f"snr{snr}",add_noise(x,snr,1000+ri)) for snr in [35,25,15,8]],
                *[("lowpass",-hz,f"{hz}hz",lowpass(x,sr,min(hz,sr*.45))) for hz in [14000,9000,5000,3200]],
                *[("attenuation",db,f"{db}db",gain(x,db)) for db in [-3,-9,-18,-30]],
            ]
            for ci,(fam,level,label,y) in enumerate(cases):
                dp=td/f"d_{ri}_{ci}.wav";write_wav(dp,y,sr)
                obj=run(a.cli,rp,dp)
                results.append({
                    "reference_index":ri,"reference_name":Path(ref_name).name,
                    "family":fam,"level":level,"label":label,
                    "mos":float(obj["mos"]),
                    "confidence":float(obj["confidence"]),
                    "lost_active_speech_fraction":float(obj.get("lost_active_speech_fraction",0)),
                    "alignment_confidence":float(obj.get("alignment_confidence",0)),
                })

    failures=[];reports={}
    for ri in range(len(selected)):
        rr=[x for x in results if x["reference_index"]==ri]
        clean=next(x["mos"] for x in rr if x["family"]=="identity")
        if clean<4.4:failures.append(f"reference {ri} identity {clean:.3f} < 4.4")
        delay_rows=[x for x in rr if x["family"]=="delay"]
        dd=max(abs(x["mos"]-clean) for x in delay_rows)
        if dd>0.20+1e-9:failures.append(f"reference {ri} delay delta {dd:.3f} > 0.20")

    for fam in ["dropout","noise","lowpass","attenuation"]:
        rr=[x for x in results if x["family"]==fam]
        by_ref=defaultdict(list)
        for x in rr:by_ref[x["reference_index"]].append(x)
        fam_rep={}
        for ri,xs in by_ref.items():
            xs=sorted(xs,key=lambda x:x["level"])
            rho=spearman([x["level"] for x in xs],[x["mos"] for x in xs])
            # Levels are encoded so larger = more severe for dropout and
            # attenuation, while negative SNR/cutoff makes larger = more severe.
            fam_rep[str(ri)]={"rho":rho,"rows":xs}
            if rho>-0.20:
                failures.append(f"{fam} reference {ri} not negatively associated with severity: {rho:.3f}")
        reports[fam]=fam_rep

    payload={
      "suite":"phase5.1-real-speech-engineering-v1",
      "reference_count":len(selected),
      "reference_names":[Path(x).name for x in selected],
      "criteria":{
        "identity_mos_min":4.4,
        "pure_delay_max_abs_delta_mos":0.20,
        "severity_spearman_max":-0.20,
      },
      "reports":reports,"rows":results,"failures":failures,
    }
    Path(a.out).write_text(json.dumps(payload,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({k:payload[k] for k in ["suite","reference_count","criteria","failures"]},indent=2))
    if failures:raise SystemExit(1)

if __name__=="__main__":main()
