# Phase 6 trace schema v1

Schema ID:

`openvq-trace-v1-2026-09-26`

Frontend dependency:

`openvq-frontend-phase6a-2026-09-26-v1`

## Grid

- prepared sample rate 48 kHz;
- hop 10 ms;
- analysis window 20 ms;
- 64 log-spaced fullband auditory bands.

## Per-frame fields

- reference 64-band log-power vector;
- degraded 64-band log-power vector after native alignment;
- reference activity;
- valid coverage;
- unmatched flag;
- local alignment confidence;
- local spectral similarity;
- reference RMS dB;
- degraded RMS dB;
- mapped-time minus reference-time offset.

Inactive and unmatched frames remain explicit.

## Global side information

Each sequence record also carries the Phase 6 rich-v3 global feature vector.

## Freeze evidence

Phase 6D recreated and verified all 2,463 development pairs against the canonical Phase 6B evidence before exporting traces.

Canonical trace artifact:

- run `36247385269`;
- artifact ID `10907723570`;
- artifact SHA-256 `b4f709a6160a9de5ceb1afaa8f60e2e87a44c9a120688e97818d5a8e4bd80c40`;
- development provenance SHA-256 `cbd5c8874026142b065d352335083640000e507ce1ba364614c236e31319c8fc`;
- engineering provenance SHA-256 `ae6c65002093cb8f0a78b3829a25719467b53352e6009f57094b8e538c4f68b8`.

## Numerical contract

Canonical content hashes use array dtype, shape, and bytes rather than NPZ container bytes.

Cross-implementation normalized trace comparisons begin with a 1e-5 absolute tolerance unless platform evidence justifies another value.

## Status

The trace representation remains part of the Phase 6.1 research foundation.

The failure of the Phase 6E hybrid candidate is a mapping/training failure and does not invalidate the trace contract.
