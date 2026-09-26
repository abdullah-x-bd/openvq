# OpenVQ documentation

Start here if you are new to the project.

## Recommended reading order

1. [Project README](../README.md)
   The shortest current status, build instructions, and claim boundary.

2. [Architecture](ARCHITECTURE.md)
   Explains the native OpenVQ measurement engine and how the Phase 5.1 repaired frontend differs from the older path.

3. [Validation history](VALIDATION_HISTORY.md)
   Chronological record from Phase 1 through Phase 5.1, including failures.

4. [Phase 5.1 final results](PHASE5_1_RESULTS.md)
   The canonical account of what the audit repaired, what improved, what still failed, and why Phase 6 is next.

5. [Datasets](DATASETS.md)
   Ledger of every subjective corpus and whether it is development evidence or still untouched.

6. [Reproducibility](REPRODUCIBILITY.md)
   Commits, workflows, artifacts, hashes, and reproduction rules.

7. [Product integration](PRODUCT_INTEGRATION.md)
   What can currently be integrated and what claims must not be made.

Historical design documents:

- [Phase 4 robust fusion](PHASE4_ROBUST_FUSION.md)
- [Phase 5 cross-domain redesign](PHASE5_CROSS_DOMAIN.md)
- [Phase 5.1 plan](PHASE5_1.md)
- [Phase 5.1 evidence erratum](PHASE5_1_EVIDENCE_ERRATUM.md)

## Current status

OpenVQ has a mature native full-reference measurement engine, but it is not demonstrated to be equivalent or superior to POLQA.

Phase 3 performed strongly on TCD and NISQA P501 but failed OpenACE because its fixed expert fusion did not generalize.

Phase 4 moved to a native-first constrained model and passed engineering tests, but failed untouched NISQA TEST_FOR correlation thresholds and failed badly on TMHINT correlation. Phase 5 then retrained the native mapper across five known domains, but still left TMHINT as the weakest domain.

Phase 5.1 repaired the evidence chain, shared preprocessing, alignment, active-speech coverage, feature representation, and validation methodology. Rich-v2 improved the constrained five-domain development objective, and a small MLP diagnostic improved it further. However, leave-one-corpus-out evaluation still failed severely on unseen OpenACE and TMHINT.

The project is therefore ready to investigate Phase 6 as a learned generalization problem, not ready to claim POLQA parity.

URGENT 2026 remains untouched for a future frozen candidate.
