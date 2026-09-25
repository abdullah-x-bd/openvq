# Reproducing the validation

## Principle

Every important validation stage is implemented as code and GitHub Actions.
The repository records model IDs, dataset roles, source commits, workflow
artifacts and negative results.

A dataset that has been inspected for model development is never described as
an untouched holdout for a later model.

## Phase 3

Frozen model:

`phase3-tcd-only-2026-09-24-f099129`

Frozen record:

`validation/frozen/phase3-freeze.json`

Successful Phase-3 hybrid workflow run:

`36089410545`

Artifact:

`openvq-phase3-hybrid`

Artifact ID:

`10847922836`

The artifact contains the frozen mapper, TCD test predictions, NISQA P501
predictions and ViSQOL expert scores.

## OpenACE Phase-3 external test

Protocol:

`validation/OPENACE_PROTOCOL.md`

Successful workflow run:

`36099432761`

Artifact:

`openvq-openace-polqa`

Artifact ID:

`10849675346`

Artifact SHA-256:

`9fb94ead53b1348569bc3c2fd70c265e20e4e37e214392595dc886b82040e8dc`

Pinned EARS-EMO-OpenACE dataset revision:

`31acd607eb4fb1d136677fab2aa6ced0af0e1194`

The workflow recomputes Google ViSQOL v3.3.3 speech and audio experts, scores
the frozen Phase-3 OpenVQ candidate and compares it with published per-file
POLQA and human MUSHRA.

## Phase 4 v1

Workflow run:

`36104456276`

Artifact:

`openvq-phase4-development`

Artifact ID:

`10850816520`

Artifact SHA-256:

`714d576f1bc1a092dc5b39c85865086f4a42f7171b99aef550fcf3be4a001ede`

Phase 4 v1 failed its purpose and is retained only as development history.

## Phase 4 v2

The v2 development workflow:

`.github/workflows/validation-phase4-v2-development.yml`

The fitter:

`validation/phase4_v2_fit.py`

The application code:

`validation/phase4_v2_apply.py`

The exact data policy and development gate are in:

`validation/PHASE4_PROTOCOL.md`

When the development gate passes, the resulting JSON model is copied into
`validation/frozen/` with its source commit and artifact digest before any
fresh holdout is evaluated.

## Final holdouts

The current reserved Phase-4 holdouts are NISQA TEST FOR and NISQA TEST NSC.

Each has 240 degraded files across 60 conditions and human subjective scores.
The holdout workflow must prepare the reference/degraded pairs, recompute the
same pinned ViSQOL v3.3.3 expert modes, extract OpenVQ native features and apply
the already-frozen Phase-4 model.

No fitting occurs inside the holdout workflow.

## Direct POLQA comparison

OpenACE includes published POLQA values and therefore supports a direct
development comparison.

For a future formal POLQA non-inferiority claim, OpenVQ and a lawful licensed
POLQA implementation must score the same locked reference/degraded pairs, with
the statistical criterion declared before the POLQA outputs are inspected.

OpenVQ is not a P.863 implementation.
