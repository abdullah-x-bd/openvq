# OpenVQ documentation

Start here if you are new to the project.

## Recommended reading order

1. [Architecture](ARCHITECTURE.md)
   Explains the native OpenVQ engine, the optional ViSQOL experts, and the relationship to POLQA.

2. [Validation history](VALIDATION_HISTORY.md)
   Records the development and validation sequence, including successful and failed experiments.

3. [Datasets](DATASETS.md)
   Explains which datasets were used for development, which were held out, and which may still be used as untouched validation.

4. [Phase 4 robust fusion](PHASE4_ROBUST_FUSION.md)
   Explains why Phase 4 exists and the rules for the redesign.

5. [Reproducibility](REPRODUCIBILITY.md)
   Explains model freezes, workflows, artifacts, and how to reproduce the experiments.

6. [Product integration](PRODUCT_INTEGRATION.md)
   Explains what can and cannot currently be claimed when OpenVQ is integrated into a drive-test application.

## Current one-paragraph status

OpenVQ is an independently derived full-reference speech-quality engine. The native C++ analyzer computes its own alignment, perceptual, temporal, and telecom diagnostics. Phase 3 added separately computed Google ViSQOL speech and audio scores as learned expert inputs. Frozen Phase 3 performed strongly on TCD and NISQA P501 but failed on the independent EARS-EMO-OpenACE codec benchmark because the fusion placed too much trust in a speech-mode expert that did not generalize to that domain. Phase 4 is redesigning the fusion around native-first and reliability-gated principles. No POLQA-parity claim is currently made.
