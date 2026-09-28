#!/usr/bin/env python3
"""Export Phase 6.3 Trace V3 timelines to deterministic NumPy caches."""
import argparse,csv,hashlib,json,os,subprocess
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import numpy as np
from phase63_feature_schema import RICH_V4,FRONTEND_ID,SCHEMA_ID

TRACE_SCHEMA="openvq-trace-v3-2026-09-29"
TRACE_IMPLEMENTATION_ID="openvq-trace-v3-transport-fallback-2026-09-29"

def content_hash(*arrays):
    h=hashlib.sha256()
    for a in arrays:
        a=np.ascontiguousarray(a);h.update(str(a.dtype).encode());h.update(str(a.shape).encode());h.update(a.tobytes())
    return h.hexdigest()

def main():
    ap=argparse.ArgumentParser();ap.add_argument("manifest");ap.add_argument("features");ap.add_argument("outdir")
    ap.add_argument("--trace-cli",default="./build/openvq_trace_cli")
    ap.add_argument("--jobs",type=int,default=max(1,min(4,os.cpu_count() or 1)))
    a=ap.parse_args();rows=list(csv.DictReader(open(a.manifest,newline="",encoding="utf-8")))
    feats=list(csv.DictReader(open(a.features,newline="",encoding="utf-8")))
    if len(rows)!=len(feats):raise SystemExit(f"manifest/features row mismatch {len(rows)} != {len(feats)}")
    fm={(r["filename"],r["reference"],r["degraded"]):r for r in feats}
    if len(fm)!=len(feats):raise SystemExit("duplicate feature identity")
    outdir=Path(a.outdir);(outdir/"npz").mkdir(parents=True,exist_ok=True)
    def one(item):
        i,r=item;key=(r["filename"],r["reference"],r["degraded"]);fr=fm.get(key)
        if fr is None:raise RuntimeError(f"missing feature row for {key}")
        obj=json.loads(subprocess.check_output([a.trace_cli,r["reference"],r["degraded"]],text=True))
        if obj["frontend_id"]!=FRONTEND_ID:raise RuntimeError("frontend mismatch")
        if obj["trace_schema_id"]!=TRACE_SCHEMA:raise RuntimeError("trace schema mismatch")
        if obj.get("trace_implementation_id")!=TRACE_IMPLEMENTATION_ID:raise RuntimeError("trace implementation mismatch")
        frames=obj["frames"];ref=np.asarray([q["reference_bands_db"] for q in frames],np.float32)
        deg=np.asarray([q["degraded_bands_db"] for q in frames],np.float32)
        extras=np.asarray([[1.0 if q["reference_active"] else 0.0,1.0 if q["valid"] else 0.0,
          1.0 if q["unmatched"] else 0.0,q["alignment_confidence"],q["local_similarity"],
          q["reference_rms_db"],q["degraded_rms_db"],q["mapped_start_ms"]-q["start_ms"]] for q in frames],np.float32)
        glob=np.asarray([float(fr[k]) for k in RICH_V4],np.float32);h=content_hash(ref,deg,extras,glob)
        p=outdir/"npz"/f"{i:06d}_{h[:16]}.npz";np.savez_compressed(p,reference_bands_db=ref,degraded_bands_db=deg,frame_extras=extras,global_features=glob)
        row=dict(r);row["dataset"]=fr["dataset"];row.update({"trace_path":str(p),"trace_content_sha256":h,"trace_frames":len(frames),
          "frontend_id":FRONTEND_ID,"trace_schema_id":TRACE_SCHEMA,"trace_implementation_id":TRACE_IMPLEMENTATION_ID,
          "feature_schema_id":SCHEMA_ID});return row
    out=[]
    with ThreadPoolExecutor(max_workers=a.jobs) as pool:
        for n,r in enumerate(pool.map(one,enumerate(rows)),1):
            out.append(r)
            if n%25==0 or n==len(rows):print("phase63 traces",n,"/",len(rows),flush=True)
    path=outdir/"sequences.csv";fields=[]
    for r in out:
        for k in r:
            if k not in fields:fields.append(k)
    with path.open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(out)
    meta={"frontend_id":FRONTEND_ID,"feature_schema_id":SCHEMA_ID,"trace_schema_id":TRACE_SCHEMA,
      "trace_implementation_id":TRACE_IMPLEMENTATION_ID,"feature_order":RICH_V4,"rows":len(out),
      "manifest_sha256":hashlib.sha256(path.read_bytes()).hexdigest()}
    (outdir/"trace-provenance.json").write_text(json.dumps(meta,indent=2)+"\n");print(json.dumps(meta,indent=2))
if __name__=="__main__":main()
