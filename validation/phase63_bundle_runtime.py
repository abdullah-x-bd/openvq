#!/usr/bin/env python3
"""Bundle-aware Phase 6.3 inference for the frozen Phase 6.2G candidate."""
from __future__ import annotations
import csv,hashlib,json,math
from pathlib import Path
import numpy as np
import onnxruntime as ort

EXPECTED={
  "bundle_schema":"openvq-phase62g-clipping-regularized-ensemble-v1",
  "phase":"6.2G",
  "frontend_id":"openvq-frontend-phase6a-2026-09-26-v1",
  "feature_schema_id":"openvq-rich-v3-2026-09-26-v1",
  "trace_schema_id":"openvq-trace-v2-2026-09-27",
  "trace_implementation_id":"openvq-trace-spectral-v2-fft-corrected-2026-09-27",
  "model_mode":"learned_bands_padding_safe_clipreg",
  "source_commit":"9c59fec790e0490c22b363474dd75b476f891f8f",
  "seeds":[20260926,20260927,20260928],
  "ensemble_rule":"arithmetic mean of raw quality predictions, then clamp to [0,1]",
  "pipeline_id":"openvq-phase62g-749eaa80ea0a796cc15c",
}

def sha256(path):
    h=hashlib.sha256()
    with open(path,"rb") as f:
        for block in iter(lambda:f.read(1<<20),b""):h.update(block)
    return h.hexdigest()

def _require(cond,msg):
    if not cond:raise ValueError(msg)

def load_bundle(bundle_path,candidate_dir,expected_bundle_sha256=None):
    bundle_path=Path(bundle_path);candidate_dir=Path(candidate_dir)
    if expected_bundle_sha256:
        got=sha256(bundle_path)
        _require(got==expected_bundle_sha256,f"bundle.json sha256 mismatch {got} != {expected_bundle_sha256}")
    b=json.loads(bundle_path.read_text())
    for k,v in EXPECTED.items():
        _require(b.get(k)==v,f"bundle field {k} mismatch: {b.get(k)!r} != {v!r}")
    models=b.get("onnx")
    _require(isinstance(models,list) and len(models)==3,"bundle must contain exactly three ONNX entries")
    expected_names=[f"clipreg-seed{s}.onnx" for s in EXPECTED["seeds"]]
    names=[x.get("file") for x in models]
    _require(names==expected_names,f"ONNX order/name mismatch: {names} != {expected_names}")
    model_paths=[]
    for ent in models:
        _require(set(ent)=={"file","sha256"},f"unexpected ONNX manifest fields for {ent.get('file')}")
        p=candidate_dir/ent["file"]
        _require(p.is_file(),f"missing model {p}")
        got=sha256(p)
        _require(got==ent["sha256"],f"model hash mismatch for {p.name}: {got} != {ent['sha256']}")
        model_paths.append(p)
    return b,model_paths

def trace_tensors(path):
    z=np.load(path)
    required={"reference_bands_db","degraded_bands_db","frame_extras","global_features"}
    _require(required.issubset(z.files),f"trace {path} missing arrays {sorted(required-set(z.files))}")
    ref=np.clip((z["reference_bands_db"].astype("float32")+120)/140,0,1)
    deg=np.clip((z["degraded_bands_db"].astype("float32")+120)/140,0,1)
    ext=z["frame_extras"].astype("float32").copy()
    _require(ref.ndim==2 and deg.shape==ref.shape and ref.shape[1]==64,"invalid band tensor shape")
    _require(ext.ndim==2 and len(ext)==len(ref) and ext.shape[1]>=8,"invalid frame_extras shape")
    ext[:,5]=np.clip((ext[:,5]+120)/140,0,1)
    ext[:,6]=np.clip((ext[:,6]+120)/140,0,1)
    ext[:,7]=np.clip(ext[:,7]/500,-4,4)
    glob=z["global_features"].astype("float32")
    _require(np.all(np.isfinite(ref)) and np.all(np.isfinite(deg)) and np.all(np.isfinite(ext)) and np.all(np.isfinite(glob)),
             f"non-finite trace values in {path}")
    mask=np.ones(len(ref),np.float32)
    return [x[None] for x in (ref,deg,ext,mask,glob)]

def validate_sequence_row(row):
    _require(row.get("trace_schema_id")==EXPECTED["trace_schema_id"],
             f"wrong trace schema for {row.get('filename')}: {row.get('trace_schema_id')}")
    _require(row.get("trace_implementation_id")==EXPECTED["trace_implementation_id"],
             f"wrong trace implementation for {row.get('filename')}: {row.get('trace_implementation_id')}")
    _require(Path(row["trace_path"]).is_file(),f"missing trace {row.get('trace_path')}")

class FrozenEnsemble:
    def __init__(self,bundle_path,candidate_dir,expected_bundle_sha256=None):
        self.bundle,self.model_paths=load_bundle(bundle_path,candidate_dir,expected_bundle_sha256)
        self.sessions=[ort.InferenceSession(str(p),providers=["CPUExecutionProvider"]) for p in self.model_paths]
        self.input_names=[[x.name for x in s.get_inputs()] for s in self.sessions]
        _require(all(len(n)==5 for n in self.input_names),"unexpected ONNX input count")

    def predict_arrays(self,arr):
        raws=[]
        for sess,names in zip(self.sessions,self.input_names):
            q=float(sess.run(None,{n:x for n,x in zip(names,arr)})[0].reshape(-1)[0])
            _require(math.isfinite(q),"non-finite ONNX output")
            raws.append(q)
        raw=float(np.mean(raws))
        clipped=float(min(1.0,max(0.0,raw)))
        return raws,raw,clipped,1.0+4.0*clipped

    def predict_trace(self,path):
        return self.predict_arrays(trace_tensors(path))

def score_sequences(sequences,bundle,candidate_dir,out,expected_bundle_sha256=None):
    rows=list(csv.DictReader(open(sequences,newline="",encoding="utf-8")))
    _require(rows,"empty sequence manifest")
    ens=FrozenEnsemble(bundle,candidate_dir,expected_bundle_sha256)
    scored=[]
    for i,r in enumerate(rows,1):
        validate_sequence_row(r)
        seed_raw,raw,clipped,mos=ens.predict_trace(r["trace_path"])
        scored.append({**r,
          "openvq_seed20260926_raw":seed_raw[0],
          "openvq_seed20260927_raw":seed_raw[1],
          "openvq_seed20260928_raw":seed_raw[2],
          "openvq_quality_raw":raw,
          "openvq_quality":clipped,
          "openvq_mos":mos,
        })
        if i%50==0 or i==len(rows):print("scored",i,"/",len(rows),flush=True)
    with open(out,"w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=list(scored[0]));w.writeheader();w.writerows(scored)
    return scored
