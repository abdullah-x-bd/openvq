#!/usr/bin/env python3
"""Blinded full-reference pairing preflight for the untouched NISQA TEST_NSC reserve.

MOS and dimension-rating columns are deliberately neither read nor emitted.
"""
import argparse,csv,hashlib,json
from pathlib import Path
import soundfile as sf

DENY=("mos","noi","dis","col","loud","rating","score","listener")

def sha(path):
    h=hashlib.sha256()
    with open(path,"rb") as f:
        for b in iter(lambda:f.read(1<<20),b""):h.update(b)
    return h.hexdigest()

def choose(fields,names,required=True):
    low={x.lower():x for x in fields}
    for n in names:
        if n.lower() in low:return low[n.lower()]
    if required:raise SystemExit(f"missing required column {names}; have {fields}")
    return None

def safe_fields(fields):
    return [x for x in fields if not any(t in x.lower() for t in DENY)]

def resolve(root,val,by_name):
    p=Path(str(val).replace("\\","/"));hits=[]
    for q in (root/p,root/p.name):
        if q.is_file():hits.append(q.resolve())
    hits.extend(by_name.get(p.name,[]));hits=list(dict.fromkeys(hits))
    if len(hits)==1:return hits[0],""
    if not hits:return None,"not_found"
    return None,"ambiguous"

def main():
    ap=argparse.ArgumentParser();ap.add_argument("root");ap.add_argument("--manifest",required=True);ap.add_argument("--ledger",required=True);ap.add_argument("--out",required=True);a=ap.parse_args()
    root=Path(a.root);csvs=[p for p in root.rglob("*_file.csv") if "NISQA_TEST_NSC" in str(p)]
    if len(csvs)!=1:raise SystemExit(f"expected exactly one TEST_NSC *_file.csv, found {csvs}")
    source=csvs[0];wavs=[p.resolve() for p in root.rglob("*.wav")];by={}
    for p in wavs:by.setdefault(p.name,[]).append(p)
    rows=[];ledger=[]
    with source.open(newline="",encoding="utf-8-sig") as f:
        rd=csv.DictReader(f);fields=rd.fieldnames or []
        ref=choose(fields,["filepath_ref","ref","reference","ref_file"])
        deg=choose(fields,["filepath_deg","deg","degraded","file","filename"])
        con=choose(fields,["con","condition","condition_id","ConditionID"],False)
        speaker=choose(fields,["source","source_id","speaker","speaker_id"],False)
        # Record schema only after removing subjective columns. Never index a MOS/dimension field.
        safe=safe_fields(fields)
        for i,r in enumerate(rd,1):
            rp,rr=resolve(root,r.get(ref,""),by);dp,dr=resolve(root,r.get(deg,""),by)
            if rp is None or dp is None:
                ledger.append({"row":i,"status":"ineligible","reason":"reference_"+rr if rp is None else "degraded_"+dr,
                               "reference_declared":r.get(ref,""),"degraded_declared":r.get(deg,"")});continue
            ri=sf.info(str(rp));di=sf.info(str(dp));rid=sha(rp);did=sha(dp)
            sample_id=Path(r.get(deg,"")).as_posix()
            rows.append({"sample_id":sample_id,"dataset":"NISQA_TEST_NSC","protocol":"P.808","language":"German",
              "reference_member":str(rp.relative_to(root.resolve())).replace("\\\\","/"),
              "degraded_member":str(dp.relative_to(root.resolve())).replace("\\\\","/"),
              "reference_sha256":rid,"degraded_sha256":did,
              "source_cluster":rid,"speaker_id":r.get(speaker,"") if speaker else "",
              "system_id":r.get(con,"") if con else "","reference_sample_rate":ri.samplerate,
              "degraded_sample_rate":di.samplerate,"reference_frames":ri.frames,"degraded_frames":di.frames,
              "reference_duration_s":ri.duration,"degraded_duration_s":di.duration,
              "reference_channels":ri.channels,"degraded_channels":di.channels,
              "pairing_evidence":"explicit filepath_ref in the released NISQA TEST_NSC file manifest"})
            ledger.append({"row":i,"sample_id":sample_id,"status":"eligible","reason":""})
    ids=[r["sample_id"] for r in rows]
    if len(ids)!=len(set(ids)):raise SystemExit("conflicting duplicate sample IDs")
    pairs={(r["reference_sha256"],r["degraded_sha256"]) for r in rows}
    if len(pairs)!=len(rows):raise SystemExit("duplicate exact audio pairs")
    Path(a.manifest).parent.mkdir(parents=True,exist_ok=True)
    fields=list(rows[0]) if rows else []
    with open(a.manifest,"w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)
    with open(a.ledger,"w",newline="",encoding="utf-8") as f:
        fields=["row","sample_id","status","reason","reference_declared","degraded_declared"]
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader()
        for x in ledger:w.writerow({k:x.get(k,"") for k in fields})
    rights=[]
    for p in sorted(root.rglob("*")):
        if p.is_file() and any(k in p.name.lower() for k in ("license","readme","copyright")):
            rights.append({"path":str(p.relative_to(root)),"sha256":sha(p)})
    result={"phase":"6.3C","reserve_candidate":"NISQA_TEST_NSC","subjective_values_read":False,
      "source_manifest":str(source.relative_to(root)),"source_manifest_sha256":sha(source),
      "archive_source":"TU Berlin DepositOnce NISQA_Corpus.zip, record 11303/13012.5/9",
      "safe_source_columns":safe,"eligible_rows":len(rows),
      "ineligible_rows":sum(x["status"]!="eligible" for x in ledger),"unique_source_clusters":len(set(r["source_cluster"] for r in rows)),
      "explicit_reference_column":ref,"explicit_degraded_column":deg,"rights_files":rights,
      "manifest_sha256":sha(a.manifest),"ledger_sha256":sha(a.ledger),
      "eligibility_passes":len(rows)==240 and all(x["status"]=="eligible" for x in ledger)}
    Path(a.out).write_text(json.dumps(result,indent=2)+"\n");print(json.dumps(result,indent=2))
    if not result["eligibility_passes"]:raise SystemExit(2)
if __name__=="__main__":main()
