# Dataset ledger

This ledger tracks how each subjective dataset is used. The status matters because a dataset stops being an untouched holdout once its labels influence model design.

## TCD-VoIP

Source:
https://www.isca-archive.org/interspeech_2015/hines15_interspeech.html

Purpose:
Common VoIP degradations with subjective quality judgments.

Use in OpenVQ:
- early validation
- Phase 2 development
- Phase 3 train/development split
- frozen Phase 3 held-out test split

Current status:
Development data for Phase 4. It can no longer provide untouched validation for a new Phase 4 candidate.

## NISQA Speech Quality Corpus

Source:
https://zenodo.org/records/4728081

Project documentation:
https://github.com/gabrielmittag/NISQA/wiki/NISQA-Corpus

Purpose:
Large subjective speech-quality corpus spanning simulated and live conditions.

OpenVQ used the NISQA TEST P501 subset because reference/degraded pairing could be reconstructed for full-reference evaluation.

Use in OpenVQ:
- Phase 3 external holdout

Frozen Phase 3 result on TEST P501:
- n = 240
- Pearson = 0.8185
- Spearman = 0.8209
- RMSE = 0.6011 MOS

Current status:
Because the Phase 3 result has been inspected and is now informing Phase 4 design, it is development evidence for Phase 4 rather than an untouched Phase 4 holdout.

## EARS-EMO-OpenACE

Source:
https://huggingface.co/datasets/mcernak/EARS-EMO-OpenACE

Purpose:
Codec quality under emotional speech, with human MUSHRA ratings plus published objective metric outputs.

Evaluated codecs:
- EVS
- LC3
- LC3Plus
- Opus

Use in OpenVQ:
- independent external test of the frozen Phase 3 candidate

Frozen Phase 3 result:
- OpenVQ Pearson = 0.1607
- OpenVQ Spearman = 0.1465
- published POLQA Pearson = 0.7939
- published POLQA Spearman = 0.7818
- published OpenACE ViSQOL Pearson = 0.7034

Interpretation:
A clear Phase 3 generalization failure.

Current status:
Development and forensic evidence for Phase 4. It must not be presented as untouched Phase 4 validation after its labels have influenced the redesign.

## URGENT 2026 subjective speech-quality data

Subjective dataset:
https://huggingface.co/datasets/urgent-challenge/urgent2026-sqa

Challenge:
https://urgent-challenge.github.io/urgent2026/track1/

The released subjective dataset contains 5,040 ACR samples across 840 utterances, nine languages, and six enhancement systems, with individual listener ratings and MOS.

The challenge test material includes simulated and real-world speech. The simulated portion is particularly interesting for OpenVQ because reference-capable material exists in the challenge data path, while real-world samples may not have a strictly matched reference.

Current status:
Candidate future external validation source.

Important:
Do not use the selected final URGENT subset or its MOS labels for Phase 4 fitting if it is chosen as the final untouched holdout. The exact subset and pairing procedure must be frozen before scoring.

## POLQA data

POLQA is not a training dependency of OpenVQ.

When lawful POLQA scores exist for the exact same audio pairs, they may be used as a benchmark against the same subjective human target.

The repository's locked direct-comparison protocol is in:
`validation/LOCKED_POLQA_PROTOCOL.md`
