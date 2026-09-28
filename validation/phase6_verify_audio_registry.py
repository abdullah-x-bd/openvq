#!/usr/bin/env python3
"""Verify recreated Phase 6 audio against the frozen Phase 6B registry."""
import argparse,csv,hashlib,json
from pathlib import Path

def sha(path):
    h=hashlib.sha256()
    with open(path,"rb") as f:
        for b in iter(lambda:f.read(1<<20),b""):h.update(b)
    return h.hexdigest()

def main():
    ap=argparse.ArgumentParser();ap.add_argument("manifest");a=ap.parse_args()
    rows=list(csv.DictReader(open(a.manifest,newline="",encoding="utf-8")))
    bad=[];seen={}
    for i,r in enumerate(rows,1):
        for kind,col,hashcol in (
            ("reference","reference","reference_sha256"),
            ("degraded","degraded","degraded_sha256"),
        ):
            p=r[col];expected=r[hashcol]
            if p in seen:got=seen[p]
            else:
                if not Path(p).is_file():
                    bad.append({"row":i,"kind":kind,"path":p,"reason":"missing"});continue
                got=sha(p);seen[p]=got
            if got!=expected:
                bad.append({"row":i,"kind":kind,"path":p,"expected":expected,"got":got,"reason":"sha256"})
    result={"rows":len(rows),"unique_files":len(seen),"failures":bad}
    print(json.dumps({"rows":len(rows),"unique_files":len(seen),"failure_count":len(bad),
                      "first_failures":bad[:5]},indent=2))
    if bad:raise SystemExit(2)
if __name__=="__main__":main()
