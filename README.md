# OpenVQ

OpenVQ is a source-available full-reference speech-quality research engine for telecom and drive-test applications. It compares a known reference utterance with a degraded recording and produces an OpenVQ quality estimate together with timing, spectral, temporal, and telecom diagnostics.

OpenVQ is independently derived. It is not POLQA, does not implement ITU-T P.863, and is not currently demonstrated to be equivalent or superior to POLQA.

## Current research status

The current research milestone is **Phase 6.1**.

Phase 6 established a frozen native frontend, repaired validation infrastructure, corpus-balanced summary-model baselines, a canonical dataset registry, a local sequence trace, and compact sequence-model experiments. Phase 6.1 records the completed sequence evaluation and the engineering-gate outcome.

The main result is:

> Sequence information contains useful cross-domain signal, but the selected hybrid candidate is not eligible for promotion because it fails independent engineering sanity checks.

The selected Phase 6E architecture was the 263,009-parameter **hybrid** model. It improved held-out OpenACE from the negative correlations seen in earlier phases to Pearson 0.3990 and Spearman 0.4390. It still showed weak or unstable transfer on other completely held corpora.

The full-development hybrid candidate exported to ONNX and passed PyTorch-to-ONNX parity with a maximum absolute difference of 0.0000091 MOS. It then failed the independent engineering gate:

- clean identity MOS 2.393, below the 4.4 requirement;
- two dropout severity reversals;
- one dropout-count reversal;
- one mixed-impairment reversal;
- two noise severity reversals.

The candidate was therefore not frozen as a product model and was not integrated into the main CLI or Android scoring path.

See [Phase 6.1 results](docs/PHASE6_1_RESULTS.md).

## Research phases

| Phase | Main goal | Main finding |
| --- | --- | --- |
| 1 | independent native full-reference engine | the core signal-processing and diagnostic path was viable |
| 2 | telecom failure-mode coverage | temporal and network-like impairments needed explicit treatment |
| 3 | optional expert fusion | strong TCD/NISQA results did not generalize to OpenACE |
| 4 | native-first constrained mapping | engineering behavior improved, but untouched external correlation gates failed |
| 5 | five-domain native refit | broader fitting helped but did not solve weakest-domain transfer |
| 5.1 | evidence, frontend, alignment, feature, and validation repair | richer measurements helped, while true leave-corpus-out transfer still failed |
| 6A | executable frontend correctness | Release tests became active and the frontend contract was frozen |
| 6B | fair summary-model comparison | balanced MLP gains were real, but summary features still failed corpus-invariant transfer |
| 6C-D | registry and local trace | canonical source identity and 2,463 local sequence traces were established |
| 6E | compact sequence-model comparison | hybrid won the frozen worst-corpus selection rule |
| 6F | candidate export and engineering gate | ONNX parity passed, independent engineering sanity failed |
| 6.1 | evidence consolidation and next-model diagnosis | representation improved, training constraints and calibration are now the main bottleneck |

## Native measurement engine

The native C++ engine includes:

- shared 48 kHz preprocessing;
- windowed-sinc sample-rate conversion;
- shared DC removal;
- global delay estimation;
- piecewise-continuous local alignment;
- direct-match protection for transport-only delay;
- clock-drift estimation;
- reference activity and active-speech coverage;
- lost active speech;
- matched active levels;
- FFT and ERB perceptual analysis;
- multi-resolution comparison;
- missing and added disturbance;
- coloration and noisiness;
- discontinuity and clipping;
- temporal-envelope and modulation similarity;
- spectral tilt;
- bad-section and worst-interval evidence;
- echo, choppiness, PLC-like repetition, and residual intrusion;
- alignment coverage and confidence;
- local Phase 6 trace export.

## Build

    cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
    cmake --build build --parallel
    ctest --test-dir build --output-on-failure

Analyze two WAV files:

    ./build/openvq_cli reference.wav degraded.wav

Export the Phase 6 local trace:

    ./build/openvq_trace_cli reference.wav degraded.wav trace.npz

Historical score paths remain available for reproducibility. They must not be interpreted as currently validated replacements for POLQA.

## Runtime status

The repaired native measurement engine is the stable runtime foundation.

The Phase 5.1 constrained mapper, Phase 6B summary models, and Phase 6E sequence models are research artifacts. The Phase 6E hybrid candidate is not promoted because it failed the engineering gate.

Android uses the same native preprocessing and analyzer sources. The experimental neural model is not the released Android quality path.

## Scientific claim boundary

Supported descriptions include:

- independently derived full-reference speech-quality research engine;
- reproducible timing, perceptual, temporal, and telecom diagnostics;
- frozen frontend and trace contracts;
- documented human-subjective development experiments;
- documented cross-domain failures and engineering-gate failures.

Unsupported descriptions include:

- POLQA-equivalent;
- general POLQA replacement;
- P.863 compliant;
- generally superior to POLQA;
- externally validated Phase 6.1 MOS model.

A direct POLQA comparison requires lawful POLQA outputs for the exact same audio pairs and a predeclared paired analysis.

## External reserve

URGENT 2026 subjective labels remain unconsumed by Phase 6.1 model selection.

The reserve is not opened for a candidate that fails the independent engineering gate.

## Reproducibility highlights

Phase 6A frontend freeze:

- run 36232604130
- artifact 10902877054
- artifact SHA-256 772ae5666a0edcefbfe835a1d53ea7d5d1d4477c248d6802f6c4f4e262496fb1c

Phase 6B summary experiment:

- run 36233995161
- artifact 10905043210
- artifact SHA-256 8d5fefb87379862acf6385d0514d1ac0088c87762612a3c05601ff978a24d32b

Phase 6D trace artifact:

- run 36247385269
- artifact 10907723570
- artifact SHA-256 b4f709a6160a9de5ceb1afaa8f60e2e87a44c9a120688e97818d5a8e4bd80c40

Phase 6E/F recovery and candidate evidence:

- run 36284538942
- artifact 10921181778
- artifact SHA-256 3912c8581c907d779e37e9728c3144208f4a70e25b7547396c1730c774203068
- selected mode hybrid
- ONNX SHA-256 cea7b5e17cf5e7bf183e994cf7c8c24cf509f553d5d4c6ac5329bdb9b93ff7df
- engineering gate failed

## Documentation

- [Documentation index](docs/README.md)
- [Phase 6.1 results](docs/PHASE6_1_RESULTS.md)
- [Architecture](docs/ARCHITECTURE.md)
- [Algorithm](docs/ALGORITHM.md)
- [Validation framework](docs/VALIDATION.md)
- [Validation history](docs/VALIDATION_HISTORY.md)
- [Dataset ledger](docs/DATASETS.md)
- [Reproducibility](docs/REPRODUCIBILITY.md)
- [Product integration](docs/PRODUCT_INTEGRATION.md)

## Licensing

OpenVQ is source-available under PolyForm Noncommercial 1.0.0. Commercial use requires a separate written commercial license. See LICENSE and COMMERCIAL-LICENSE.md.
