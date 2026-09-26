# Product integration guidance

## Intended use

OpenVQ is designed for full-reference telecom and drive-test workflows where a known reference utterance and a captured degraded utterance can be compared.

Useful product outputs include:

- quality score for internal experimentation;
- bandwidth class;
- delay;
- clock drift;
- active-speech coverage;
- lost active speech;
- alignment confidence;
- clipping;
- missing and added disturbance;
- coloration;
- noisiness;
- discontinuity;
- loudness/active-level mismatch;
- echo;
- choppiness;
- residual intrusion;
- confidence.

## Naming

Acceptable names include:

- OpenVQ quality score;
- OpenVQ full-reference speech-quality score;
- OpenVQ MOS, when clearly identified as an OpenVQ-specific research/product scale.

Do not label an OpenVQ output as:

- POLQA;
- POLQA MOS;
- P.863 score;
- P.863-compliant score.

## Current deployment status after Phase 5.1

The repaired native analyzer and diagnostic outputs are suitable for:

- engineering integration;
- internal drive-test experimentation;
- side-by-side field collection;
- impairment diagnostics;
- collection of future validation data.

OpenVQ is **not** currently validated strongly enough to be marketed as a general replacement for POLQA.

Phase 5.1 improved the measurement foundation and known-domain modeling, but leave-corpus-out evaluation still failed severely for some unseen domains.

## Phase 5.1 model status

Phase 5.1 produced a reproducible constrained rich-v2 research export.

It was deliberately **not promoted into the main CLI or Android product scoring path** because unseen-corpus transfer was insufficient.

The small Phase 5.1 MLP is diagnostic only.

The repaired preprocessing and native analysis code *are* part of the current native engine and Android build.

## Recommended product architecture

```
known test utterance
        |
        v
shared OpenVQ preprocessing
        |
        v
alignment + active-speech accounting
        |
        v
native perceptual / telecom diagnostics
        |
        +--------------------------+
        |                          |
        v                          v
engineering diagnostics     experimental quality model
        |                          |
        +------------+-------------+
                     |
                     v
               product reporting
```

The diagnostic path should remain useful even while the learned MOS mapper evolves.

## Why diagnostics are currently the strongest integration surface

Phase 5.1 separated engineering sanity from subjective generalization.

The engineering suites pass, while unseen-corpus MOS mapping remains weak.

That means outputs such as:

- delay;
- active coverage;
- lost speech;
- clipping;
- bandwidth;
- echo;
- choppiness;
- noise-related diagnostics;
- alignment confidence;

can be operationally useful without implying that the current scalar MOS is POLQA-equivalent.

## External claims

Before making a broad claim that OpenVQ equals or outperforms POLQA, the project should complete:

1. a frozen Phase 6 candidate;
2. untouched external subjective validation;
3. lawful direct POLQA scoring of the exact same audio pairs;
4. the locked paired comparison protocol;
5. reporting across impairment families rather than only aggregate metrics.

## Commercial note

The repository uses PolyForm Noncommercial 1.0.0.

Commercial deployment requires a separate written commercial license from the OpenVQ licensor.

Google ViSQOL is a separate upstream project with its own licensing and attribution requirements when used.
