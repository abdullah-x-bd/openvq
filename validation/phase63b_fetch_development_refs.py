#!/usr/bin/env python3
"""Select a small fixed multilingual real-speech diagnostic set from development archives.

This script retrieves only already-consumed development references. It never reads
subjective labels and never accesses the URGENT 2026 reserve.
"""
from __future__ import annotations
import argparse,csv,hashlib,io,json
from collections import defaultdict
from pathlib import Path
from remotezip import RemoteZip

CLEAN={"","none","clean","null","na","n/a"}

def sha256(path):
    h=hashlib.sha256()
    with open(path,"rb") as f:
        for b in iter(lambda:f.read(1<<20),b""):h.update(b)
    return h.hexdigest()

def norm(name):
    return name.replace("\\","/")

def base(name):
    return norm(name).rsplit("/",1)[-1]

def spread(items,n):
    items=sorted(items)
    if len(items)<n:raise RuntimeError(f"need {n} items, found {len(items)}")
    if n==1:return [items[len(items)//2]]
    idx=[round(i*(len(items)-1)/(n-1)) for i in range(n)]
    return [items[i] for i in idx]

def save_member(z,member,path):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_bytes(z.read(member))

def fetch_tcd(url,out,n=3):
    with RemoteZip(url) as z:
        names=z.namelist()
        refs=[x for x in names if base(x).lower().endswith(".wav") and base(x).startswith("R_")]
        selected=spread(refs,n)
        rows=[]
        for i,m in enumerate(selected,1):
            p=out/f"tcd_{i:02d}_{base(m)}"
            save_member(z,m,p)
            rows.append({"source_corpus":"TCD-VoIP","language":"English",
                         "source_archive_member":norm(m),"reference":str(p.resolve()),
                         "reference_sha256":sha256(p),
                         "pairing_evidence":"TCD clean R_ reference member selected directly from the already-used development archive"})
        return rows

def fetch_tmhint(url,out,n=3):
    with RemoteZip(url) as z:
        names=z.namelist()
        raw=[x for x in names if base(x).lower()=="raw_data.csv"]
        if len(raw)!=1:raise RuntimeError(f"expected one TMHINT raw_data.csv, found {raw}")
        text=z.read(raw[0]).decode("utf-8-sig")
        meta={}
        for r in csv.DictReader(io.StringIO(text)):
            stem=(r.get("file_name") or "").strip()
            if stem:meta[stem]=r
        wav_by_stem=defaultdict(list)
        for m in names:
            q=norm(m).lower()
            if q.endswith(".wav") and "/test/" in q:
                wav_by_stem[Path(base(m)).stem].append(m)
        clean_by_utt=defaultdict(list)
        for stem,r in meta.items():
            method=(r.get("method") or "").strip().lower()
            utt=(r.get("uttr") or "").strip()
            if utt and method in CLEAN and len(wav_by_stem.get(stem,[]))==1:
                clean_by_utt[utt].append(stem)
        candidates=[]
        for utt,stems in sorted(clean_by_utt.items()):
            if len(stems)==1:
                candidates.append((utt,stems[0],wav_by_stem[stems[0]][0]))
        chosen=spread(candidates,n)
        rows=[]
        for i,(utt,stem,m) in enumerate(chosen,1):
            p=out/f"tmhint_{i:02d}_{base(m)}"
            save_member(z,m,p)
            rows.append({"source_corpus":"TMHINT-QI-original","language":"Mandarin",
                         "source_archive_member":norm(m),"reference":str(p.resolve()),
                         "reference_sha256":sha256(p),"source_utterance_id":utt,
                         "pairing_evidence":"unique clean TMHINT test member for the utterance in raw_data.csv; labels not read"})
        return rows

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--tcd-url",required=True)
    ap.add_argument("--tmhint-url",required=True)
    ap.add_argument("--outdir",required=True)
    ap.add_argument("--out",required=True)
    a=ap.parse_args()
    out=Path(a.outdir);out.mkdir(parents=True,exist_ok=True)
    rows=fetch_tcd(a.tcd_url,out/"tcd",3)+fetch_tmhint(a.tmhint_url,out/"tmhint",3)
    for i,r in enumerate(rows,1):
        r["reference_id"]=f"phase63b-ref-{i:02d}"
    fields=sorted(set().union(*(r.keys() for r in rows)))
    with open(a.out,"w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)
    result={"phase":"6.3B","reserve_accessed":False,"human_labels_read":False,
            "references":len(rows),"languages":sorted(set(r["language"] for r in rows)),
            "corpora":sorted(set(r["source_corpus"] for r in rows)),
            "reference_manifest_sha256":sha256(a.out)}
    (out/"reference-provenance.json").write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps(result,indent=2))
if __name__=="__main__":main()
