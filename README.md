# OpenVQ

OpenVQ is a source-available, independently derived, full-reference speech-quality research engine for telecom, network-testing, and drive-test applications.

It compares a known reference utterance with a degraded recording and produces an OpenVQ quality estimate together with interpretable timing, spectral, temporal, and telecom diagnostics.

OpenVQ is **not POLQA**, does not implement ITU-T P.863, and does not currently claim POLQA equivalence, P.863 conformance, or general superiority to POLQA.

## Project status

> **Trace V1 correctness erratum.** A confirmed FFT indexing defect affects the Phase 6.1 local sequence traces and therefore all three recorded Phase 6E sequence arms. Phase 6A native analysis is unaffected because it uses a separate correct FFT. Phase 6.2 introduces corrected Trace V2 and reruns the original model grid before training changes. See [the erratum](docs/PHASE6_1_TRACE_ERRATUM.md).

The latest research milestone is **Phase 6.1**.

This branch contains the current Phase 6.1 research implementation and evidence pipeline. The default `main` branch remains the stable baseline.

Phase 6.1 established a frozen native frontend, repaired validation infrastructure, a canonical five-corpus registry, a local sequence representation, fair summary-model baselines, compact sequence models, ONNX export, and an independent engineering promotion gate.

The frozen architecture-selection rule selected the 263,009-parameter hybrid sequence model. It improved completely held-out OpenACE to:

- Pearson 0.3990
- Spearman 0.4390
- normalized RMSE 0.2362

The full-development candidate then:

- exported successfully to ONNX;
- passed PyTorch-to-ONNX parity with maximum absolute difference 0.00000906 MOS;
- failed the independent engineering gate.

The engineering failure included:

- clean identity MOS 2.3929, below the required 4.4;
- two dropout severity reversals;
- one repeated-dropout reversal;
- one mixed-impairment reversal;
- two noise severity reversals.

The candidate was therefore **not promoted into the main CLI or Android MOS path**.

Full evidence is recorded in [Phase 6.1 results](docs/PHASE6_1_RESULTS.md).

## Phase 6.2 current result

Corrected Trace V2 changes the sequence-model ranking. Under the unchanged five-corpus, three-seed selection protocol, `learned_bands` is now selected with:

- worst held-corpus correlation 0.0894;
- mean held-corpus correlation 0.4317;
- worst normalized RMSE 0.3487.

The corrected hybrid model collapses under the same protocol, which makes the hybrid training/fusion contract the current diagnostic target.

See [Phase 6.2 results](docs/PHASE6_2_RESULTS.md).

Phase 6.2D found two additional training-contract issues. The existing temporal models have a small padding-context dependence, and the raw rich-v3 globals span roughly 95.6 million to 1 in standard deviation. Fold-fitted normalization substantially rescues hybrid but leaves OpenACE negative, so corrected learned-bands remains the preferred representation. Phase 6.2E now tests a padding-safe learned-bands architecture before any property losses are introduced.

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

`openvq-trace-v1-2026-09-26`

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
                 global rich-v3 features     local trace v1
                         |                         |
                         +------------+------------+
                                      |
                              research mappers
                    summary models / sequence models
```

The stable runtime foundation ends before the research mapper.

The latest neural candidate remains a research artifact because it did not satisfy the independent engineering gate.

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

The failed Phase 6E neural model is **not** the released Android MOS path.

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

The Phase 6.1 result narrows the next problem.

The local sequence representation appears worth keeping. The immediate research target is the learned quality mapping.

The next iteration should focus on:

- explicit identity constraints
- explicit impairment-order constraints
- corpus-balanced calibration
- domain-robust objectives
- seed stability
- preserving the positive OpenACE transfer
- retesting all five completely held corpora
- passing the independent engineering gate before external reserve consumption

Only after a candidate passes those gates should URGENT 2026 be opened.

## Scientific claim boundary

Current evidence supports describing OpenVQ as:

- an independently derived full-reference speech-quality research engine
- a native telecom/perceptual diagnostic system
- a reproducible research pipeline with frozen frontend and trace contracts
- a project with documented human-subjective, cross-domain, and engineering evaluation

Current evidence does **not** support describing OpenVQ as:

- POLQA-equivalent
- a general POLQA replacement
- P.863 compliant
- generally superior to POLQA
- externally validated at Phase 6.1

## Documentation

- [Phase 6.1 results](docs/PHASE6_1_RESULTS.md)
- [Stable algorithm baseline](docs/ALGORITHM.md)
- [Validation status](docs/VALIDATION.md)

The complete Phase 5.1 and Phase 6 research documentation is maintained in this branch under `docs/` and `validation/`.

## Licensing

OpenVQ is source-available under PolyForm Noncommercial 1.0.0.

Commercial use requires a separate written commercial license.

See:

- `LICENSE`
- `COMMERCIAL-LICENSE.md`
- `THIRD_PARTY.md`
