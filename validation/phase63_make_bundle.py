#!/usr/bin/env python3
"""Build immutable Phase 6.3B-R1 bundle only after all development qualification gates pass."""
import argparse,hashlib,json,subprocess
from pathlib import Path
def sha(path):
    h=hashlib.sha256()
    with open(path,"rb") as f:
        for b in iter(lambda:f.read(1<<20),b""):h.update(b)
    return h.hexdigest()
def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--onnx",action="append",required=True);ap.add_argument("--state",action="append",required=True);ap.add_argument("--training-report",action="append",required=True);ap.add_argument("--parity-report",action="append",required=True)
    ap.add_argument("--guardrail-report",required=True);ap.add_argument("--engineering-report",required=True);ap.add_argument("--real-speech-report",required=True)
    ap.add_argument("--trace-provenance",required=True);ap.add_argument("--property-provenance",required=True);ap.add_argument("--selection-provenance",required=True);ap.add_argument("--output",required=True);a=ap.parse_args()
    if not(len(a.onnx)==len(a.state)==len(a.training_report)==len(a.parity_report)==3):raise SystemExit("expected exactly three seeds")
    source=subprocess.check_output(["git","rev-parse","HEAD"],text=True).strip()
    payload={"bundle_schema":"openvq-phase63b-r1-ensemble-v1","phase":"6.3B-R1","frontend_id":"openvq-frontend-phase63b-2026-09-29-v1",
      "feature_schema_id":"openvq-rich-v4-2026-09-29-v1","trace_schema_id":"openvq-trace-v3-2026-09-29",
      "trace_implementation_id":"openvq-trace-v3-transport-fallback-2026-09-29","model_mode":"learned_bands_padding_safe_clipreg_identityinv_v3",
      "seeds":[20260926,20260927,20260928],"ensemble_rule":"arithmetic mean of raw quality predictions, then clamp to [0,1]",
      "property_contract":{"clip_lambda":0.25,"clip_margin_raw":0.03,"identity_lambda":0.50,"identity_floor_raw":0.85,"invariance_lambda":0.25,"invariance_margin_raw":0.05,"property_interval_human_batches":4},
      "source_commit":source,"onnx":[{"file":Path(p).name,"sha256":sha(p)} for p in a.onnx],
      "pytorch_states":[{"file":Path(p).name,"sha256":sha(p)} for p in a.state],
      "training_reports":[{"file":Path(p).name,"sha256":sha(p)} for p in a.training_report],
      "parity_reports":[{"file":Path(p).name,"sha256":sha(p)} for p in a.parity_report],
      "guardrail_report":{"file":Path(a.guardrail_report).name,"sha256":sha(a.guardrail_report)},
      "engineering_report":{"file":Path(a.engineering_report).name,"sha256":sha(a.engineering_report)},
      "real_speech_report":{"file":Path(a.real_speech_report).name,"sha256":sha(a.real_speech_report)},
      "trace_provenance":{"file":Path(a.trace_provenance).name,"sha256":sha(a.trace_provenance)},
      "property_provenance":{"file":Path(a.property_provenance).name,"sha256":sha(a.property_provenance)},
      "selection_provenance":{"file":Path(a.selection_provenance).name,"sha256":sha(a.selection_provenance)},
      "claim_status":"development candidate eligible for Phase 6.3C external-protocol freeze; reserve untouched"}
    canonical=json.dumps(payload,sort_keys=True,separators=(",",":")).encode();payload["pipeline_id"]="openvq-phase63b-r1-"+hashlib.sha256(canonical).hexdigest()[:20]
    Path(a.output).write_text(json.dumps(payload,indent=2)+"\n");print(json.dumps(payload,indent=2))
if __name__=="__main__":main()
