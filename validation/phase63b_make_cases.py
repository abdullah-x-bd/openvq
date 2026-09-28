#!/usr/bin/env python3
"""Create deterministic Phase 6.3B real-speech engineering transformations."""
from __future__ import annotations
import argparse,csv,hashlib,json,math,random,shutil
from pathlib import Path
import numpy as np
import soundfile as sf

def clamp(x):return np.clip(x,-0.999969,0.999969).astype(np.float32)

def sha256(path):
    h=hashlib.sha256()
    with open(path,"rb") as f:
        for b in iter(lambda:f.read(1<<20),b""):h.update(b)
    return h.hexdigest()

def read(path):
    x,sr=sf.read(path,dtype="float32",always_2d=True)
    return x.mean(axis=1).astype(np.float32),int(sr)

def write(path,x,sr):
    path.parent.mkdir(parents=True,exist_ok=True)
    sf.write(path,clamp(x),sr,subtype="PCM_16")

def active_center(x,sr,ms=500):
    n=max(1,min(len(x),int(sr*ms/1000)))
    if len(x)<=n:return len(x)//2
    e=np.convolve(np.square(x,dtype=np.float64),np.ones(n,dtype=np.float64),mode="valid")
    return int(np.argmax(e)+n//2)

def delay(x,sr,ms):
    return np.concatenate([np.zeros(int(sr*ms/1000),np.float32),x])

def noise(x,snr,seed):
    rng=np.random.default_rng(seed)
    rms=float(np.sqrt(np.mean(np.square(x,dtype=np.float64))))
    sigma=rms/(10**(snr/20))
    return clamp(x+rng.normal(0,sigma,len(x)).astype(np.float32))

def resample_linear(x,out_n):
    if out_n<=1:return np.asarray([x[0]],np.float32)
    old=np.linspace(0,1,len(x),endpoint=True)
    new=np.linspace(0,1,out_n,endpoint=True)
    return np.interp(new,old,x).astype(np.float32)

def roundtrip(x,sr,target):
    down=resample_linear(x,max(2,round(len(x)*target/sr)))
    return resample_linear(down,len(x))

def gain(x,db):return clamp(x*(10**(db/20)))

def silence_pad(x,sr,seconds,where):
    z=np.zeros(round(sr*seconds),np.float32)
    return np.concatenate([z,x]) if where=="prefix" else np.concatenate([x,z])

def clip_peak_fraction(x,frac):
    thr=max(1e-6,float(np.max(np.abs(x)))*frac)
    return np.clip(x,-thr,thr).astype(np.float32)

def dropout(x,sr,ms,center):
    y=x.copy();n=max(1,round(sr*ms/1000));b=max(0,center-n//2);e=min(len(y),b+n);y[b:e]=0;return y

def repeated_segment(x,sr,ms,center):
    y=x.copy();total=max(1,round(sr*ms/1000));unit=max(1,round(sr*.04))
    b=max(0,center-total//2);e=min(len(y),b+total)
    src_b=max(0,b-unit);seg=y[src_b:b].copy()
    if len(seg)<2:seg=y[b:min(len(y),b+unit)].copy()
    if len(seg)<2:return y
    reps=int(math.ceil((e-b)/len(seg)));y[b:e]=np.tile(seg,reps)[:e-b];return y

def clock_drift(x,ppm):
    return resample_linear(x,max(2,round(len(x)*(1+ppm*1e-6))))

def time_scale(x,pct):
    return resample_linear(x,max(2,round(len(x)*(1+pct/100))))

def main():
    ap=argparse.ArgumentParser();ap.add_argument("references");ap.add_argument("outdir");ap.add_argument("manifest");a=ap.parse_args()
    refs=list(csv.DictReader(open(a.references,newline="",encoding="utf-8")))
    out=Path(a.outdir);out.mkdir(parents=True,exist_ok=True);rows=[]
    def add(meta,ref_path,sr,family,level,label,y,kind):
        fn=f'{meta["reference_id"]}__{family}__{label}.wav'.replace("/","_")
        p=out/fn
        if y is None:
            if Path(ref_path).resolve()!=p.resolve():shutil.copyfile(ref_path,p)
        else:write(p,y,sr)
        rows.append({
          "dataset":"phase63b_real_speech","reference":str(Path(ref_path).resolve()),"degraded":str(p.resolve()),
          "filename":fn,"canonical_source_id":meta["reference_sha256"],"group_id":meta["reference_id"],
          "condition_id":f"{family}:{label}","family":family,"level":float(level),"label":label,
          "source_corpus":meta["source_corpus"],"language":meta["language"],
          "reference_id":meta["reference_id"],"reference_sha256":meta["reference_sha256"],
          "degraded_sha256":sha256(p),"check_class":kind,"placeholder_mos":1.0,
        })
    for ri,m in enumerate(refs):
        ref=m["reference"];x,sr=read(ref);center=active_center(x,sr)
        add(m,ref,sr,"identity",0,"clean",None,"numerical_invariance")
        for ms in (50,200,800):add(m,ref,sr,"delay",ms,f"{ms}ms",delay(x,sr,ms),"numerical_invariance")
        for snr in (60,40,20,10):add(m,ref,sr,"noise",60-snr,f"snr{snr}",noise(x,snr,63000+ri*100+snr),"physical_ordering")
        for hz in (16000,8000):
            if hz<sr:add(m,ref,sr,"resample_roundtrip",1/hz,f"{hz}hz",roundtrip(x,sr,hz),"diagnostic_ordering")
        for db in (-3,-12,-24):add(m,ref,sr,"attenuation",abs(db),f"{db}db",gain(x,db),"physical_ordering")
        add(m,ref,sr,"polarity",0,"inverted",-x,"numerical_invariance")
        for sec,where in ((.5,"prefix"),(1.0,"suffix")):
            add(m,ref,sr,"silence_padding",sec,f"{where}_{sec:g}s",silence_pad(x,sr,sec,where),"numerical_invariance")
        add(m,ref,sr,"silence_only",1,"same_duration",np.zeros_like(x),"diagnostic_absolute")
        for frac in (.80,.40,.15):add(m,ref,sr,"clipping",1-frac,f"peakfrac{frac:.2f}",clip_peak_fraction(x,frac),"physical_ordering")
        for ms in (20,80,320):add(m,ref,sr,"burst_loss",ms,f"{ms}ms",dropout(x,sr,ms,center),"physical_ordering")
        for ms in (80,240,480):add(m,ref,sr,"repeated_segment",ms,f"{ms}ms",repeated_segment(x,sr,ms,center),"physical_ordering")
        for ppm in (100,500,2000):add(m,ref,sr,"clock_drift",ppm,f"{ppm}ppm",clock_drift(x,ppm),"physical_ordering")
        for pct in (.5,2,8):add(m,ref,sr,"time_scale",pct,f"plus{pct:g}pct",time_scale(x,pct),"physical_ordering")
    fields=list(rows[0])
    with open(a.manifest,"w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)
    prov={"phase":"6.3B","rows":len(rows),"references":len(refs),
          "languages":sorted(set(r["language"] for r in rows)),
          "human_targets_used":False,"reserve_accessed":False,
          "transform_contract":"deterministic development-reference engineering transformations",
          "manifest_sha256":sha256(a.manifest)}
    (out/"case-provenance.json").write_text(json.dumps(prov,indent=2)+"\n")
    print(json.dumps(prov,indent=2))
if __name__=="__main__":main()
