#!/usr/bin/env python3
"""Phase 6.3A fail-closed verification of the frozen candidate and evaluator."""
from __future__ import annotations
import argparse,csv,hashlib,json,shutil,tempfile
from pathlib import Path
import numpy as np

from phase63_bundle_runtime import EXPECTED,FrozenEnsemble,load_bundle,score_sequences,sha256

SCOPED={"dropout","dropout_count","noise","lowpass","clipping","mixed"}

def close(a,b,tol=1e-4):
    return abs(float(a)-float(b))<=tol

def summarize(rows):
    by={(r["family"],r["label"]):r for r in rows}
    clean=float(next(r["openvq_mos"] for r in rows if r["family"]=="clean"))
    delay=[float(r["openvq_mos"]) for r in rows if r["family"]=="delay"]
    fam={}
    for name in sorted(SCOPED):
        rr=sorted([r for r in rows if r["family"]==name],key=lambda z:float(z["level"]))
        fam[name]=rr
    return clean,max(abs(x-clean) for x in delay),fam

def require_failure(fn,label,results):
    try:
        fn()
    except Exception as e:
        results.append({"case":label,"passes":True,"error":type(e).__name__+": "+str(e)})
        return
    results.append({"case":label,"passes":False,"error":"verification unexpectedly succeeded"})

def negative_tests(bundle_path,candidate_dir,bundle_sha):
    results=[]
    with tempfile.TemporaryDirectory(prefix="phase63-negative-") as td:
        root=Path(td)
        shutil.copytree(candidate_dir,root/"candidate")
        shutil.copy(bundle_path,root/"bundle.json")
        # Missing model.
        miss=root/"candidate"/"clipreg-seed20260928.onnx"
        miss.unlink()
        require_failure(lambda:load_bundle(root/"bundle.json",root/"candidate",bundle_sha),"missing_model",results)

    with tempfile.TemporaryDirectory(prefix="phase63-negative-") as td:
        root=Path(td);shutil.copytree(candidate_dir,root/"candidate");shutil.copy(bundle_path,root/"bundle.json")
        p=root/"candidate"/"clipreg-seed20260927.onnx"
        data=bytearray(p.read_bytes());data[len(data)//2]^=1;p.write_bytes(data)
        require_failure(lambda:load_bundle(root/"bundle.json",root/"candidate",bundle_sha),"altered_model",results)

    with tempfile.TemporaryDirectory(prefix="phase63-negative-") as td:
        root=Path(td);shutil.copytree(candidate_dir,root/"candidate")
        b=json.loads(Path(bundle_path).read_text());b["trace_schema_id"]="openvq-trace-v1-2026-09-26"
        p=root/"bundle.json";p.write_text(json.dumps(b,indent=2)+"\n")
        require_failure(lambda:load_bundle(p,root/"candidate",sha256(p)),"wrong_trace_version",results)

    with tempfile.TemporaryDirectory(prefix="phase63-negative-") as td:
        root=Path(td);shutil.copytree(candidate_dir,root/"candidate")
        b=json.loads(Path(bundle_path).read_text());b["bundle_schema"]="openvq-wrong-bundle"
        p=root/"bundle.json";p.write_text(json.dumps(b,indent=2)+"\n")
        require_failure(lambda:load_bundle(p,root/"candidate",sha256(p)),"wrong_bundle_schema",results)
    return results

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--bundle",required=True)
    ap.add_argument("--candidate-dir",required=True)
    ap.add_argument("--expected-bundle-sha256",required=True)
    ap.add_argument("--engineering-sequences",required=True)
    ap.add_argument("--engineering-report",required=True)
    ap.add_argument("--guardrail-report",required=True)
    ap.add_argument("--expected-engineering-sha256",required=True)
    ap.add_argument("--expected-guardrail-sha256",required=True)
    ap.add_argument("--outdir",required=True)
    ap.add_argument("--tol-mos",type=float,default=1e-4)
    a=ap.parse_args()
    out=Path(a.outdir);out.mkdir(parents=True,exist_ok=True)
    if sha256(a.engineering_report)!=a.expected_engineering_sha256:raise SystemExit("engineering report hash mismatch")
    if sha256(a.guardrail_report)!=a.expected_guardrail_sha256:raise SystemExit("guardrail report hash mismatch")
    guard=json.loads(Path(a.guardrail_report).read_text())
    if guard.get("passes") is not True:raise SystemExit("frozen subjective guardrail did not pass")
    b,_=load_bundle(a.bundle,a.candidate_dir,a.expected_bundle_sha256)
    scored_path=out/"engineering-rescored.csv"
    rows=score_sequences(a.engineering_sequences,a.bundle,a.candidate_dir,scored_path,a.expected_bundle_sha256)
    clean,delay_delta,fam=summarize(rows)
    old=json.loads(Path(a.engineering_report).read_text())
    diffs=[]
    diffs.append(abs(clean-float(old["identity_mos"])))
    diffs.append(abs(delay_delta-float(old["delay_max_abs_delta_mos"])))
    for family,section in old["scoped_monotonic"].items():
        new={(r["label"]):r for r in fam[family]}
        for r in section["rows"]:
            if r["label"] not in new:raise SystemExit(f"missing engineering row {family}/{r['label']}")
            diffs.append(abs(float(new[r["label"]]["openvq_mos"])-float(r["mos"])))
            for i,key in enumerate(("openvq_seed20260926_raw","openvq_seed20260927_raw","openvq_seed20260928_raw")):
                diffs.append(abs(float(new[r["label"]][key])-float(r["seed_quality_raw"][i]))*4.0)
    max_diff=max(diffs)
    neg=negative_tests(Path(a.bundle),Path(a.candidate_dir),a.expected_bundle_sha256)
    if not all(x["passes"] for x in neg):raise SystemExit("negative verification tests failed")
    result={
      "phase":"6.3A",
      "candidate_source":EXPECTED["source_commit"],
      "evaluator_source":"recorded by workflow",
      "bundle_sha256":sha256(a.bundle),
      "engineering_report_sha256":sha256(a.engineering_report),
      "guardrail_report_sha256":sha256(a.guardrail_report),
      "reproduced_identity_mos":clean,
      "reproduced_delay_max_abs_delta_mos":delay_delta,
      "max_abs_reproduction_mos_difference":max_diff,
      "tolerance_mos":a.tol_mos,
      "reproduction_passes":max_diff<=a.tol_mos,
      "negative_tests":neg,
      "polqa_required":False,
      "polqa_status":"not_evaluated_not_required",
    }
    Path(out/"phase63a-verification.json").write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps(result,indent=2))
    if not result["reproduction_passes"]:raise SystemExit(2)
if __name__=="__main__":main()
