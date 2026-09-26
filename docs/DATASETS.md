# Dataset ledger

This ledger records how each subjective dataset has been used and whether it can still serve as untouched evidence.

A dataset stops being an untouched holdout once its labels or results influence model design.

## TCD-VoIP

Purpose:

Common VoIP degradation families with subjective quality judgments.

Use:

- Phase 2 development;
- Phase 3 train/development and frozen held-out test;
- Phase 4 development;
- Phase 5 cross-domain development;
- Phase 5.1 repaired feature extraction, real-speech engineering references, grouped transfer, and leave-corpus-out analysis.

Phase 5.1 rows:

384

Current status:

Development evidence. Not an untouched future holdout.

## NISQA TEST P501

Source:

https://zenodo.org/records/4728081

Purpose:

Reference-capable subjective speech-quality test conditions.

Historical frozen Phase 3 result, n = 240:

- Pearson 0.8185
- Spearman 0.8209
- RMSE 0.6011 MOS

Use:

- Phase 3 external holdout;
- Phase 4 development after unblinding;
- Phase 5 development;
- Phase 5.1 repaired development and leave-corpus-out analysis.

Current status:

Development evidence.

## NISQA TEST_FOR

Purpose:

A second reference-capable NISQA foreign test subset.

Phase 4 untouched result, n = 240:

- Pearson 0.6148
- Spearman 0.5892
- RMSE 0.7503 MOS

It failed the predeclared Phase 4 Pearson/Spearman gate.

Use after Phase 4:

- Phase 5 development;
- Phase 5.1 development and leave-corpus-out analysis.

Current status:

Development evidence.

## NISQA TEST_NSC

The NISQA documentation identifies a 240-file TEST_NSC set, but the public archive endpoints used by the validation workflows did not expose the expected TEST_NSC directory through their ZIP listings.

No OpenVQ TEST_NSC score was produced during Phase 4.

Current status:

Not consumed, but unavailable through the workflow path used so far. Do not imply that it was tested.

## EARS-EMO-OpenACE

Source:

https://huggingface.co/datasets/mcernak/EARS-EMO-OpenACE

Purpose:

Codec quality under emotional speech with human MUSHRA ratings and published objective-metric outputs.

Codecs:

- EVS
- LC3
- LC3Plus
- Opus

Phase 3 external result:

- OpenVQ Pearson 0.1607
- OpenVQ Spearman 0.1465
- published POLQA Pearson 0.7939
- published POLQA Spearman 0.7818

Use after Phase 3:

- Phase 4 forensics/development;
- Phase 5 development;
- Phase 5.1 repaired development, processing-family transfer, and leave-corpus-out analysis.

Phase 5.1 leave-corpus-out rich model:

- Pearson -0.4904
- Spearman -0.4114

Current status:

Development evidence.

## TMHINT-QI

Archive source used by Phase 5.1:

`urgent-challenge/urgent26_track2_sqa / TMHINTQI.zip`

### Important Phase 5.1 correction

The archive was historically labelled in OpenVQ as `TMHINT_QI_V2_TEST`.

Phase 5.1 inspected the processing families and metadata and detected:

- release: `TMHINT_QI_ORIGINAL`
- observed listener score scale: 1 to 5
- observed score minimum: 1.0
- observed score maximum: 5.0

The earlier workflow transformed ratings with `1 + 0.8 * score`. That transform was unnecessary.

Final Phase 5.1 pairing:

- test WAVs: 2,297
- paired non-clean samples: 1,455
- unresolved non-clean samples: 331
- unique reference IDs: 192

Provenance:

- archive SHA-256 `cda6581c9fb0ea634b8bac4c6503e772feb080629a5d95eb84f3d1888876912b`
- raw metadata SHA-256 `832ac3fdaf393e77f62edb096770f8ade9f52fbb574e9bebcab0bf9ba02732a5`
- manifest SHA-256 `8af544f59d9f192d51ebc6837e5c50022576e0c5534618e36405ab4334835072`

Historical interpretation:

- historical Pearson/Spearman remain useful correlation diagnostics because the incorrect transform was positive affine;
- historical RMSE/MAE/bias based on the transformed target are not corrected absolute-error evidence;
- Phase 5 v1 used transformed TMHINT targets during fitting and is retained only as a diagnostic baseline.

Phase 5.1 leave-corpus-out rich model:

- Pearson -0.0269
- Spearman 0.0590
- normalized RMSE 0.5047
- floor fraction 0.7739

Current status:

Development evidence.

## URGENT 2026 subjective speech-quality data

Subjective dataset:

https://huggingface.co/datasets/urgent-challenge/urgent2026-sqa

Challenge:

https://urgent-challenge.github.io/urgent2026/track1/

The release contains multilingual subjective quality data and includes simulated and real-world enhancement material.

Current OpenVQ status:

**Untouched by Phase 5.1.**

Phase 5.1 explicitly did not consume URGENT 2026 subjective labels.

Intended use:

Candidate final external validation source for a future frozen Phase 6 model.

Rule:

Do not use the selected final URGENT subset, labels, system identities, or performance feedback for Phase 6 model fitting or selection once the final holdout protocol is frozen.

## POLQA data

POLQA is not an OpenVQ training dependency.

Lawfully obtained POLQA outputs may be used as a benchmark only when they correspond to exactly the same reference/degraded pairs and the same human subjective target.

The locked direct-comparison protocol is:

`validation/LOCKED_POLQA_PROTOCOL.md`
