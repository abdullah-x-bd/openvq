# Phase 6.3 Frozen External Validation and Qualification

## Status

Phase 6.3 is being executed against the immutable Phase 6.2G candidate.

Candidate source:

`9c59fec790e0490c22b363474dd75b476f891f8f`

Pipeline:

`openvq-phase62g-749eaa80ea0a796cc15c`

Qualification artifact:

`10980470659`

Qualification ZIP SHA-256:

`407b04a1130b559ef59d54c63f3d40c02d24fb08c106ef80dc7fdf8f654d645c`

Bundle JSON SHA-256:

`9188ac73c104d53cb96b78e51a1e4a8bc1db9b02bcb660548faac945a5637e35`

The candidate weights, frontend, feature schema, Trace V2 contract, seed set, and ensemble equation are frozen.

Phase 6.3 is evaluation and qualification work. It does not authorize model tuning from external results.

## 6.3A Exact candidate execution

The evaluator is versioned separately from the candidate source.

It must:

- verify the qualification ZIP by immutable artifact ID and archive digest;
- verify the bundle JSON digest;
- validate the exact candidate source, frontend, feature schema, trace schema, trace implementation, model mode, seed set, and ensemble equation;
- verify all three ONNX file hashes;
- reproduce the existing protected engineering scores within 0.0001 MOS;
- retrieve the subjective guardrail report from its separate held-corpus artifact and verify its hash;
- reject a missing model, modified model, wrong trace version, or wrong bundle schema;
- test trained-model zero-padding invariance across varied trace durations;
- use NumPy 2.1.3 and ONNX Runtime 1.23.1;
- operate without POLQA software, credentials, or score files.

## 6.3B Real-speech engineering expansion

Use fixed development references only, never reserved labels.

Cover multiple speakers, languages, durations, and bandwidths and test identity, delay, mild noise including 40 and 60 dB SNR, resampling round trips, supported gain changes, polarity, silence padding, silence-only input, clipping, burst loss, repeated segments, clock drift, and time-scale changes.

Checks are classified as numerical invariance, expected physical ordering, or diagnostic-only absolute behavior. Synthetic transformations do not receive invented MOS targets.

## 6.3C Frozen external dataset and statistics

Before reserve scoring, freeze:

- exact reference source identity and audio hashes;
- dataset revision;
- source cluster, speaker, language, and system metadata;
- sample rate, duration, and format;
- inclusion and exclusion ledger;
- evaluator commit;
- candidate bundle;
- dependency versions;
- statistics implementation;
- 10,000 source-cluster bootstrap and seed.

Conflicting duplicate IDs, invalid audio, non-finite values, invalid references, and unexplained format mismatches fail closed.

## 6.3D One frozen external evaluation

After 6.3A-C preflight passes, run the qualified candidate once against eligible reserved human MOS.

Primary metrics:

- Pearson;
- Spearman;
- raw MOS RMSE;
- MAE;
- signed bias;
- floor and ceiling behavior;
- eligible and scored coverage;
- per-language and per-system results;
- source-cluster bootstrap uncertainty.

Historical research screen:

- Pearson >= 0.70;
- Spearman >= 0.70;
- RMSE <= 0.80 MOS.

A failed screen still completes the external evaluation. It blocks promotion.

## Optional 6.3E Published POLQA comparison

No POLQA runtime or new score generation is required.

The optional activity uses only already published lawful scores on exact matched recordings, records missing outputs and provenance, and remains development evidence.

It is not part of the Phase 6.3 human-rating completion criterion and cannot establish P.863 conformance.
