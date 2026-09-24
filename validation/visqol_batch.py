#!/usr/bin/env python3
"""Score a manifest with the pinned upstream Google ViSQOL v3.3.3 CLI."""
import argparse,csv,math,subprocess,tempfile
from pathlib import Path
import numpy as np
import soundfile as sf
from scipy.signal import resample_poly

def read(path):
    x,sr=sf.read(path,dtype="float64",always_2d=True)
    return x.mean(axis=1),sr
def resample(x,sr,target):
    if sr==target:return x
    g=math.gcd(int(sr),int(target))
    return resample_poly(x,target//g,sr//g)
def write(path,x,sr):
    sf.write(path,np.asarray(x,dtype=np.float32),sr,subtype="PCM_16")
def run_batch(binary,csv_path,out_path,speech):
    repo_root = Path(binary).resolve().parent.parent
    if speech:
        model = repo_root / "model" / "lattice_tcditugenmeetpackhref_ls2_nl60_lr12_bs2048_learn.005_ep2400_train1_7_raw.tflite"
    else:
        model = repo_root / "model" / "libsvm_nu_svr_model.txt"
    cmd=[
        binary,
        "--batch_input_csv",str(csv_path),
        "--results_csv",str(out_path),
        "--similarity_to_quality_model",str(model),
    ]
    if speech:cmd+=["--use_speech_mode"]
    subprocess.check_call(cmd, cwd=repo_root)
def load_scores(path):
    with open(path,newline="",encoding="utf-8") as f:
        return [float(r["moslqo"]) for r in csv.DictReader(f)]
def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("manifest");ap.add_argument("output")
    ap.add_argument("--binary",required=True)
    a=ap.parse_args()
    with open(a.manifest,newline="",encoding="utf-8") as f:rows=list(csv.DictReader(f))
    with tempfile.TemporaryDirectory(prefix="openvq-visqol-") as td:
        td=Path(td); speech_pairs=[]; audio_pairs=[]
        for i,row in enumerate(rows):
            r,rs=read(row["reference"]);d,ds=read(row["degraded"])
            r16=td/f"r16_{i}.wav";d16=td/f"d16_{i}.wav"
            r48=td/f"r48_{i}.wav";d48=td/f"d48_{i}.wav"
            write(r16,resample(r,rs,16000),16000);write(d16,resample(d,ds,16000),16000)
            write(r48,resample(r,rs,48000),48000);write(d48,resample(d,ds,48000),48000)
            speech_pairs.append((r16,d16));audio_pairs.append((r48,d48))
        def make_csv(path,pairs):
            with open(path,"w",newline="",encoding="utf-8") as f:
                w=csv.writer(f);w.writerow(["reference","degraded"])
                for r,d in pairs:w.writerow([r,d])
        sc=td/"speech.csv";ac=td/"audio.csv";so=td/"speech-out.csv";ao=td/"audio-out.csv"
        make_csv(sc,speech_pairs);make_csv(ac,audio_pairs)
        run_batch(a.binary,sc,so,True);run_batch(a.binary,ac,ao,False)
        ss=load_scores(so);aa=load_scores(ao)
    fields=list(rows[0].keys())+["visqol_speech_mos","visqol_audio_mos"]
    with open(a.output,"w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader()
        for row,s,x in zip(rows,ss,aa):
            row["visqol_speech_mos"]=s;row["visqol_audio_mos"]=x;w.writerow(row)
if __name__=="__main__":main()
