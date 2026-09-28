# Phase 6 trace schema v2

Schema ID:

`openvq-trace-v2-2026-09-27`

Trace implementation ID:

`openvq-trace-spectral-v2-fft-corrected-2026-09-27`

Frontend dependency:

`openvq-frontend-phase6a-2026-09-26-v1`

## Why v2 exists

Phase 6.1 Trace V1 contained an FFT butterfly indexing defect in the trace-only spectral path. V2 corrects that calculation and adds independent numerical tests.

The Phase 6A native analyzer has a separate correct FFT and remains frozen.

Trace V1 is retained as historical evidence and must not be silently interpreted as V2.

See [Phase 6.1 trace correctness erratum](PHASE6_1_TRACE_ERRATUM.md).

## Grid

- prepared sample rate 48 kHz;
- hop 10 ms;
- analysis window 20 ms;
- FFT length 1024 for the normal 20 ms / 48 kHz frame;
- 64 log-spaced auditory bands from approximately 50 Hz to the usable fullband region.

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

Each sequence record carries the frozen rich-v3 global feature vector.

## Numerical correctness gate

The V2 trace spectral implementation is tested against:

- direct complex DFT at lengths 8, 16, and 1024;
- impulse spectrum;
- constant-input spectrum;
- Parseval energy conservation;
- deterministic tone-to-band placement;
- expected approximately 6.02 dB band-energy change when tone amplitude is halved.

Trace generation is not considered valid if these tests fail.

## Cache contract

Sequence manifests record both:

- `trace_schema_id`;
- `trace_implementation_id`.

V2 training rejects V1 cache rows.

Canonical content hashes continue to use array dtype, shape, and bytes rather than NPZ container bytes.

## Phase 6.2 baseline

All 2,463 development traces and engineering traces are regenerated under V2 before the controlled 45-fit sequence experiment.

The first V2 model comparison changes no training architecture, data split, seed, or hyperparameter from the Phase 6E baseline.
