# Phase 6 trace schema v1

Schema ID: `openvq-trace-v1-2026-09-26`

Frontend dependency: `openvq-frontend-phase6a-2026-09-26-v1`

The trace preserves local evidence before utterance pooling.

## Grid

- prepared sample rate: 48 kHz
- hop: 10 ms
- analysis window: 20 ms
- auditory bands: 64 log-spaced bands from approximately 50 Hz to the usable fullband Nyquist region

## Per-frame fields

- reference 64-band log-power vector
- degraded 64-band log-power vector after native alignment
- reference activity flag
- valid-coverage flag
- unmatched flag
- local alignment confidence
- local spectral similarity
- reference RMS dB
- degraded RMS dB
- mapped-time minus reference-time offset

Inactive frames are retained.

Unmatched frames are retained and explicitly masked. They are not silently removed or treated as ordinary recorded silence.

## Global side information

The cached sequence includes the Phase 6 rich-v3 global feature vector alongside the local timeline.

## Numerical contract

The canonical content hash is computed from array dtype, shape, and bytes rather than from the ZIP/NPZ container bytes.

Within a pinned build/platform, trace-content hashes must be stable.

Cross-implementation numerical comparisons should initially use `1e-5` absolute tolerance on normalized trace features, with any relaxation justified by a measured platform analysis.

## Intended use

This is a research representation for Phase 6. It is not a POLQA representation and does not copy P.863 constants or software.
