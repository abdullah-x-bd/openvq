# Phase 4 robust fusion

## Objective

Phase 4 is intended to fix the generalization weakness exposed by EARS-EMO-OpenACE without hiding or rewriting the Phase 3 result.

The design target is not "make OpenACE look good." The target is a fusion rule that remains useful when one external expert becomes unreliable outside its familiar domain.

## Evidence motivating the redesign

On the available datasets, ViSQOL expert reliability changes materially by domain.

For the normalized Phase 3 speech-degradation feature, correlation with human MOS is strongly negative on both NISQA and TCD, meaning higher expert degradation tracks lower human quality well.

OpenACE breaks that pattern. The recomputed speech-mode ViSQOL score correlates only modestly with human MUSHRA, while audio mode is substantially stronger.

A fixed global coefficient therefore creates a single-point domain failure.

## Phase 4 design principles

1. Native OpenVQ evidence is the anchor.
2. External experts are optional and fallible.
3. No single expert receives unconditional dominant weight.
4. Expert influence is reduced when experts disagree with each other or with native evidence.
5. Expert disagreement itself is exposed as a diagnostic.
6. Phase 3 remains frozen and reproducible.
7. OpenACE can be used for diagnosis and development, but not as the final Phase 4 holdout.
8. Final Phase 4 claims require a new untouched subjective corpus.

## Development sequence

### A. Forensic feature extraction

Extract the complete normalized native OpenVQ feature vector for every OpenACE sample while preserving the already computed ViSQOL expert values.

Measure:

- individual native-feature association with human judgments
- expert association with human judgments
- Phase 3 contribution magnitudes
- score compression by codec
- failure modes by emotion
- expert disagreement

### B. Reliability-gated candidate models

Evaluate candidate fusion families such as:

- bounded external-expert corrections around a native anchor
- agreement-weighted expert corrections
- expert-consensus penalties
- disagreement-triggered fallback to native evidence
- monotonic models with explicit caps on any single expert contribution

Development evaluation must report each existing domain separately. A candidate that fixes OpenACE by materially breaking TCD or NISQA is not acceptable.

### C. Lock Phase 4

After selecting the design:

- assign a new model ID
- freeze coefficients and code
- record source commit and artifact hashes
- freeze the evaluation protocol before the new external holdout is scored

### D. New untouched validation

Use a subjective corpus not used for Phase 4 model selection.

If lawful POLQA values are available for exactly the same audio pairs, run a paired OpenVQ versus POLQA comparison.

## Product implication

Until Phase 4 passes new external validation, the frozen Phase 3 score should not be marketed as a general POLQA replacement.

The native diagnostics and experimental OpenVQ score can still be integrated into a drive-test application under an explicit experimental label, but the scientific claim must remain narrower than POLQA parity.
