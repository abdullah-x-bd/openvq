# Dataset ledger

This ledger records how subjective datasets have been used and whether they remain eligible as untouched evidence.

A dataset becomes development evidence once its labels or results influence model design.

## Development corpora

### TCD-VoIP

Rows used in Phase 6:

384

Use includes Phases 2-6 development, Phase 6A real-speech engineering references, Phase 6B summary modeling, and Phase 6E leave-one-corpus-out testing.

Status:

Development evidence.

### NISQA TEST P501

Source:

https://zenodo.org/records/4728081

Rows used in Phase 6:

240

Historical Phase 3 external result:

- Pearson 0.8185
- Spearman 0.8209
- RMSE 0.6011 MOS

Phase 6 use:

- summary-model development;
- source-verified trace export;
- completely held-corpus sequence evaluation.

Status:

Development evidence.

### NISQA TEST_FOR

Rows used in Phase 6:

240

Historical Phase 4 untouched result:

- Pearson 0.6148
- Spearman 0.5892
- RMSE 0.7503 MOS

Phase 6 use:

- summary-model development;
- source-verified trace export;
- completely held-corpus sequence evaluation.

Status:

Development evidence.

### NISQA TEST_NSC

The public archive path used by OpenVQ has not exposed the expected TEST_NSC directory.

No OpenVQ TEST_NSC score has been reported.

Status:

Not consumed through the current workflow path.

### EARS-EMO-OpenACE

Source:

https://huggingface.co/datasets/mcernak/EARS-EMO-OpenACE

Rows:

144

The dataset contains EVS, LC3, LC3Plus, and Opus conditions with human MUSHRA ratings. Published per-file POLQA values are available for 143 samples.

Historical Phase 3 result:

- OpenVQ Pearson 0.1607
- OpenVQ Spearman 0.1465
- published POLQA Pearson 0.7939
- published POLQA Spearman 0.7818

Phase 6E held-out hybrid result:

- Pearson 0.3990
- Spearman 0.4390
- normalized RMSE 0.2362

OpenACE has been used repeatedly for development and cannot serve as untouched Phase 6.1 proof. Its published per-file POLQA outputs remain useful for a scoped historical paired benchmark.

Status:

Development evidence.

### TMHINT-QI original

Archive:

`urgent-challenge/urgent26_track2_sqa / TMHINTQI.zip`

Verified release:

`TMHINT_QI_ORIGINAL`

Listener scale:

1 to 5

Paired non-clean rows:

1,455

Unique reference IDs:

192

Provenance:

- archive SHA-256 `cda6581c9fb0ea634b8bac4c6503e772feb080629a5d95eb84f3d1888876912b`
- raw metadata SHA-256 `832ac3fdaf393e77f62edb096770f8ade9f52fbb574e9bebcab0bf9ba02732a5`
- manifest SHA-256 `8af544f59d9f192d51ebc6837e5c50022576e0c5534618e36405ab4334835072`

Phase 6 uses the native 1-to-5 target without the historical erroneous transform.

Status:

Development evidence.

## Phase 6 development total

The canonical Phase 6 development set contains 2,463 rows:

- P501 240
- TEST_FOR 240
- OpenACE 144
- TCD 384
- TMHINT 1,455

Canonical source identity uses SHA-256 of exact reference waveform bytes.

## URGENT 2026 subjective speech-quality data

Subjective source:

https://huggingface.co/datasets/urgent-challenge/urgent2026-sqa

Status:

**Untouched by Phase 6.1 model selection.**

The released enhanced audio is not treated as its own clean reference.

Full-reference use requires a separately verified exact reference map for simulated rows.

The reserve is not opened for a candidate that has failed the independent engineering promotion gate.

## POLQA evidence

POLQA is not a training dependency.

Lawful published or licensed POLQA outputs may be compared only when they correspond to the same audio pairs and human targets.

OpenACE provides a historical public per-file example. A future external comparison must clearly distinguish development benchmarks from untouched validation.
