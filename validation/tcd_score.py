#!/usr/bin/env python3
import argparse,csv,json,os,subprocess
from concurrent.futures import ThreadPoolExecutor

ap=argparse.ArgumentParser()
ap.add_argument("manifest")
ap.add_argument("output")
ap.add_argument("--cli",default="./build/openvq_cli")
ap.add_argument("--calibration")
ap.add_argument("--jobs",type=int,default=max(1,min(4,os.cpu_count() or 1)))
args=ap.parse_args()

with open(args.manifest,newline="",encoding="utf-8") as src:
    rd=csv.DictReader(src)
    input_fields=list(rd.fieldnames)
    rows=list(rd)

def analyze(row):
    cmd=[args.cli,row["reference"],row["degraded"]]
    if args.calibration: cmd += ["--calibration",args.calibration]
    obj=json.loads(subprocess.check_output(cmd,text=True))
    result=dict(row)
    result["openvq_mos"]=obj["mos"]
    result["openvq_confidence"]=obj["confidence"]
    result["base_mos"]=obj.get("base_mos","")
    return result

fields=input_fields+["openvq_mos","openvq_confidence","base_mos"]
with open(args.output,"w",newline="",encoding="utf-8") as dst:
    wr=csv.DictWriter(dst,fieldnames=fields)
    wr.writeheader()
    with ThreadPoolExecutor(max_workers=args.jobs) as pool:
        for i,row in enumerate(pool.map(analyze,rows),1):
            wr.writerow(row)
            if i%25==0:
                print(f"scored {i}/{len(rows)}",flush=True)
