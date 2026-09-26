# OpenVQ architecture

## Purpose

OpenVQ is an independently derived full-reference speech-quality research engine for telecom, network testing, and drive-test applications.

It compares a known reference utterance with a degraded recording and returns a quality estimate plus timing, spectral, temporal, and telecom diagnostics.

It does not implement POLQA or ITU-T P.863.

## Current architecture after Phase 5.1

The Phase 5.1 audit separated the system into four conceptual layers:

```
reference audio -------------------+
                                   |
                                   v
                         shared preprocessing
                                   |
degraded audio --------------------+
                                   |
                                   v
                      timing / alignment model
                                   |
              +--------------------+--------------------+
              |                                         |
              v                                         v
       perceptual analysis                    coverage / telecom analysis
              |                                         |
              +--------------------+--------------------+
                                   |
                                   v
                         interpretable features
                   legacy19 / rich-v2 research schema
                                   |
                                   v
                         research quality mapper
```

The important architectural change is that preprocessing and alignment are now shared infrastructure rather than partly duplicated assumptions inside base and advanced analyzers.

## Shared preprocessing

`src/preprocessing.cpp` provides the common native preparation path.

Phase 5.1 introduced:

- one windowed-sinc resampling path;
- one DC-removal path;
- one prepared reference buffer;
- one prepared degraded buffer;
- shared consumption by base and advanced analysis.

This reduces feature disagreement caused by slightly different frontend treatment.

Desktop and Android native builds compile the same preprocessing source.

## Timing and alignment

The analyzer performs:

- global delay estimation;
- multi-region clock-drift estimation;
- piecewise-continuous local alignment;
- bounded local path movement;
- alignment coverage;
- alignment confidence.

The alignment path is deliberately prevented from making arbitrary jumps across low-correlation regions.

The design principle is:

> correct nuisance timing, but do not align away a real missing word.

## Active-speech accounting

Phase 5.1 made active-speech coverage explicit.

The analyzer now records:

- active speech duration;
- active coverage fraction;
- lost active speech fraction;
- active reference level;
- active degraded level.

If degraded audio does not cover active reference speech, that missing region becomes evidence instead of silently leaving the calculation.

## Native perceptual and telecom analysis

The native engine independently computes:

### Spectral/perceptual

- FFT spectral comparison;
- ERB-band auditory representation;
- 20 ms, 80 ms, and 200 ms multi-resolution similarity;
- missing disturbance;
- added disturbance;
- asymmetric disturbance;
- coloration;
- spectral tilt;
- noisiness;
- loudness and active-level mismatch.

### Temporal/telecom

- temporal-envelope similarity;
- modulation-spectrum similarity;
- dropout and bad-section analysis;
- clipping;
- echo;
- choppiness;
- repeated-waveform or PLC-like freeze evidence;
- residual intrusion;
- clock drift;
- worst-interval severity.

## Feature schemas

### legacy19

The original 19 utterance summaries used by the Phase 4 and Phase 5 native mappers.

They are retained so measurement changes can be separated from model changes.

### rich-v2

Phase 5.1 adds 12 measurements:

- lost active speech;
- active coverage;
- alignment uncertainty;
- raw active-level delta;
- similarity p10 loss;
- similarity p50 loss;
- discontinuity p90;
- longest bad interval;
- severe-frame fraction;
- absolute clock drift;
- raw clipping ratio;
- confidence deficit.

Total: 31 features.

The rich schema is a research representation, not a guarantee that the final product model must use all 31 features directly.

## Mapping layer

Historical mapping layers are preserved for reproducibility.

### Phase 3

Native measurements plus optional external ViSQOL speech/audio expert values.

OpenACE showed fixed expert trust did not generalize.

### Phase 4

Native-first constrained degree-two mapping.

Engineering behavior improved, but untouched external testing failed.

### Phase 5

Five-domain refit of the legacy feature family.

It improved breadth but remained weak on TMHINT and later proved to have a TMHINT target-scale evidence defect.

### Phase 5.1

The repaired frontend was tested with:

- constrained legacy19 mapper;
- constrained rich-v2 mapper;
- small rich-v2 MLP diagnostic.

The constrained rich model is exported as a research artifact only.

The MLP is diagnostic only.

Neither is promoted into the product runtime because leave-corpus-out transfer is not strong enough.

## ViSQOL relationship

ViSQOL is an optional external project and is not the OpenVQ core.

OpenVQ's native analyzer performs its own:

- preprocessing;
- alignment;
- timing analysis;
- perceptual spectral analysis;
- temporal analysis;
- telecom diagnostics.

ViSQOL was used as expert evidence in historical Phase 3 work and remains a benchmark/optional external signal.

## POLQA relationship

POLQA is used only as a benchmark when lawful outputs are available.

OpenVQ:

- contains no POLQA source code;
- does not implement P.863;
- does not claim P.863 conformance;
- does not require POLQA at runtime.

A direct comparison must score the exact same audio pairs against the same human target.

## Runtime status

The current CLI and Android runtime expose the native analyzer and historical score paths.

The Phase 5.1 constrained research model is not integrated into the production scoring path because the Phase 5.1 validation itself shows poor unseen-corpus transfer.

The repaired preprocessing and analysis changes are integrated.

## Phase 6 architectural handoff

Phase 6 should preserve the Phase 5.1 native measurement foundation while testing whether a compact learned representation/mapper can generalize better.

The current evidence supports:

- using rich-v2 as interpretable auxiliary information;
- testing compact ANN architectures;
- keeping engineering gates outside the learned model as independent tests;
- using leave-corpus-out and processing-family transfer during development;
- reserving URGENT 2026 for a frozen final candidate.
