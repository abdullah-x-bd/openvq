# Phase 6.1 trace correctness erratum

## Status

The Phase 6.1 sequence results are preserved as historical development evidence, but they were generated from a trace implementation with a confirmed FFT indexing defect.

This erratum does not alter the recorded Phase 6.1 numbers. It changes their interpretation and starts the Phase 6.2 corrected-trace baseline.

## Defect

The Phase 6.1 trace FFT butterfly used the first element of each FFT block instead of the current butterfly element.

Historical expression:

```cpp
const auto u = x[i];
```

Correct expression:

```cpp
const auto u = x[i + j];
```

The defect affected:

- reference auditory-band vectors;
- degraded auditory-band vectors;
- local spectral similarity derived from those vectors;
- all three Phase 6E sequence arms, including native_temporal because it consumes local similarity.

The Phase 6A native analyzer uses a separate correct FFT implementation. Its frozen frontend evidence is not invalidated by this trace-only defect.

## Affected canonical evidence

Historical trace schema:

`openvq-trace-v1-2026-09-26`

Canonical Phase 6D run:

`36247385269`

Canonical Phase 6D artifact:

`10907723570`

Artifact SHA-256:

`b4f709a6160a9de5ceb1afaa8f60e2e87a44c9a120688e97818d5a8e4bd80c40`

The Phase 6E/F model results derived from that trace remain reproducible records. They are not used as proof that the local spectral representation was mathematically correct.

## Phase 6.2 correction

Corrected trace schema:

`openvq-trace-v2-2026-09-27`

Trace implementation ID:

`openvq-trace-spectral-v2-fft-corrected-2026-09-27`

The corrected trace path adds:

- FFT-versus-direct-DFT oracle tests;
- impulse fixture;
- constant-input fixture;
- Parseval energy fixture;
- known-frequency auditory-band fixtures;
- amplitude-to-band-energy fixture.

The Phase 6A frontend ID remains unchanged because its frozen files and measurement semantics are not modified.

## Controlled rerun rule

The first Phase 6.2 model experiment changes only the trace implementation.

The following remain fixed from Phase 6E:

- five development corpora;
- 2,463 development pairs;
- source grouping;
- three architectures;
- three seeds;
- held-corpus folds;
- optimizer and hyperparameters;
- early-stopping procedure;
- 80-epoch ceiling;
- ensemble aggregation;
- architecture selection rule.

This controlled rerun measures the effect of corrected trace mathematics before any normalization, batching, loss, architecture, or dataset redesign.
