# Product integration guidance

## Intended use

OpenVQ supports full-reference telecom and drive-test workflows with a known reference utterance and a captured degraded utterance.

Useful native outputs include:

- delay;
- bandwidth;
- clock drift;
- active coverage;
- lost active speech;
- alignment confidence;
- clipping;
- missing and added disturbance;
- coloration;
- noisiness;
- discontinuity;
- level mismatch;
- echo;
- choppiness;
- residual intrusion.

## Naming

Acceptable:

- OpenVQ quality score;
- OpenVQ full-reference speech-quality score;
- OpenVQ MOS when clearly identified as an OpenVQ-specific scale.

Not acceptable:

- POLQA;
- POLQA MOS;
- P.863 score;
- P.863-compliant score.

## Current deployment status

The Phase 6A native frontend and analyzer are the stable integration surface.

The Phase 6E hybrid sequence candidate is **not deployed**.

It passed model export and ONNX parity, but it failed independent engineering sanity. In particular, clean identity scored 2.393 MOS and several worsening degradation sequences received improving scores.

The failed candidate is retained for research diagnosis only.

## Recommended integration boundary

```
reference + degraded audio
          |
          v
 frozen native frontend
          |
          v
 diagnostics + trace
          |
          +----------------------+
          |                      |
          v                      v
 operational diagnostics   research quality model
```

Native diagnostics can be integrated independently from the evolving scalar quality mapper.

## Android

Android compiles the shared native frontend and analyzer sources.

The trace-native path exists for Phase 6 research.

The failed Phase 6E neural candidate is not the released Android MOS path.

## External claims

A broad replacement or superiority claim requires evidence beyond Phase 6.1:

- a candidate that passes engineering promotion gates;
- a genuinely untouched subjective evaluation;
- lawful POLQA outputs for the exact same pairs when POLQA comparison is claimed;
- predeclared paired statistics;
- impairment-family reporting.

## Commercial note

The repository is source-available under PolyForm Noncommercial 1.0.0.

Commercial use requires a separate written commercial license.
