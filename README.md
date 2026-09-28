# OpenVQ

OpenVQ is a source-available, independently derived, full-reference speech-quality research engine for telecom, network-testing, and drive-test applications.

It compares a known reference utterance with a degraded recording and produces an OpenVQ quality estimate together with interpretable timing, spectral, temporal, and telecom diagnostics.

OpenVQ is **not POLQA**, does not implement ITU-T P.863, and does not currently claim POLQA equivalence, P.863 conformance, or general superiority to POLQA.

## Project status

> **Trace V1 correctness erratum.** A confirmed FFT indexing defect affects the Phase 6.1 local sequence traces and therefore all three recorded Phase 6E sequence arms. Phase 6A native analysis is unaffected because it uses a separate correct FFT. Phase 6.2 introduces corrected Trace V2 and reruns the original model grid before training changes. See [the erratum](docs/PHASE6_1_TRACE_ERRATUM.md).

The latest research milestone is **Phase 6.2G**.

This branch contains the current Phase 6 research implementation and evidence pipeline. The default `main` branch remains the stable baseline.

Phase 6.2 repaired the Trace V1 spectral defect, established mathematically checked Trace V2, selected the padding-safe learned-bands representation, and then added a narrowly scoped clipping-order constraint without changing the frozen frontend, held-corpus protocol, seed set, or ensemble rule.

The final Phase 6.2G three-seed held-corpus results are:

| Held corpus | Pearson | Spearman | normalized RMSE |
| --- | ---: | ---: | ---: |
| NISQA P501 | 0.6551 | 0.6384 | 0.1943 |
| NISQA TEST_FOR | 0.5640 | 0.4656 | 0.1850 |
| OpenACE | 0.4213 | 0.4659 | 0.2135 |
| TCD | 0.5901 | 0.6129 | 0.2818 |
| TMHINT | 0.3541 | 0.3281 | 0.2919 |

Aggregate Phase 6.2G objective:

- worst held-corpus correlation 0.3281;
- mean held-corpus correlation 0.4887;
- worst normalized RMSE 0.2919.

Relative to Phase 6.2E, the weakest held-corpus correlation improved from 0.1900 to 0.3281, mean held-corpus correlation improved from 0.4551 to 0.4887, and worst normalized RMSE improved from 0.3062 to 0.2919.

The full-development three-seed Phase 6.2G ensemble then passed the unchanged protected engineering gate:

- clean identity MOS 4.6062;
- pure-delay maximum absolute change 0.00924 MOS;
- zero >0.12 MOS reversals for clipping, dropout, repeated dropout, noise, low-pass, and mixed impairments;
- PyTorch-to-ONNX parity passed for all three seeds at the 0.0001 MOS tolerance.

An immutable engineering-qualified development bundle was created:

- source commit `9c59fec790e0490c22b363474dd75b476f891f8f`;
- pipeline ID `openvq-phase62g-749eaa80ea0a796cc15c`;
- workflow run `36422583627`;
- qualification artifact `10980470659`;
- artifact ZIP SHA-256 `407b04a1130b559ef59d54c63f3d40c02d24fb08c106ef80dc7fdf8f654d645c`.

Phase 6.2G is an **engineering-qualified development candidate**. It is not yet an externally validated model and has not been promoted into the stable CLI or Android MOS path.

URGENT 2026 subjective labels remain untouched.

See [Phase 6.2 results](docs/PHASE6_2_RESULTS.md) and [Phase 6.2 execution record](docs/PHASE6_2_PLAN.md).

## Why OpenVQ exists

Full-reference speech-quality measurement is useful when the clean source signal is known and the received or processed version can be compared against it.

OpenVQ is designed around three goals:

1. keep the native signal-processing path independently derived and interpretable;
2. expose telecom-relevant diagnostics instead of only a single scalar score;
3. treat model fitting, engineering sanity, cross-domain generalization, and external validation as separate scientific requirements.

The project deliberately preserves failed experiments and holdout failures rather than hiding them behind one headline metric.

## What OpenVQ measures

### Frontend and timing

- PCM/float WAV ingestion
- mono preparation
- 48 kHz fullband internal processing
- windowed-sinc resampling
- DC removal
- global delay
- clock drift
- bounded local alignment
- alignment confidence
- alignment coverage
- direct-match protection for transport-only delay

### Active-speech accounting

- reference activity
- active duration
- active coverage
- lost active speech
- matched reference/degraded active levels
- level mismatch

### Spectral and perceptual evidence

- FFT spectral comparison
- ERB auditory bands
- bandwidth classification
- missing disturbance
- added disturbance
- asymmetric disturbance
- coloration
- noisiness
- spectral tilt
- multi-resolution 20 ms, 80 ms, and 200 ms comparison

### Temporal and telecom evidence

- discontinuity
- dropout behavior
- bad sections
- worst intervals
- clipping
- temporal-envelope similarity
- modulation-spectrum similarity
- echo
- choppiness
- repeated-waveform or PLC-like freeze evidence
- residual intrusion

### Phase 6 local representation

The Phase 6 research branch additionally exports a local trace with:

- 10 ms hop
- 20 ms analysis window
- 64 reference auditory bands
- 64 degraded auditory bands
- reference activity
- valid coverage
- unmatched-state flag
- local alignment confidence
- local similarity
- reference/degraded RMS
- mapped-time offset
- rich-v3 global side information

Trace schema:

`openvq-trace-v2-2026-09-27`

## Architecture

```
reference audio ----------------------+
                                      |
                                      v
                           shared native frontend
                                      |
degraded audio -----------------------+
                                      |
                                      v
                    alignment + active-speech accounting
                                      |
                  +-------------------+-------------------+
                  |                                       |
                  v                                       v
          perceptual analysis                    telecom/coverage analysis
                  |                                       |
                  +-------------------+-------------------+
                                      |
                         +------------+------------+
                         |                         |
                         v                         v
                 global rich-v3 features     local Trace V2
                         |                         |
                         +------------+------------+
                                      |
                              research mappers
                    summary models / sequence models
```

The stable runtime foundation ends before the research mapper.

The Phase 6.2G neural ensemble is an engineering-qualified development artifact. External validation is still required before any release-path promotion.

## Development history

### Phase 1

Built the independent C++ full-reference engine, Android integration, deterministic degradation tests, alignment, perceptual-band disturbance measures, and initial quality aggregation.

Main lesson: the native signal-processing path worked, but engineering measurements alone did not establish human-MOS accuracy.

### Phase 2

Expanded explicit telecom failure modes:

- echo
- choppiness
- local temporal edits
- short holes
- residual intrusion
- clipping
- codec/network laboratory workflows

Main lesson: speech quality is strongly multidimensional and cannot be represented reliably by a narrow spectral score.

### Phase 3

Added pinned Google ViSQOL v3.3.3 speech/audio outputs as optional external expert features and fitted a nonlinear monotonic mapper using TCD development evidence.

Frozen model:

`phase3-tcd-only-2026-09-24-f099129`

TCD held-out test, n=60:

- Pearson 0.9541
- Spearman 0.9375
- RMSE 0.4335 MOS
- MAE 0.3665 MOS

NISQA P501, n=240:

- Pearson 0.8185
- Spearman 0.8209
- RMSE 0.6011 MOS
- MAE 0.4904 MOS

OpenACE then exposed the failure:

- frozen Phase 3 OpenVQ Pearson 0.1607
- frozen Phase 3 OpenVQ Spearman 0.1465
- published POLQA Pearson 0.7939
- published POLQA Spearman 0.7818

The failure analysis showed that fixed expert trust, especially in speech-mode ViSQOL, did not generalize across domains.

### Phase 4

Moved back to a native-first constrained degree-two model.

The final Phase 4 candidate passed deterministic engineering tests but failed untouched NISQA TEST_FOR correlation gates.

NISQA TEST_FOR, n=240:

- Pearson 0.6148
- Spearman 0.5892
- RMSE 0.7503 MOS

TMHINT historical correlation:

- Pearson 0.2116
- Spearman 0.2580

Phase 4 was therefore engineering-valid but scientifically weak as a general quality model.

### Phase 5

Fitted the native mapper across five known domains:

- TCD
- NISQA P501
- NISQA TEST_FOR
- OpenACE
- TMHINT

The broader fit improved average performance, but the weakest-domain problem remained.

Phase 5.1 later established that Phase 5 had also used an unnecessary transformed TMHINT target, so the Phase 5 model is retained as a historical diagnostic baseline rather than a clean release candidate.

### Phase 5.1

Phase 5.1 repaired the evidence chain and frontend.

Key changes:

- restored a previously suppressed independent delay assertion
- identified the downloaded TMHINT archive correctly as original TMHINT-QI
- restored native 1-to-5 TMHINT targets
- unified preprocessing
- unified DC removal
- repaired alignment
- added active-speech coverage
- added lost-active-speech accounting
- added alignment confidence
- expanded the global feature representation from legacy19 to rich-v2
- repaired grouped, processing-family, and leave-one-corpus-out evaluation

Fixed-evidence development results:

| Model | Worst correlation | Mean correlation | Worst normalized RMSE |
| --- | ---: | ---: | ---: |
| legacy19 constrained poly2 | 0.3897 | 0.6257 | 0.2052 |
| rich-v2 constrained poly2 | 0.4337 | 0.6370 | 0.1977 |
| rich-v2 MLP diagnostic | 0.5304 | 0.6772 | 0.1914 |

The decisive leave-one-corpus-out test still failed:

| Held corpus | Pearson | Spearman | normalized RMSE |
| --- | ---: | ---: | ---: |
| NISQA P501 | 0.6656 | 0.6547 | 0.1905 |
| NISQA TEST_FOR | 0.5296 | 0.5175 | 0.2229 |
| OpenACE | -0.4904 | -0.4114 | 0.3760 |
| TCD | 0.3893 | 0.4438 | 0.2350 |
| TMHINT | -0.0269 | 0.0590 | 0.5047 |

This showed that richer utterance summaries were still not enough to learn a corpus-invariant quality function.

### Phase 6A

Phase 6A focused on frontend correctness.

It:

- removed reliance on disabled C assertions in Release tests
- registered previously unregistered tests
- added a controlled failure harness
- repaired periodic-signal alignment ambiguity
- repaired PLC-like repetition detection
- added direct-match protection for pure transport delay
- separated raw-input clipping
- froze the frontend contract

Frontend ID:

`openvq-frontend-phase6a-2026-09-26-v1`

Canonical run:

`36232604130`

The six-reference real-speech engineering suite completed with zero failures.

### Phase 6B

Phase 6B tested whether a fair, corpus-balanced ANN over global summary features could solve the Phase 5.1 problem.

Balanced MLP leave-one-corpus-out:

| Held corpus | Pearson | Spearman | normalized RMSE |
| --- | ---: | ---: | ---: |
| NISQA P501 | 0.7641 | 0.7367 | 0.1662 |
| NISQA TEST_FOR | 0.6499 | 0.6026 | 0.1863 |
| OpenACE | -0.5280 | -0.4386 | 0.3762 |
| TCD | 0.5545 | 0.5765 | 0.2526 |
| TMHINT | 0.1187 | 0.2075 | 0.3293 |

The ANN improvement was real, but the global summary representation still did not produce robust unseen-corpus transfer.

### Phase 6C

Introduced a canonical dataset/source registry.

The registry records:

- exact reference/degraded paths and hashes
- canonical source identity
- dataset ancestry
- subjective protocol
- speaker/system/family metadata where available
- raw and normalized targets
- exclusion reasons

Canonical source identity uses SHA-256 of exact reference waveform bytes.

### Phase 6D

Exported the local sequence representation for all 2,463 development pairs after recreating the audio and verifying it against frozen Phase 6B evidence.

Development counts:

- NISQA P501 240
- NISQA TEST_FOR 240
- OpenACE 144
- TCD 384
- TMHINT 1,455
- total 2,463

Canonical trace artifact:

- run `36247385269`
- artifact `10907723570`
- SHA-256 `b4f709a6160a9de5ceb1afaa8f60e2e87a44c9a120688e97818d5a8e4bd80c40`

### Phase 6E

Evaluated three compact sequence architectures:

- `native_temporal`, 158,337 parameters
- `learned_bands`, 260,961 parameters
- `hybrid`, 263,009 parameters

Each architecture was tested with one entire corpus held out and three fixed seeds.

Complete held-corpus results:

| Model | Held corpus | Pearson | Spearman | normalized RMSE |
| --- | --- | ---: | ---: | ---: |
| native temporal | P501 | 0.6161 | 0.6190 | 0.2174 |
| native temporal | TEST_FOR | 0.2234 | 0.2082 | 0.3677 |
| native temporal | OpenACE | -0.3733 | -0.3496 | 0.3437 |
| native temporal | TCD | 0.3169 | 0.3198 | 0.3286 |
| native temporal | TMHINT | 0.3136 | 0.3114 | 0.2403 |
| learned bands | P501 | 0.6482 | 0.6573 | 0.2123 |
| learned bands | TEST_FOR | 0.0887 | 0.0721 | 0.3733 |
| learned bands | OpenACE | -0.3026 | -0.3088 | 0.3788 |
| learned bands | TCD | 0.2526 | 0.3284 | 0.3069 |
| learned bands | TMHINT | 0.2569 | 0.2715 | 0.2438 |
| hybrid | P501 | 0.2312 | 0.1581 | 0.5061 |
| hybrid | TEST_FOR | -0.0456 | 0.0213 | 0.4035 |
| hybrid | OpenACE | 0.3990 | 0.4390 | 0.2362 |
| hybrid | TCD | 0.1798 | 0.1758 | 0.3351 |
| hybrid | TMHINT | -0.1287 | -0.1392 | 0.5453 |

Frozen selection objective:

| Model | Worst held-corpus correlation | Mean held-corpus correlation | Worst normalized RMSE |
| --- | ---: | ---: | ---: |
| native temporal | -0.3733 | 0.2159 | 0.3677 |
| learned bands | -0.3088 | 0.1842 | 0.3788 |
| hybrid | **-0.1392** | 0.1096 | 0.5453 |

The frozen rule selected **hybrid** because its weakest held-corpus correlation was least negative.

The most important scientific gain was OpenACE. Earlier approaches reversed the ordering of completely held-out OpenACE samples. Hybrid moved that result into positive correlation.

This did not solve overall generalization. Other corpora remained weak and per-seed outcomes were unstable.

### Phase 6F and Phase 6.1

A deterministic full-development hybrid candidate was fitted on all 2,463 development rows.

Candidate:

- architecture `hybrid`
- parameters 263,009
- seed `20260926`
- selected epoch 2

ONNX parity:

- 64 samples
- maximum absolute MOS difference 0.00000906
- tolerance 0.0001
- result pass

Independent engineering gate:

- identity MOS 2.3929, fail
- pure-delay maximum change 0.0810 MOS, pass
- dropout 2 reversals, fail
- dropout-count 1 reversal, fail
- mixed 1 reversal, fail
- noise 2 reversals, fail
- clipping monotonicity, pass
- low-pass monotonicity, pass

The failed gate intentionally stopped product bundling.

Phase 6.1 therefore retains the frontend and sequence representation but rejects the current learned mapper as a release model.

### Phase 6.2

Phase 6.2 corrected the local trace and then tightened the learned-model contract in controlled stages.

- 6.2A-B corrected the Trace V1 FFT indexing defect, added direct numerical correctness tests, and froze Trace V2.
- 6.2C reran the original sequence grid unchanged and selected corrected `learned_bands`.
- 6.2D diagnosed padding-context dependence and hybrid global-feature scale mismatch.
- 6.2E introduced padding-safe masking and per-frame channel LayerNorm. Every held corpus became positively correlated.
- 6.2F aligned full-development qualification with the three-seed ensemble. It passed all protected checks except one clipping-severity reversal.
- 6.2G added a clipping-order property constraint using separate fixtures with thresholds disjoint from the protected gate.

Phase 6.2G passed the predeclared subjective no-regression guardrails and improved the aggregate held-corpus objective to 0.3281 worst correlation, 0.4887 mean correlation, and 0.2919 worst normalized RMSE.

The unchanged protected engineering gate then passed with zero failures. The formerly failing clipping sequence became:

| Protected clipping threshold | MOS |
| --- | ---: |
| 0.95 | 4.4760 |
| 0.50 | 2.0543 |
| 0.25 | 1.7905 |
| 0.08 | 1.5014 |

The final three ONNX models passed parity with maximum absolute MOS differences of 0.00000119, 0.00000095, and 0.00000167.

The resulting immutable development bundle is `openvq-phase62g-749eaa80ea0a796cc15c`.

URGENT 2026 remains untouched. The next scientific step is one-time external validation of this frozen candidate under the reserved protocol.

## Datasets and evidence status

| Dataset | Current role |
| --- | --- |
| TCD-VoIP | development evidence |
| NISQA P501 | development evidence |
| NISQA TEST_FOR | development evidence |
| OpenACE | development evidence and historical public per-file POLQA benchmark |
| TMHINT-QI original | development evidence |
| NISQA TEST_NSC | not consumed through the current workflow path |
| URGENT 2026 | untouched external reserve |

### OpenACE and POLQA

OpenACE is particularly useful because its public metadata contains exact reference/degraded filenames, human MUSHRA, and per-file POLQA values for 143 samples.

It can therefore support a direct historical paired OpenVQ/POLQA benchmark.

It cannot serve as untouched Phase 6.1 evidence because OpenACE has already influenced model development.

## Build and use

### Stable main branch

```bash
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build --parallel
ctest --test-dir build --output-on-failure
```

Analyze a reference/degraded pair:

```bash
./build/openvq_cli reference.wav degraded.wav
```

Historical calibration and optional expert paths remain available for reproducibility.

### Phase 6 research branch

```bash
git checkout validation/phase6
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build --parallel
ctest --test-dir build --output-on-failure
```

Export the local trace as JSON:

```bash
./build/openvq_trace_cli reference.wav degraded.wav > trace.json
```

The Phase 6 research workflows under `validation/` reproduce dataset preparation, summary features, local traces, sequence-model evaluation, parity testing, engineering gating, and external-validation preparation.

## Android

OpenVQ includes Android JNI/Kotlin integration.

The Android native build shares the OpenVQ C++ analyzer sources.

The Phase 6 research branch also includes the local trace-native path.

The Phase 6.2G neural ensemble is **not yet** the released Android MOS path. Android integration remains on the native analyzer path until external validation and release qualification are complete.

## ViSQOL relationship

OpenVQ is not based on ViSQOL.

Google ViSQOL was used as an optional external expert in historical Phase 3 work and remains useful as an external benchmark.

ViSQOL is not vendored into this repository.

The native analyzer independently performs its own preprocessing, alignment, timing analysis, spectral/perceptual analysis, temporal analysis, and telecom diagnostics.

## POLQA relationship

OpenVQ is not POLQA.

It contains no POLQA source code and does not implement P.863.

POLQA is treated only as an external benchmark when lawful scores are available for the exact same audio pairs.

A direct comparison should use:

- the same reference/degraded files
- the same human target
- paired error statistics
- a predeclared protocol
- clear scope limits

No current result establishes general POLQA equivalence or superiority.

## Validation philosophy

OpenVQ separates:

1. frontend correctness
2. engineering sanity
3. development subjective fit
4. completely held-corpus transfer
5. untouched external validation
6. external benchmark comparison

A model can have good human-MOS fit and still violate basic physical behavior. Phase 6.1 demonstrated exactly that.

A model can also pass engineering tests and still fail cross-domain subjective prediction. Phase 4 demonstrated that.

Both requirements matter.

## Reproducibility

### Phase 5.1

- source `4f96463411da8f9f6aecb370e8ac69ae2c228273`
- run `36219037262`
- artifact `10899193034`
- artifact SHA-256 `7e1e244074520e3e9e620fc29a602b99b094c6592a4bb954407b3e98b4949426`

### Phase 6A

- source `d129658f084eaac28ed88f801c566ff2addb72f2`
- run `36232604130`
- artifact `10902877054`
- artifact SHA-256 `772ae5666a0edcefbfe835a1d53ea7d5d1d4477c248d6802f6c4f4e262496fb1`

### Phase 6B

- run `36233995161`
- artifact `10905043210`
- artifact SHA-256 `8d5fefb87379862acf6385d0514d1ac0088c87762612a3c05601ff978a24d32b`

### Phase 6D

- run `36247385269`
- artifact `10907723570`
- artifact SHA-256 `b4f709a6160a9de5ceb1afaa8f60e2e87a44c9a120688e97818d5a8e4bd80c40`

### Phase 6E/F recovery

- run `36284538942`
- artifact `10921181778`
- artifact SHA-256 `3912c8581c907d779e37e9728c3144208f4a70e25b7547396c1730c774203068`
- ONNX SHA-256 `cea7b5e17cf5e7bf183e994cf7c8c24cf509f553d5d4c6ac5329bdb9b93ff7df`

### Phase 6.2 Trace V2

- source `bc2637808f1299570eb74e4b2282da1532fc53f2`
- run `36306154897`
- artifact `10928082645`
- artifact SHA-256 `1cfb4066a2461c08166cf10555ce287aa63310d68a1186a7573a39b4b0b0aff6`

### Phase 6.2 corrected-trace baseline

- artifact `10931420305`
- artifact SHA-256 `161e19fb8964177bdc00879ea8fc4606bfac0eb163a8dda669d4d1e07c30deea`

### Phase 6.2D diagnostics

- run `36319146056`
- diagnostics artifact `10932370265`
- diagnostics SHA-256 `b2b154f0f9837a8b9f1bdb48b7eb8a65dddc9a5cf48f089af8b824615a2f1f4a`
- normalized-hybrid artifact `10932529605`
- normalized-hybrid SHA-256 `d0667c42cfbccaca345feedcb8890d11e08f1177e4a5c844c3ceca33257c2fb4`

### Phase 6.2E padding-safe model

- run `36330893596`
- artifact `10937636963`
- artifact ZIP SHA-256 `7d222696a891cfbb4d8ae6dda8131c259d41840a187d0319ad886d96ec43ce0b`

### Phase 6.2F engineering qualification

- run `36397704754`
- qualification artifact `10961376404`
- artifact ZIP SHA-256 `2b0c1aeaf1aaa20b5650115a0c4089276ca1a4dc10a4df5ed235c369f2cec852`
- result: one protected clipping reversal, no bundle promotion

### Phase 6.2G engineering-qualified candidate

- source `9c59fec790e0490c22b363474dd75b476f891f8f`
- run `36422583627`
- clipping-constraint artifact `10969564021`
- held-corpus artifact `10975650939`
- qualification artifact `10980470659`
- qualification artifact ZIP SHA-256 `407b04a1130b559ef59d54c63f3d40c02d24fb08c106ef80dc7fdf8f654d645c`
- pipeline ID `openvq-phase62g-749eaa80ea0a796cc15c`
- seed 20260926 ONNX SHA-256 `7bb40fc128ecc902271be93076a3af21b35f1f142ddcf3cb9b6798d90b1f0821`
- seed 20260927 ONNX SHA-256 `64cb9ba8e769b8c8e2801e4c1fe3b143ddf2ca0b033ce68885430ce85a32981d`
- seed 20260928 ONNX SHA-256 `8ed003ef19bd6b640951f0b1ee6b02c47b5a4573f17eba7e8d477e06685b514b`

## Repository structure

```
android/        Android JNI/Kotlin integration
docs/           architecture, validation, datasets, history, results
include/        public C++ headers
python/         calibration and analysis utilities
src/            native C++ engine
tests/          native regression tests
tools/          degradation and external-metric helpers
validation/     dataset preparation, experiments, protocols, evidence
.github/        CI and validation workflows
```

## What comes next

Phase 6.2 development is complete through the engineering-qualified Phase 6.2G bundle.

The next step is **Phase 6.3 external validation**. The exact 6.2G bundle must remain frozen while the external protocol is finalized and the URGENT 2026 full-reference source map is independently verified.

The intended order is:

1. freeze the exact 6.2G candidate and its provenance;
2. verify the URGENT full-reference source map, exclusions, and bootstrap unit without using subjective labels for tuning;
3. consume the URGENT reserve once under the predeclared protocol;
4. report Pearson, Spearman, MOS RMSE, MAE, signed bias, saturation, coverage, and source-cluster bootstrap intervals;
5. if the frozen external result is adequate, obtain lawful POLQA scores on the exact same eligible pairs;
6. run the predeclared paired OpenVQ-versus-POLQA error comparison.

If URGENT results influence the model, URGENT becomes development evidence and a changed candidate requires genuinely new reserved evidence.

## Scientific claim boundary

Current evidence supports describing OpenVQ as:

- an independently derived full-reference speech-quality research engine;
- a native telecom/perceptual diagnostic system;
- a reproducible research pipeline with frozen frontend and Trace V2 contracts;
- a project with documented human-subjective, cross-domain, deployment-parity, and engineering evaluation;
- a project with an engineering-qualified Phase 6.2G development candidate.

Current evidence does **not** support describing OpenVQ as:

- POLQA-equivalent;
- a general POLQA replacement;
- P.863 compliant;
- generally superior to POLQA;
- externally validated on the untouched URGENT 2026 reserve.

## Documentation

- [Phase 6.2 results](docs/PHASE6_2_RESULTS.md)
- [Phase 6.2 execution record](docs/PHASE6_2_PLAN.md)
- [Phase 6.1 historical results](docs/PHASE6_1_RESULTS.md)
- [Phase 6.1 Trace V1 erratum](docs/PHASE6_1_TRACE_ERRATUM.md)
- [Algorithm](docs/ALGORITHM.md)
- [Validation framework](docs/VALIDATION.md)
- [Phase 6 external protocol](validation/PHASE6_EXTERNAL_PROTOCOL.md)

The complete Phase 5.1 and Phase 6 research documentation is maintained in this branch under `docs/` and `validation/`.

## Licensing

OpenVQ is source-available under PolyForm Noncommercial 1.0.0.

Commercial use requires a separate written commercial license.

See:

- `LICENSE`
- `COMMERCIAL-LICENSE.md`
- `THIRD_PARTY.md`
