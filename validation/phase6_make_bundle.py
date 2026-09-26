#!/usr/bin/env python3
"""Build an immutable Phase 6 model-bundle manifest."""
import argparse,hashlib,json,subprocess
from pathlib import Path

def sha(path):
    h=hashlib.sha256()
    with open(path,"rb") as f:
        for b in iter(lambda:f.read(1024*1024),b""):h.update(b)
    return h.hexdigest()

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--onnx",required=True);ap.add_argument("--state",required=True)
    ap.add_argument("--training-report",required=True);ap.add_argument("--mode",required=True)
    ap.add_argument("--output",required=True)
    ap.add_argument("--source-commit",default="")
    a=ap.parse_args()
    source=a.source_commit or subprocess.check_output(["git","rev-parse","HEAD"],text=True).strip()
    payload={
      "bundle_schema":"openvq-phase6-bundle-v1",
      "frontend_id":"openvq-frontend-phase6a-2026-09-26-v1",
      "feature_schema_id":"openvq-rich-v3-2026-09-26-v1",
      "trace_schema_id":"openvq-trace-v1-2026-09-26",
      "model_mode":a.mode,"source_commit":source,
      "onnx_sha256":sha(a.onnx),"pytorch_state_sha256":sha(a.state),
      "training_report_sha256":sha(a.training_report),
      "onnx_file":Path(a.onnx).name,"state_file":Path(a.state).name,
      "training_report_file":Path(a.training_report).name,
      "parity_mos_abs_tolerance":1e-4,
      "weights_budget_bytes":10*1024*1024,
      "peak_memory_budget_bytes":128*1024*1024,
      "android_rtf_budget":0.25,
      "claim_status":"development candidate until frozen external validation",
    }
    canonical=json.dumps(payload,sort_keys=True,separators=(",",":")).encode()
    payload["pipeline_id"]="openvq-phase6-"+hashlib.sha256(canonical).hexdigest()[:20]
    Path(a.output).write_text(json.dumps(payload,indent=2)+"\n")
    print(json.dumps(payload,indent=2))
if __name__=="__main__":main()
