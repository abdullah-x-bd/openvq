# OpenVQ architecture

## Purpose

OpenVQ is an independently derived full-reference speech-quality research engine.

It compares reference and degraded speech and returns native diagnostics plus research score-path outputs. It does not implement POLQA or ITU-T P.863.

## Current architecture in Phase 6.1

```
reference audio ----------------------+
                                      |
                                      v
                           frozen shared frontend
                                      |
degraded audio -----------------------+
                                      |
                                      v
                    alignment + active-speech accounting
                                      |
                  +-------------------+-------------------+
                  |                                       |
                  v                                       v
          native perceptual analysis              telecom/coverage analysis
                  |                                       |
                  +-------------------+-------------------+
                                      |
                         +------------+------------+
                         |                         |
                         v                         v
                 global rich-v3 features     local trace v1
                         |                         |
                         +------------+------------+
                                      |
                              research mappers
                    summary models / sequence models
```

The stable runtime foundation ends before the research mapper.

## Frozen frontend

Frontend ID:

`openvq-frontend-phase6a-2026-09-26-v1`

The frontend provides:

- shared 48 kHz preprocessing;
- one windowed-sinc resampler;
- one DC-removal implementation;
- shared prepared reference/degraded buffers;
- global delay;
- direct-match detection for transport-only delay;
- bounded piecewise-continuous local alignment;
- alignment confidence and coverage;
- clock drift;
- reference activity;
- active coverage and lost active speech;
- matched active levels;
- separate raw-input clipping.

The same native preprocessing sources are compiled for desktop and Android.

## Native analysis

The analyzer computes spectral, perceptual, temporal, and telecom evidence including:

- FFT and ERB comparisons;
- multi-resolution similarity;
- missing and added disturbance;
- asymmetric disturbance;
- coloration;
- noisiness;
- active-level mismatch;
- discontinuity;
- clipping;
- temporal-envelope and modulation similarity;
- spectral tilt;
- bad sections and worst intervals;
- echo;
- choppiness;
- PLC-like repetition;
- residual intrusion.

## Global feature schemas

`legacy19` is retained for historical ablation.

`rich-v2` adds coverage, alignment, tail, drift, clipping, and confidence summaries.

`rich-v3` adds separate raw input clipping and is bound to the Phase 6A frontend.

Summary-model experiments remain development evidence.

## Local trace

Trace schema:

`openvq-trace-v1-2026-09-26`

The local trace retains 10 ms timeline evidence before utterance pooling.

It contains reference/degraded 64-band auditory vectors, activity, coverage, unmatched state, local confidence, local similarity, levels, and mapped-time offset.

The trace is paired with the rich-v3 global side vector.

## Sequence-model research layer

Phase 6E evaluated:

- native temporal;
- learned bands;
- hybrid.

The hybrid model combines learned local sequence evidence with rich-v3 global features.

Hybrid won the frozen worst-held-corpus selection rule. It is not the product model.

The full-development hybrid candidate passed ONNX parity but failed the independent engineering gate. It is therefore retained as research evidence only.

## Runtime boundary

Current product-facing code can use the native analyzer and diagnostics.

The Phase 6 sequence model is not integrated as the released MOS path.

This boundary is intentional. Model exportability is not sufficient for promotion when independent engineering sanity fails.

## External metrics

ViSQOL remains an optional external benchmark and historical expert signal.

POLQA is a benchmark only when lawful outputs are available for the exact same pairs.

OpenVQ contains no POLQA source and makes no P.863 conformance claim.
