# OpenVQ documentation

## Current milestone

OpenVQ is at **Phase 6.1**.

Phase 6A through 6E are complete as research and validation milestones. Phase 6F produced an exportable hybrid development candidate and passed ONNX parity, but the candidate failed the independent engineering gate and was not promoted.

URGENT 2026 remains reserved and unconsumed.

## Recommended reading order

1. [Project README](../README.md)
2. [Phase 6.1 results](PHASE6_1_RESULTS.md)
3. [Architecture](ARCHITECTURE.md)
4. [Algorithm](ALGORITHM.md)
5. [Validation framework](VALIDATION.md)
6. [Validation history](VALIDATION_HISTORY.md)
7. [Datasets](DATASETS.md)
8. [Reproducibility](REPRODUCIBILITY.md)
9. [Product integration](PRODUCT_INTEGRATION.md)
10. [Phase 6 trace schema](PHASE6_TRACE_SCHEMA.md)
11. [Phase 6 sequence model](PHASE6_SEQUENCE_MODEL.md)

Historical design and evidence documents remain available without rewriting their original phase context:

- [Phase 4 robust fusion](PHASE4_ROBUST_FUSION.md)
- [Phase 5 cross-domain redesign](PHASE5_CROSS_DOMAIN.md)
- [Phase 5.1 plan](PHASE5_1.md)
- [Phase 5.1 evidence erratum](PHASE5_1_EVIDENCE_ERRATUM.md)
- [Phase 5.1 final results](PHASE5_1_RESULTS.md)

## Current scientific position

The native frontend is substantially better specified and tested than the early OpenVQ system. Local sequence evidence also contains cross-domain information that pooled summary features discarded.

The current limitation is the quality-learning procedure. The selected hybrid sequence candidate improved held-out OpenACE but remained unstable across corpora and learned physically wrong quality relationships on an independent engineering suite.

The next iteration keeps the Phase 6A frontend and Phase 6D trace contracts fixed while repairing training, calibration, and explicit engineering constraints.
