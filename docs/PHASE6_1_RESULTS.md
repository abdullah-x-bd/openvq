# Phase 6.1 research status

Research branch:

`validation/phase6`

## Completed work

Phase 6 established:

- a frozen and regression-tested native frontend;
- fair summary-model baselines;
- canonical source and dataset provenance;
- 2,463 verified local sequence traces;
- three compact sequence-model architectures;
- five completely held-corpus evaluations per architecture;
- three fixed seeds per held corpus;
- deterministic full-development candidate fitting;
- ONNX export and parity testing;
- an independent learned-model engineering gate.

## Sequence-model selection

The frozen selection rule maximized the weakest held-corpus Pearson/Spearman value, then mean held-corpus correlation, then lower worst normalized RMSE.

| Model | worst held-corpus correlation | mean held-corpus correlation | worst normalized RMSE |
| --- | ---: | ---: | ---: |
| native temporal | -0.3733 | 0.2159 | 0.3677 |
| learned bands | -0.3088 | 0.1842 | 0.3788 |
| hybrid | **-0.1392** | 0.1096 | 0.5453 |

The rule selected **hybrid**.

Hybrid held-corpus results:

| Corpus | Pearson | Spearman | normalized RMSE |
| --- | ---: | ---: | ---: |
| NISQA P501 | 0.2312 | 0.1581 | 0.5061 |
| NISQA TEST_FOR | -0.0456 | 0.0213 | 0.4035 |
| OpenACE | 0.3990 | 0.4390 | 0.2362 |
| TCD | 0.1798 | 0.1758 | 0.3351 |
| TMHINT | -0.1287 | -0.1392 | 0.5453 |

The positive held-out OpenACE result shows that local sequence information contains useful generalizable evidence. Overall cross-domain transfer and seed stability remain weak.

## Final development candidate

- mode `hybrid`
- parameters 263,009
- development rows 2,463
- seed `20260926`

ONNX parity:

- 64 samples
- maximum absolute MOS difference 0.00000906
- tolerance 0.0001
- pass

## Engineering promotion gate

The candidate failed.

- identity MOS 2.3929, requirement at least 4.4;
- pure-delay maximum change 0.0810 MOS, pass;
- dropout 2 reversals;
- dropout count 1 reversal;
- mixed impairment 1 reversal;
- noise 2 reversals.

The candidate is not a release model and is not integrated into main.

## Canonical evidence

Phase 6A:

- run `36232604130`
- artifact `10902877054`
- artifact SHA-256 `772ae5666a0edcefbfe835a1d53ea7d5d1d4477c248d6802f6c4f4e262496fb1`

Phase 6B:

- run `36233995161`
- artifact `10905043210`
- artifact SHA-256 `8d5fefb87379862acf6385d0514d1ac0088c87762612a3c05601ff978a24d32b`

Phase 6D:

- run `36247385269`
- artifact `10907723570`
- artifact SHA-256 `b4f709a6160a9de5ceb1afaa8f60e2e87a44c9a120688e97818d5a8e4bd80c40`

Phase 6E/F recovery:

- run `36284538942`
- artifact `10921181778`
- artifact SHA-256 `3912c8581c907d779e37e9728c3144208f4a70e25b7547396c1730c774203068`
- ONNX SHA-256 `cea7b5e17cf5e7bf183e994cf7c8c24cf509f553d5d4c6ac5329bdb9b93ff7df`

## External validation status

URGENT 2026 remains untouched.

No Phase 6.1 result establishes POLQA equivalence, P.863 conformance, or general superiority to POLQA.
