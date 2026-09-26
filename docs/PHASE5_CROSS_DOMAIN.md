# Phase 5 cross-domain redesign

**Status: historical development milestone, superseded by Phase 5.1.**

Phase 5 began because the frozen Phase 4 candidate failed untouched cross-domain validation.

Its question was:

> Can the existing 19 native OpenVQ features generalize if they are fitted across five known subjective domains with corpus-balanced weighting and worst-domain selection?

## Phase 4 evidence entering Phase 5

NISQA TEST_FOR, n = 240:

- Pearson 0.6148
- Spearman 0.5892
- RMSE 0.7503 MOS

TMHINT historical Phase 4 correlation diagnostic, n = 1,455:

- Pearson 0.2116
- Spearman 0.2580

Phase 5.1 later established that the TMHINT archive was the original TMHINT-QI release and that its 1-to-5 listener scores had been unnecessarily transformed in the Phase 4/5 workflow.

Therefore the old TMHINT Pearson/Spearman remain useful, but the old absolute-error figures are not corrected metrics.

## Phase 5 v1 design

Development evidence:

- TCD
- NISQA P501
- NISQA TEST_FOR
- OpenACE
- TMHINT

Primary score:

native-only.

Candidate families:

- regularized linear;
- regularized degree-two.

Constraints retained:

- high identity quality;
- sample-rate identity quality;
- pure-delay tolerance;
- monotonic behavior under deterministic impairment families.

Each subjective corpus received equal total fit weight.

Selection maximized the weakest Pearson/Spearman value across the five development corpora.

## Phase 5 v1 result

Selected model:

`phase5-native-crossdomain-2026-09-26-v1`

Basis:

`poly2`

Alpha:

`10.0`

Grouped development results:

| Corpus | Pearson | Spearman |
| --- | ---: | ---: |
| NISQA P501 | 0.6800 | 0.6812 |
| NISQA TEST_FOR | 0.5921 | 0.5715 |
| OpenACE | 0.7505 | 0.7838 |
| TCD | 0.6674 | 0.6748 |
| TMHINT | 0.3608 | 0.3510 |

Worst correlation:

`0.3510`

Mean correlation:

`0.6113`

The cross-domain retraining improved the failure picture but did not make the 19-feature mapping robust.

## Why Phase 5 v1 was not enough

Two conclusions drove Phase 5.1.

First, the weakest-domain result showed that simply changing coefficients on the same feature representation was not sufficient.

Second, the later Phase 5.1 audit found evidence-chain defects:

- the historical independent pure-delay gate had not actually executed;
- TMHINT release identity and score scale had been misinterpreted.

Because Phase 5 v1 used transformed TMHINT targets during fitting, it is retained as a diagnostic baseline rather than a release candidate.

## What Phase 5.1 changed

Phase 5.1 repaired:

- evidence provenance;
- shared preprocessing;
- alignment;
- active-speech coverage;
- rich temporal/tail representation;
- engineering validation;
- grouped and leave-corpus-out evaluation.

See:

- `docs/PHASE5_1.md`
- `docs/PHASE5_1_RESULTS.md`
- `docs/PHASE5_1_EVIDENCE_ERRATUM.md`

## Validation status

NISQA TEST_FOR and TMHINT are development evidence after earlier unblinding.

They cannot validate Phase 6.

URGENT 2026 remains untouched at the end of Phase 5.1 and is the preferred future external source once a Phase 6 candidate and protocol are frozen.
