# OpenVQ project guide

## Purpose

OpenVQ is a source-available, full-reference speech-quality engine intended for
telecom, network testing and drive-test applications.

It compares a clean reference recording with a degraded recording and returns
an estimated perceptual quality score plus diagnostic information about the
degradation.

OpenVQ is research software under active validation. It is not POLQA and does
not claim ITU-T P.863 conformance.

## Is OpenVQ based on ViSQOL?

No, not in the sense of being a ViSQOL wrapper or a renamed ViSQOL score.

OpenVQ contains its own native C++ analysis engine. That engine can run without
ViSQOL and independently calculates alignment, spectral and temporal
disturbance, missing and added energy, coloration, noise, discontinuity,
loudness, clipping, echo, choppiness and other telecom-oriented diagnostics.

Beginning in Phase 3, OpenVQ also allowed two scores from the separate Google
ViSQOL v3.3.3 program to enter the final fusion as expert features.

So the architecture is:

clean reference + degraded recording
-> native OpenVQ analysis
-> optional external ViSQOL expert signals
-> OpenVQ quality model
-> quality score and diagnostics

POLQA is never used as an input to OpenVQ. Where lawful POLQA results are
available, they are used only as an external benchmark.

## Why use external experts at all?

A full-reference quality model has to capture several different kinds of
perceptual damage. The native engine provides interpretable telecom-oriented
signals. ViSQOL provides an independently designed perceptual similarity view.

The validation work has shown that no single ViSQOL mode is universally
reliable. Speech mode worked very well on TCD and NISQA P501 but performed
poorly on OpenACE. Audio mode behaved much better on OpenACE and poorly on
TCD.

Phase 4 therefore treats expert behavior as domain-dependent rather than
assuming that one expert should always dominate.

## Major validation stages

### Engineering stage

Deterministic impairment tests established basic behavior under delay, packet
loss, noise, filtering, clipping, attenuation, clock drift, time scaling and
mixed degradations.

### Phase 2

TCD-VoIP exposed failure modes around echo and choppiness. New native
diagnostics were added.

### Phase 3

A frozen hybrid model was trained on TCD development data.

It performed strongly on the TCD held-out split and on the previously untouched
NISQA TEST P501 corpus.

It then failed badly on the independent EARS-EMO-OpenACE codec benchmark.

That failure is retained in the repository rather than removed or hidden.

### Phase 4

Phase 4 is a multi-domain redesign. TCD, P501 and OpenACE are now development
data. The model is selected using grouped cross-validation across all three
observed domains.

NISQA TEST FOR and TEST NSC are reserved as untouched final holdouts.

## What the current evidence supports

The native software, diagnostics, Android bindings and validation
infrastructure are functional.

Phase 3 showed strong prediction on TCD and P501 but did not generalize to
OpenACE. Therefore the project currently does not claim that OpenVQ is at
POLQA parity and does not recommend calling an OpenVQ score a POLQA score.

The Phase-4 holdouts determine whether the redesigned model is ready for a
stronger deployment claim.

## Repository map

- `src/` and `include/` contain the native C++ engine.
- `android/` contains Android JNI and Kotlin bindings.
- `validation/` contains dataset preparation, scoring, calibration and locked
  evaluation protocols.
- `validation/frozen/` contains immutable model records.
- `docs/ARCHITECTURE.md` explains the system components.
- `docs/VALIDATION_HISTORY.md` records all major results, including failures.
- `docs/REPRODUCING_VALIDATION.md` explains how the validation chain is
  reproduced.
- `validation/PHASE4_PROTOCOL.md` defines the current data roles and freeze
  rules.

## Licensing

OpenVQ is source-available under PolyForm Noncommercial 1.0.0. Commercial use
requires a separate written commercial license from the licensor.

Google ViSQOL is a separate upstream dependency and is not vendored into this
repository.
