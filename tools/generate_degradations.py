#!/usr/bin/env python3
"""Deterministically apply telecom-like degradations to PCM16 mono/stereo WAV."""
import argparse
import array
import math
import random
import wave

def read_wav(path):
    with wave.open(path, "rb") as w:
        if w.getsampwidth() != 2:
            raise SystemExit("PCM16 WAV required")
        ch, sr = w.getnchannels(), w.getframerate()
        raw = array.array("h", w.readframes(w.getnframes()))
    if ch > 1:
        mono = array.array("h")
        for i in range(0, len(raw), ch):
            mono.append(int(sum(raw[i:i+ch]) / ch))
        raw = mono
    return sr, [x / 32768.0 for x in raw]

def write_wav(path, sr, x):
    y = array.array("h", [int(max(-1.0, min(0.999969, v))*32768) for v in x])
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(y.tobytes())

def lowpass(x, sr, hz):
    if not hz:
        return x
    a = math.exp(-2*math.pi*hz/sr)
    y = []
    z = 0.0
    for v in x:
        z = (1-a)*v + a*z
        y.append(z)
    return y

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("input")
    ap.add_argument("output")
    ap.add_argument("--gain-db", type=float, default=0.0)
    ap.add_argument("--clip", type=float, default=1.0)
    ap.add_argument("--dropout-start-ms", type=float)
    ap.add_argument("--dropout-duration-ms", type=float, default=0.0)
    ap.add_argument("--noise-snr-db", type=float)
    ap.add_argument("--lowpass-hz", type=float)
    ap.add_argument("--seed", type=int, default=1)
    a = ap.parse_args()
    sr,x = read_wav(a.input)
    g = 10**(a.gain_db/20)
    x = [v*g for v in x]
    x = lowpass(x,sr,a.lowpass_hz)
    if a.noise_snr_db is not None:
        rng = random.Random(a.seed)
        rms = math.sqrt(sum(v*v for v in x)/max(1,len(x)))
        sigma = rms/(10**(a.noise_snr_db/20))
        x = [v+rng.gauss(0,sigma) for v in x]
    if a.dropout_start_ms is not None:
        b = int(a.dropout_start_ms*sr/1000)
        e = b + int(a.dropout_duration_ms*sr/1000)
        for i in range(max(0,b),min(len(x),e)):
            x[i] = 0.0
    lim = max(0.01,min(1.0,a.clip))
    x = [max(-lim,min(lim,v)) for v in x]
    write_wav(a.output,sr,x)

if __name__=="__main__":
    main()
