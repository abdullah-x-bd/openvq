#!/usr/bin/env python3
"""Export versioned Phase 6 native traces to deterministic NumPy caches."""
import argparse,csv,hashlib,json,os,subprocess
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import numpy as np
from phase6_feature_schema import RICH_V3,FRONTEND_ID

TRACE_SCHEMA="openvq-trace-v1-2026-09-26"

def content_hash(*arrays):
    h=hashlib.sha256()
    for a in arrays:
        a=np.ascontiguousarray(a)
        h.update(str(a.dtype).encode());h.update(str(a.shape).encode());h.update(a.tobytes())
    return h.hexdigest()

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("canonical_manifest");ap.add_argument("features");ap.add_argument("outdir")
    ap.add_argument("--trace-cli",default="./build/openvq_trace_cli")
    ap.add_argument("--jobs",type=int,default=max(1,min(4,os.cpu_count() or 1)))
    a=ap.parse_args()
    rows=list(csv.DictReader(open(a.canonical_manifest,newline="",encoding="utf-8")))
    feats=list(csv.DictReader(open(a.features,newline="",encoding="utf-8")))
    # Feature lookup uses dataset+filename, which is unique in the current registry.
    fm={(r["dataset"],r["filename"]):r for r in feats}
    outdir=Path(a.outdir);(outdir/"npz").mkdir(parents=True,exist_ok=True)

    def one(item):
        i,r=item
        fr=fm.get((r["dataset"],r["filename"]))
        if fr is None: raise RuntimeError(f"missing summary features for {r['dataset']} {r['filename']}")
        obj=json.loads(subprocess.check_output([a.trace_cli,r["reference"],r["degraded"]],text=True))
        if obj["frontend_id"]!=FRONTEND_ID:raise RuntimeError("frontend ID mismatch")
        if obj["trace_schema_id"]!=TRACE_SCHEMA:raise RuntimeError("trace schema mismatch")
        frames=obj["frames"];T=len(frames)
        ref=np.asarray([q["reference_bands_db"] for q in frames],np.float32)
        deg=np.asarray([q["degraded_bands_db"] for q in frames],np.float32)
        extras=np.asarray([[
            1.0 if q["reference_active"] else 0.0,
            1.0 if q["valid"] else 0.0,
            1.0 if q["unmatched"] else 0.0,
            q["alignment_confidence"],
            q["local_similarity"],
            q["reference_rms_db"],
            q["degraded_rms_db"],
            q["mapped_start_ms"]-q["start_ms"],
        ] for q in frames],np.float32)
        global_features=np.asarray([float(fr[k]) for k in RICH_V3],np.float32)
        h=content_hash(ref,deg,extras,global_features)
        p=outdir/"npz"/f"{i:06d}_{h[:16]}.npz"
        np.savez_compressed(p,reference_bands_db=ref,degraded_bands_db=deg,
            frame_extras=extras,global_features=global_features)
        return {
          **r,"trace_path":str(p),"trace_content_sha256":h,"trace_frames":T,
          "frontend_id":FRONTEND_ID,"trace_schema_id":TRACE_SCHEMA,
          "feature_schema_id":fr.get("feature_schema_id",""),
        }

    out=[]
    with ThreadPoolExecutor(max_workers=a.jobs) as pool:
        for n,r in enumerate(pool.map(one,enumerate(rows)),1):
            out.append(r)
            if n%25==0 or n==len(rows):print("traces",n,"/",len(rows),flush=True)
    path=outdir/"sequences.csv"
    with path.open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=list(out[0]));w.writeheader();w.writerows(out)
    manifest_hash=hashlib.sha256(path.read_bytes()).hexdigest()
    meta={"frontend_id":FRONTEND_ID,"trace_schema_id":TRACE_SCHEMA,
          "feature_order":RICH_V3,"rows":len(out),"manifest_sha256":manifest_hash}
    (outdir/"trace-provenance.json").write_text(json.dumps(meta,indent=2)+"\n")
    print(json.dumps(meta,indent=2))
if __name__=="__main__":main()
