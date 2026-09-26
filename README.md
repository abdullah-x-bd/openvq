# OpenVQ

OpenVQ is a source-available, full-reference speech-quality research engine for telecom and drive-test applications. It compares a known reference utterance with a degraded recording and produces a quality estimate plus interpretable timing, spectral, temporal, and telecom diagnostics.

OpenVQ is independently derived. It is **not POLQA**, does not implement ITU-T P.863, and is not currently demonstrated to be equivalent or superior to POLQA.

## Current project status

The project has completed **Phase 5.1: measurement and validation repair**.

The main conclusion is:

> The native measurement engine is substantially more rigorous than it was in Phases 1 to 5, and richer measurements improve known-domain prediction, but current hand-engineered mappings still do not generalize reliably to a completely unseen corpus.

Phase 6 is therefore the next research milestone.

See:

- [Phase 5.1 final results](docs/PHASE5_1_RESULTS.md)
- [Validation history](docs/VALIDATION_HISTORY.md)
- [Architecture](docs/ARCHITECTURE.md)
- [Dataset ledger](docs/DATASETS.md)
- [Reproducibility](docs/REPRODUCIBILITY.md)

## What happened across the phases

| Phase | Main goal | Main finding |
| --- | --- | --- |
| 1 | build an independent full-reference native engine | the core signal-processing path and diagnostics were viable |
| 2 | cover more telecom failure modes | echo, choppiness, residual intrusion, clipping, and network impairments needed explicit treatment |
| 3 | improve MOS mapping using optional ViSQOL experts | excellent TCD/NISQA results did not generalize to OpenACE; fixed expert trust was fragile |
| 4 | move to a native-first constrained mapper | engineering behavior became sane, but untouched TEST_FOR and TMHINT exposed cross-domain failure |
| 5 | refit the native mapper across five known domains | broader training helped but did not remove the weakest-domain problem |
| 5.1 | repair evidence, preprocessing, alignment, features, and validation | richer features and a small MLP helped, but leave-one-corpus-out transfer still failed badly |

## Phase 5.1 headline results

All Phase 5.1 figures below are development evidence. They are not untouched external validation.

### Fixed-evidence ablations

| Model | Worst correlation | Mean correlation | Worst normalized RMSE |
| --- | ---: | ---: | ---: |
| repaired frontend + legacy19 constrained poly2 | 0.3897 | 0.6257 | 0.2052 |
| repaired frontend + rich-v2 constrained poly2 | 0.4337 | 0.6370 | 0.1977 |
| repaired frontend + rich-v2 small MLP diagnostic | 0.5304 | 0.6772 | 0.1914 |

The richer feature representation helped. A compact neural mapper helped more.

However, the selected constrained rich model still failed when an entire corpus was held out:

- held-out OpenACE Pearson = **-0.4904**
- held-out TMHINT Pearson = **-0.0269**
- held-out TMHINT floor fraction = **77.4 percent**

This is why the Phase 5.1 research export was **not promoted into the product runtime**.

## Important evidence correction

Phase 5.1 discovered that the downloaded TMHINT archive is the **original TMHINT-QI release**, not the previously assumed version-II test set, and that the observed listener quality ratings are already on a **1-to-5** scale.

Consequences:

- historical TMHINT Pearson and Spearman remain useful correlation diagnostics because the old transform was positive affine;
- historical TMHINT RMSE, MAE, and bias based on that transform are not corrected absolute-error metrics;
- Phase 5 v1 used the transformed TMHINT target in fitting and is retained as a diagnostic baseline, not a clean release candidate.

See [Phase 5.1 evidence erratum](docs/PHASE5_1_EVIDENCE_ERRATUM.md).

## Native OpenVQ measurement engine

The native C++ engine now includes:

- shared 48 kHz preprocessing for base and advanced analysis;
- windowed-sinc sample-rate conversion;
- shared DC-removal path;
- global delay estimation;
- piecewise-continuous local alignment;
- multi-region clock-drift estimation;
- reference voice-activity detection;
- active-reference coverage and lost-active-speech measurement;
- matched active-speech level measurement;
- FFT and ERB perceptual analysis;
- multi-resolution 20 ms, 80 ms, and 200 ms comparison;
- missing and added disturbance;
- asymmetric disturbance;
- coloration;
- noisiness;
- discontinuity and dropout analysis;
- clipping;
- temporal-envelope similarity;
- modulation-spectrum similarity;
- spectral-tilt error;
- worst-interval pooling;
- echo;
- choppiness;
- residual intrusion;
- alignment coverage and confidence;
- percentile and tail statistics used by the Phase 5.1 rich-v2 research schema.

## Is OpenVQ based on ViSQOL?

No.

The native analyzer does not call ViSQOL and does not reimplement it.

Phase 3 used separately computed Google ViSQOL speech and audio scores as optional expert inputs. OpenACE showed that fixed trust in those experts was not robust across domains. Later native-first phases therefore treat external expert scores as historical/optional evidence rather than as the definition of OpenVQ quality.

Google ViSQOL is not vendored into this repository.

## Build

    cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
    cmake --build build --parallel
    ctest --test-dir build --output-on-failure

Analyze two WAV files with the native analyzer:

    ./build/openvq_cli reference.wav degraded.wav

The repository also retains the historical Phase 4 path for reproducibility:

    ./build/openvq_cli reference.wav degraded.wav --phase4

Phase 4 should not be interpreted as a currently validated production replacement for POLQA.

## Phase 5.1 runtime status

Phase 5.1 exports a reproducible constrained rich-v2 research model and a standalone Python predictor.

That model is **not wired into the main CLI or Android product path**. This is intentional. Phase 5.1 leave-corpus-out testing showed that promoting it would be scientifically premature.

The Android build does use the same repaired native preprocessing and analysis sources.

## Engineering validation

The final Phase 5.1 run passed:

- native C++ tests;
- preprocessing tests;
- repaired synthetic engineering validation;
- independent pure-delay validation;
- six-reference real-speech engineering validation;
- provenance and schema hashing.

Engineering correctness and subjective generalization are reported separately.

## Scientific claim boundary

OpenVQ currently supports claims such as:

- independently derived full-reference speech-quality research engine;
- reproducible native timing, perceptual, temporal, and telecom diagnostics;
- engineering-tested monotonic behavior across deterministic degradation families;
- documented human-MOS development experiments and failure analyses.

OpenVQ does **not** currently support claims such as:

- POLQA-equivalent;
- POLQA replacement;
- P.863 compliant;
- superior to POLQA overall;
- externally validated Phase 5.1 MOS model.

A future direct POLQA comparison requires lawful POLQA outputs for exactly the same audio pairs and the locked comparison protocol in `validation/LOCKED_POLQA_PROTOCOL.md`.

## Next milestone: Phase 6

Phase 6 should start from the repaired Phase 5.1 measurement and validation foundation.

The evidence supports investigating a compact ANN or similarly regularized learned representation/mapper, while preserving:

- the repaired preprocessing and alignment;
- rich-v2 measurements as interpretable inputs or auxiliary features;
- engineering sanity gates;
- grouped, processing-family, and leave-corpus-out development validation;
- a completely untouched final subjective corpus.

The selected URGENT 2026 validation subset must remain untouched until the Phase 6 candidate and evaluation protocol are frozen.

## Android

The Android library exposes the same native measurement engine as the desktop build.

    val json = OpenVqNative.analyzePcm16(reference, degraded, 48000)

The Android CMake build compiles the repaired shared preprocessing source used by the native library.

## Reproducibility

Canonical Phase 5.1 record:

- source commit: `4f96463411da8f9f6aecb370e8ac69ae2c228273`
- PR: `#12 Phase 5.1: measurement and validation repair`
- workflow run: `36219037262`
- artifact: `openvq-phase51`
- artifact ID: `10899193034`
- artifact SHA-256: `7e1e244074520e3e9e620fc29a602b99b094c6592a4bb954407b3e98b4949426`

## Licensing

OpenVQ is source-available under PolyForm Noncommercial 1.0.0. Commercial use requires a separate written commercial license from the licensor. See `LICENSE` and `COMMERCIAL-LICENSE.md`.
