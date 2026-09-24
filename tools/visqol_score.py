#!/usr/bin/env python3
"""Run Google's separately installed ViSQOL in 48 kHz audio mode.

OpenVQ does not redistribute ViSQOL. ViSQOL is an optional Apache-2.0 input
expert and remains independently licensed by its upstream project.
"""
import argparse
import os
import wave
import numpy as np
from visqol import visqol_lib_py
from visqol.pb2 import visqol_config_pb2

def wav(path):
    with wave.open(path, "rb") as w:
        if w.getframerate()!=48000 or w.getsampwidth()!=2:
            raise SystemExit("visqol_score.py currently expects 48 kHz PCM16 WAV")
        ch = w.getnchannels()
        raw = np.frombuffer(w.readframes(w.getnframes()),dtype="<i2").astype(np.float64)/32768.0
    if ch>1:
        raw = raw.reshape(-1,ch).mean(axis=1)
    return raw

def main():
    p = argparse.ArgumentParser()
    p.add_argument("reference")
    p.add_argument("degraded")
    a = p.parse_args()
    cfg = visqol_config_pb2.VisqolConfig()
    cfg.audio.sample_rate = 48000
    cfg.options.use_speech_scoring = False
    cfg.options.svr_model_path = os.path.join(os.path.dirname(visqol_lib_py.__file__),"model","libsvm_nu_svr_model.txt")
    api = visqol_lib_py.VisqolApi()
    api.Create(cfg)
    print(f"{api.Measure(wav(a.reference),wav(a.degraded)).moslqo:.6f}")

if __name__=="__main__":
    main()
