#!/usr/bin/env python3
"""Inspect only the NISQA TEST P501 portion of the remote NISQA archive."""
import argparse
import json
from collections import Counter
from remotezip import RemoteZip

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument(
        "--url",
        default="https://zenodo.org/records/4728081/files/NISQA_Corpus.zip?download=1",
    )
    ap.add_argument("--out", required=True)
    args=ap.parse_args()

    with RemoteZip(args.url) as z:
        names=z.namelist()
        p501=[n for n in names if "NISQA_TEST_P501" in n]
        relevant=[
            n for n in names
            if ("NISQA_TEST_P501" in n or
                n.endswith(".csv") or
                "P501" in n and n.endswith((".txt",".md")))
        ]
        result={
            "archive_entries":len(names),
            "p501_entries":len(p501),
            "p501_extensions":dict(Counter(
                ("."+n.rsplit(".",1)[-1].lower()) if "." in n.rsplit("/",1)[-1] else ""
                for n in p501
            )),
            "entries":relevant[:2000],
        }
        with open(args.out,"w",encoding="utf-8") as f:
            json.dump(result,f,indent=2)
        print(json.dumps(result,indent=2))

if __name__=="__main__":
    main()
