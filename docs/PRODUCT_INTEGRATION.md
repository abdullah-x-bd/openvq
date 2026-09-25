# Product integration guidance

## Intended product use

OpenVQ is designed for use in telecom and drive-test systems where a known reference speech sample is available and a recorded or transmitted degraded sample can be compared with it.

Potential product outputs include:

- OpenVQ quality score
- bandwidth class
- delay
- clock drift
- clipping
- missing and added disturbance
- coloration
- noisiness
- discontinuity
- loudness mismatch
- echo
- choppiness
- residual intrusion
- confidence

## Naming

A product may call the output:

- OpenVQ MOS
- OpenVQ quality score
- OpenVQ full-reference speech-quality score

It should not call the output:

- POLQA
- POLQA MOS
- P.863 score
- P.863-compliant score

unless a separate licensed and conformant POLQA implementation is actually being used.

## Current deployment status

The native analyzer and diagnostics are suitable for engineering integration and experimental field collection.

The frozen Phase 3 hybrid score is not currently validated strongly enough to be presented as a general replacement for POLQA because it failed the independent OpenACE codec benchmark.

A drive-test product can still integrate OpenVQ now for:

- internal experimentation
- side-by-side field evaluation
- diagnostic dimensions
- collection of future validation data

A broad external claim that OpenVQ is equivalent to or better than POLQA should wait for Phase 4 and new untouched validation.

## Recommended application architecture

```
known test utterance
        |
        +---------------------+
                              |
                              v
network / device / call --> recorded speech
                              |
                              v
                       native OpenVQ
                              |
                    diagnostics + score
                              |
                 optional expert evidence
                              |
                              v
                       product reporting
```

The preferred Phase 4 direction is native-first. External experts such as ViSQOL should be optional and reliability-gated.

## Why the diagnostics matter

A single MOS-like value can identify that quality changed, but it is less useful for troubleshooting.

OpenVQ's diagnostic dimensions can help distinguish cases such as:

- network loss or choppiness
- echo
- bandwidth limitation
- excessive noise
- spectral coloration
- clipping
- level mismatch
- temporal misalignment

For a drive-test application this diagnostic layer may be more operationally useful than reproducing one proprietary scalar score.

## Commercial note

OpenVQ's repository license is PolyForm Noncommercial 1.0.0. Commercial deployment requires a separate written commercial license from the OpenVQ licensor.

Google ViSQOL is a separate upstream project and must retain its own licensing and attribution requirements when used.
