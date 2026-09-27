# Phase 6.1 results

> **Trace correctness erratum.** The Phase 6.1 sequence results below were generated with Trace V1, which has a confirmed FFT indexing defect in the trace-only spectral path. The numerical results remain historical development evidence, but all three sequence arms require reassessment with corrected Trace V2 before representation-level conclusions are treated as current. See [Phase 6.1 trace correctness erratum](PHASE6_1_TRACE_ERRATUM.md).

## Status

Phase 6.1 is the current OpenVQ research milestone.

It consolidates the completed Phase 6A-E evidence and records the Phase 6F promotion failure. No Phase 6 sequence model is promoted into the released scoring path.

## Phase 6A frontend freeze

Phase 6A repaired executable test coverage and alignment ambiguity.

Key changes include:

- assertion-independent Release tests;
- registered Phase 4 tests;
- a controlled failing-test harness proving Release tests execute;
- one shared preprocessing path;
- local alignment confidence;
- separate raw-input clipping;
- direct-match protection for already-correct transport delay;
- restored PLC-like repetition sensitivity;
- periodic and real-speech delay regressions.

Frozen frontend ID:

`openvq-frontend-phase6a-2026-09-26-v1`

Canonical evidence:

- source commit `d129658f084eaac28ed88f801c566ff2addb72f2`
- run `36232604130`
- artifact `10902877054`
- artifact SHA-256 `772ae5666a0edcefbfe835a1d53ea7d5d1d4477c248d6802f6c4f4e262496fb1`

The six-reference real-speech engineering suite completed with zero failures. The worst pure-delay score change was approximately 0.00005 MOS.

## Phase 6B fair summary-model test

Feature schema:

`openvq-rich-v3-2026-09-26-v1`

Rows:

- NISQA P501 240
- NISQA TEST_FOR 240
- OpenACE 144
- TCD 384
- TMHINT 1,455
- total 2,463

The balanced small MLP improved grouped known-domain development performance, but true leave-one-corpus-out transfer remained poor.

Balanced MLP leave-one-corpus-out:

| Held corpus | Pearson | Spearman | normalized RMSE |
| --- | ---: | ---: | ---: |
| NISQA P501 | 0.7641 | 0.7367 | 0.1662 |
| NISQA TEST_FOR | 0.6499 | 0.6026 | 0.1863 |
| OpenACE | -0.5280 | -0.4386 | 0.3762 |
| TCD | 0.5545 | 0.5765 | 0.2526 |
| TMHINT | 0.1187 | 0.2075 | 0.3293 |

This established that a larger mapper over the same pooled summaries was not sufficient.

Canonical evidence:

- run `36233995161`
- artifact `10905043210`
- artifact SHA-256 `8d5fefb87379862acf6385d0514d1ac0088c87762612a3c05601ff978a24d32b`

## Phase 6C registry

Phase 6C introduced explicit dataset and source identity infrastructure.

The registry records:

- dataset and protocol;
- exact waveform hashes;
- canonical source identity;
- speaker/system/family metadata where available;
- raw and normalized targets;
- exclusion reasons.

TMHINT uses the verified original release and native 1-to-5 listener scale.

NISQA full-reference preparation requires an explicit reference column and rejects ambiguous pairing.

URGENT 2026 is marked `frozen_external_only`.

## Phase 6D local trace

Trace schema:

`openvq-trace-v1-2026-09-26`

The trace preserves local evidence before utterance pooling:

- 10 ms hop;
- 20 ms analysis window;
- 64 reference auditory bands;
- 64 degraded auditory bands;
- reference activity;
- valid coverage;
- unmatched flag;
- local alignment confidence;
- local spectral similarity;
- reference and degraded RMS;
- mapped-time offset;
- rich-v3 global side vector.

All 2,463 development pairs were recreated and checked against the frozen Phase 6B evidence before trace export.

Canonical trace evidence:

- run `36247385269`
- artifact `10907723570`
- artifact SHA-256 `b4f709a6160a9de5ceb1afaa8f60e2e87a44c9a120688e97818d5a8e4bd80c40`
- development trace provenance SHA-256 `cbd5c8874026142b065d352335083640000e507ce1ba364614c236e31319c8fc`
- engineering trace provenance SHA-256 `ae6c65002093cb8f0a78b3829a25719467b53352e6009f57094b8e538c4f68b8`

## Phase 6E sequence comparison

Three architectures were evaluated with one entire corpus held out:

- `native_temporal`, 158,337 parameters;
- `learned_bands`, 260,961 parameters;
- `hybrid`, 263,009 parameters.

Each held-corpus result averages three fixed seeds:

`20260926`, `20260927`, `20260928`.

The selection rule was frozen before results:

1. maximize the weakest held-corpus value of Pearson/Spearman;
2. maximize mean held-corpus correlation;
3. minimize worst normalized RMSE.

### Complete held-corpus results

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

Architecture objectives:

| Model | worst held-corpus correlation | mean held-corpus correlation | worst normalized RMSE |
| --- | ---: | ---: | ---: |
| native temporal | -0.3733 | 0.2159 | 0.3677 |
| learned bands | -0.3088 | 0.1842 | 0.3788 |
| hybrid | **-0.1392** | 0.1096 | 0.5453 |

The frozen rule selected **hybrid** because its weakest held-corpus correlation was least negative.

### Important interpretation

The sequence representation produced a meaningful OpenACE improvement. The hybrid model was the first Phase 6 candidate in this line of work to turn completely held-out OpenACE positive:

- Pearson 0.3990
- Spearman 0.4390

The result does not establish corpus-invariant generalization. Hybrid transfer remained weak on P501, TEST_FOR, TCD, and TMHINT, and per-seed results were unstable.

The Phase 6E result therefore supports the local representation while rejecting the current training procedure as a final quality model.

## Phase 6F candidate

A deterministic full-development hybrid candidate was fitted on all 2,463 development rows.

Candidate record:

- mode `hybrid`
- seed `20260926`
- parameters 263,009
- selected epoch 2
- status development candidate only

ONNX export:

- ONNX SHA-256 `cea7b5e17cf5e7bf183e994cf7c8c24cf509f553d5d4c6ac5329bdb9b93ff7df`
- PyTorch state SHA-256 `0bb206fbd64cc149e72d9aa4d33368d441019dea51a37a0914de5d663283c372`

Parity:

- samples 64
- maximum absolute MOS difference 0.00000906
- tolerance 0.0001
- result pass

## Independent engineering gate

The candidate failed the promotion gate.

Identity:

- observed MOS 2.3929
- requirement at least 4.4

Pure delay:

- maximum absolute MOS change 0.0810
- requirement at most 0.20
- result pass

Monotonic failures:

- dropout 2 reversals;
- dropout count 1 reversal;
- mixed impairment 1 reversal;
- noise 2 reversals.

Examples:

| Family | Mild/cleaner condition | More severe condition | Incorrect direction |
| --- | ---: | ---: | --- |
| dropout | 20 ms 1.923 MOS | 640 ms 4.586 MOS | severe dropout scored better |
| noise | SNR 40 2.180 MOS | SNR 0 3.937 MOS | severe noise scored better |
| dropout count | 1 x 80 ms 4.500 MOS | 2 x 80 ms 5.000 MOS | more loss scored better |

Clipping and low-pass sequences were monotonic in the expected direction.

The failed gate prevents model promotion. The immutable product bundle step was intentionally skipped.

Recovery/candidate evidence:

- run `36284538942`
- artifact `10921181778`
- artifact SHA-256 `3912c8581c907d779e37e9728c3144208f4a70e25b7547396c1730c774203068`
- selection report SHA-256 `9c4f4a440e9f3c9ef4759b0015a5fc13f77a3dc9d4a25d695bb25eb734c95ae4`
- engineering report SHA-256 `cf8c8e9475c7f56511fb00ddc0b6836f89e2e6031326a851fb0c5e35d125d94d`
- parity report SHA-256 `ec7a81ce9206bd242e1448db690bbf8f73732cd60a6c087757d15e25a19523ab`

## Phase 6.1 conclusion

Phase 6.1 establishes four things.

1. The Phase 6A frontend and trace pipeline are reproducible and engineering-tested.
2. Sequence information contains useful cross-domain evidence that pooled summary features can lose.
3. The present sequence training procedure is unstable across domains and seeds.
4. Independent engineering gates remain necessary because subjective-data fitting alone can learn physically wrong quality relationships.

The next model iteration keeps the frozen frontend and trace representation and focuses on training constraints, calibration, domain robustness, and seed stability.

URGENT 2026 remains untouched.
