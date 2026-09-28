#!/usr/bin/env python3
"""Score Trace V2 rows with the exact frozen Phase 6.2G three-model bundle."""
import argparse
from phase63_bundle_runtime import score_sequences

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("sequences")
    ap.add_argument("--bundle",required=True)
    ap.add_argument("--candidate-dir",required=True)
    ap.add_argument("--expected-bundle-sha256",required=True)
    ap.add_argument("--out",required=True)
    a=ap.parse_args()
    score_sequences(a.sequences,a.bundle,a.candidate_dir,a.out,a.expected_bundle_sha256)
if __name__=="__main__":main()
