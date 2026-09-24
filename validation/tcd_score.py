#!/usr/bin/env python3
import argparse,csv,json,subprocess

ap=argparse.ArgumentParser()
ap.add_argument("manifest")
ap.add_argument("output")
ap.add_argument("--cli",default="./build/openvq_cli")
ap.add_argument("--calibration")
args=ap.parse_args()

with open(args.manifest,newline="",encoding="utf-8") as src, \
     open(args.output,"w",newline="",encoding="utf-8") as dst:
    rd=csv.DictReader(src)
    fields=list(rd.fieldnames)+["openvq_mos","openvq_confidence","base_mos"]
    wr=csv.DictWriter(dst,fieldnames=fields)
    wr.writeheader()
    for i,row in enumerate(rd,1):
        cmd=[args.cli,row["reference"],row["degraded"]]
        if args.calibration: cmd += ["--calibration",args.calibration]
        obj=json.loads(subprocess.check_output(cmd,text=True))
        row["openvq_mos"]=obj["mos"]
        row["openvq_confidence"]=obj["confidence"]
        row["base_mos"]=obj.get("base_mos","")
        wr.writerow(row)
        if i%25==0: print(f"scored {i}",flush=True)
