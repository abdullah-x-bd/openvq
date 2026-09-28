#!/usr/bin/env python3
"""Build an immutable Phase 6.2G ensemble bundle after both guardrails pass."""
import argparse,hashlib,json,subprocess
from pathlib import Path

def sha(path):
    h=hashlib.sha256()
    with open(path,"rb") as f:
        for b in iter(lambda:f.read(1024*1024),b""):h.update(b)
    return h.hexdigest()

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--onnx",action="append",required=True)
    ap.add_argument("--state",action="append",required=True)
    ap.add_argument("--training-report",action="append",required=True)
    ap.add_argument("--parity-report",action="append",required=True)
    ap.add_argument("--guardrail-report",required=True)
    ap.add_argument("--engineering-report",required=True)
    ap.add_argument("--output",required=True)
    a=ap.parse_args()
    if not(len(a.onnx)==len(a.state)==len(a.training_report)==len(a.parity_report)==3):
        raise SystemExit("expected exactly three seeds for every model artifact")
    source=subprocess.check_output(["git","rev-parse","HEAD"],text=True).strip()
    payload={
      "bundle_schema":"openvq-phase62g-clipping-regularized-ensemble-v1",
      "phase":"6.2G",
      "frontend_id":"openvq-frontend-phase6a-2026-09-26-v1",
      "feature_schema_id":"openvq-rich-v3-2026-09-26-v1",
      "trace_schema_id":"openvq-trace-v2-2026-09-27",
      "trace_implementation_id":"openvq-trace-spectral-v2-fft-corrected-2026-09-27",
      "model_mode":"learned_bands_padding_safe_clipreg",
      "seeds":[20260926,20260927,20260928],
      "ensemble_rule":"arithmetic mean of raw quality predictions, then clamp to [0,1]",
      "property_constraint":{"type":"clipping_order","lambda":0.25,"margin_raw":0.03,"interval_human_batches":4},
      "source_commit":source,
      "onnx":[{"file":Path(p).name,"sha256":sha(p)} for p in a.onnx],
      "pytorch_states":[{"file":Path(p).name,"sha256":sha(p)} for p in a.state],
      "training_reports":[{"file":Path(p).name,"sha256":sha(p)} for p in a.training_report],
      "parity_reports":[{"file":Path(p).name,"sha256":sha(p)} for p in a.parity_report],
      "subjective_guardrail_report":{"file":Path(a.guardrail_report).name,"sha256":sha(a.guardrail_report)},
      "engineering_report":{"file":Path(a.engineering_report).name,"sha256":sha(a.engineering_report)},
      "claim_status":"engineering-qualified development candidate; external reserve still untouched",
    }
    canonical=json.dumps(payload,sort_keys=True,separators=(",",":")).encode()
    payload["pipeline_id"]="openvq-phase62g-"+hashlib.sha256(canonical).hexdigest()[:20]
    Path(a.output).write_text(json.dumps(payload,indent=2)+"\n");print(json.dumps(payload,indent=2))
if __name__=="__main__":main()
