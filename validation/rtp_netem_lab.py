#!/usr/bin/env python3
"""Real UDP packet/jitter-buffer laboratory driven through Linux netem.

This is not a WAV-effect simulator. Speech is packetized into 20 ms UDP frames,
sent in real time through the host network stack, subjected to netem, received
with arrival timestamps, passed through a fixed playout buffer, and reconstructed
with repeat-last-frame PLC before OpenVQ scores the resulting audio.
"""
from __future__ import annotations
import argparse, array, json, math, socket, struct, subprocess, tempfile, threading, time, wave
from pathlib import Path

SR=16000
FRAME_MS=20
SAMPLES_PER_PACKET=SR*FRAME_MS//1000
HDR=struct.Struct("!HII")

def speech(seconds=5.0):
    out=[]
    for i in range(int(SR*seconds)):
        t=i/SR
        env=0.2+0.8*max(0.0,math.sin(2*math.pi*2.1*t))**0.7
        s=(0.24*math.sin(2*math.pi*185*t)
           +0.12*math.sin(2*math.pi*740*t)
           +0.065*math.sin(2*math.pi*2200*t)
           +0.035*math.sin(2*math.pi*5100*t))
        out.append(max(-0.98,min(0.98,s*env*1.5)))
    return out

def wav(path,x):
    a=array.array("h",[int(max(-.999,min(.999,v))*32767) for v in x])
    with wave.open(str(path),"wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes(a.tobytes())

def set_netem(spec):
    subprocess.run(["sudo","tc","qdisc","del","dev","lo","root"],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    if spec:
        subprocess.check_call(["sudo","tc","qdisc","add","dev","lo","root","netem",*spec])

def receiver(port,stop,packets):
    s=socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
    s.bind(("127.0.0.1",port))
    s.settimeout(0.1)
    while not stop.is_set():
        try:
            data,_=s.recvfrom(65535)
        except socket.timeout:
            continue
        now=time.monotonic()
        if len(data)<HDR.size: continue
        seq,ts,ssrc=HDR.unpack_from(data)
        packets.setdefault(seq,(now,data[HDR.size:]))
    s.close()

def run_network(x,spec,playout_ms,port):
    set_netem(spec)
    stop=threading.Event(); got={}
    th=threading.Thread(target=receiver,args=(port,stop,got),daemon=True); th.start()
    time.sleep(.05)
    s=socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
    pcm=array.array("h",[int(max(-.999,min(.999,v))*32767) for v in x])
    total=(len(pcm)+SAMPLES_PER_PACKET-1)//SAMPLES_PER_PACKET
    start=time.monotonic()
    for seq in range(total):
        target=start+seq*FRAME_MS/1000
        while True:
            remain=target-time.monotonic()
            if remain<=0: break
            time.sleep(min(remain,.002))
        frame=pcm[seq*SAMPLES_PER_PACKET:(seq+1)*SAMPLES_PER_PACKET]
        if len(frame)<SAMPLES_PER_PACKET:
            frame.extend([0]*(SAMPLES_PER_PACKET-len(frame)))
        s.sendto(HDR.pack(seq,seq*SAMPLES_PER_PACKET,0x12345678)+frame.tobytes(),("127.0.0.1",port))
    s.close()
    time.sleep(max(.7,playout_ms/1000+.3)); stop.set(); th.join(1)
    set_netem([])

    if not got:
        raise RuntimeError("no UDP packets received")
    first=min(t for t,_ in got.values())
    last_frame=array.array("h",[0]*SAMPLES_PER_PACKET)
    out=array.array("h")
    network_missing=0; late=0
    for seq in range(total):
        item=got.get(seq)
        deadline=first+playout_ms/1000+seq*FRAME_MS/1000
        if item is None:
            network_missing+=1
            frame=last_frame
        elif item[0] > deadline:
            late+=1
            frame=last_frame
        else:
            frame=array.array("h"); frame.frombytes(item[1])
            if len(frame)!=SAMPLES_PER_PACKET:
                frame=array.array("h",[0]*SAMPLES_PER_PACKET)
            last_frame=frame
        out.extend(frame)
    return [v/32768.0 for v in out[:len(x)]],{
        "sent":total,"received":len(got),
        "network_missing":network_missing,"late":late,
        "effective_loss_pct":100*(network_missing+late)/total,
    }

def score(cli,ref,deg):
    return json.loads(subprocess.check_output([cli,str(ref),str(deg)],text=True))

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--cli",default="./build/openvq_cli")
    ap.add_argument("--out",default="validation-network-results.json")
    args=ap.parse_args()
    x=speech()
    scenarios=[
        ("clean",[],80),
        ("loss1",["loss","1%"],80),
        ("loss3",["loss","3%"],80),
        ("loss5",["loss","5%"],80),
        ("loss10",["loss","10%"],80),
        ("jitter10",["delay","20ms","10ms","distribution","normal"],80),
        ("jitter35",["delay","20ms","35ms","distribution","normal"],80),
        ("reorder",["delay","20ms","10ms","reorder","25%","50%"],80),
        ("burst",["loss","gemodel","1%","30%","90%","0.5%"],80),
    ]
    results=[]
    with tempfile.TemporaryDirectory() as td:
        td=Path(td); ref=td/"ref.wav"; wav(ref,x)
        for idx,(name,spec,buffer_ms) in enumerate(scenarios):
            y,stats=run_network(x,spec,buffer_ms,51000+idx)
            deg=td/f"{name}.wav"; wav(deg,y)
            q=score(args.cli,ref,deg)
            results.append({"name":name,"netem":" ".join(spec) or "none","playout_ms":buffer_ms,
                            **stats,"mos":q["mos"],"dimensions":q["dimensions"],
                            "advanced":q.get("advanced",{})})
            print(name,stats,"MOS",q["mos"],flush=True)
    # Only enforce robust invariants, not exact MOS values.
    clean=next(r for r in results if r["name"]=="clean")
    if clean["mos"]<4.4: raise SystemExit("clean RTP path MOS unexpectedly low")
    if clean["effective_loss_pct"]>0: raise SystemExit("clean RTP path lost packets")
    loss=[next(r for r in results if r["name"]==n)["mos"] for n in ["loss1","loss3","loss5","loss10"]]
    if loss[-1] > loss[0]+0.15:
        raise SystemExit("10% loss scores materially better than 1% loss")
    Path(args.out).write_text(json.dumps({"results":results},indent=2),encoding="utf-8")

if __name__=="__main__":
    try: main()
    finally:
        subprocess.run(["sudo","tc","qdisc","del","dev","lo","root"],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
