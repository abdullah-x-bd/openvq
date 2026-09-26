# Reproducibility guide

## Core rule

Every scientific claim should be traceable to:

- source commit;
- model ID where applicable;
- dataset source/revision;
- manifest construction rule;
- feature schema;
- validation protocol;
- GitHub Actions run;
- result artifact;
- hashes for critical generated evidence.

## Historical freezes

### Phase 3

Model ID:

`phase3-tcd-only-2026-09-24-f099129`

Freeze:

`validation/frozen/phase3-freeze.json`

### Phase 4

Frozen candidate:

`phase4-native-poly2-constrained-2026-09-25-v3`

Frozen source:

`d530382d6161d0a5dc3d019782192a047982f839`

The Phase 4 model is retained with its external failures and must not be retuned and described as the same frozen candidate.

## Phase 5.1 canonical record

Source commit:

`4f96463411da8f9f6aecb370e8ac69ae2c228273`

Pull request:

`#12 Phase 5.1: measurement and validation repair`

Workflow:

`.github/workflows/validation-phase51.yml`

Run:

`36219037262`

Conclusion:

`success`

Artifact:

`openvq-phase51`

Artifact ID:

`10899193034`

Artifact SHA-256:

`7e1e244074520e3e9e620fc29a602b99b094c6592a4bb954407b3e98b4949426`

The artifact contains:

- `phase51-report.json`
- constrained model export
- synthetic engineering report
- real-speech engineering report
- TCD/NISQA/OpenACE/TMHINT feature tables
- manifests
- TMHINT provenance
- source/schema/evidence hashes

## Phase 5.1 source hashes

The canonical run records hashes in:

`validation/phase51/provenance.sha256`

Examples:

- feature schema: `9b34a471da6f967fb7807d96e1b8c1311ccd89bb96d7476d7586dfbe02a92c58`
- feature extractor: `9dff62050168ccbe243ab31c2af8e33111812c87a4500327d46ddd928b50e4f6`
- evaluator: `ad95e07527359283b7a72b2a498169c07f6cc1b938c7d333290a39931cbc5d1d`
- TMHINT preparer: `33020cfcfdc703340bc3b5ff9b87cc0381eb41d1df763fdd905645eaa145e37e`
- synthetic engineering generator: `5a36685f6fc2babe5b386f0d3243c9c51dcc0a5c40e93d838521a3ca269014dc`
- real-speech engineering generator: `def06fc822598adc293b189449692e20e952d75a5b53b853755c543b4cd73c8c`

## Phase 5.1 validation workflow

The full workflow does the following in one reproducible run:

1. builds and tests the repaired native analyzer;
2. downloads/prepares TCD;
3. extracts NISQA P501 and TEST_FOR;
4. downloads a pinned OpenACE revision;
5. downloads and identifies TMHINT;
6. extracts repaired legacy and rich features;
7. runs the repaired synthetic engineering matrix;
8. runs the independent real-speech engineering suite;
9. runs fixed-evidence ablations;
10. runs grouped, processing-family, and leave-corpus-out evaluation;
11. records hashes;
12. uploads all evidence;
13. enforces engineering exit gates.

## Feature schemas

Phase 5.1 deliberately keeps both schemas.

### legacy19

Used to isolate frontend repair from representation expansion.

### rich-v2

31 features: legacy19 plus 12 coverage, alignment, level, tail, drift, clipping, and confidence features.

Exact order is recorded in `phase51-report.json` under `selected_export.features`.

## Export status

The constrained rich-v2 model export contains:

- exact feature order;
- basis order;
- normalization mean;
- normalization scale;
- coefficients;
- solver iterations;
- generated C++ include;
- reference Python predictor.

The export is reproducible research evidence.

It is not promoted into the main native CLI/Android MOS path because leave-corpus-out generalization is insufficient.

## Main validation workflows

### Phase 5.1 full repair

`.github/workflows/validation-phase51.yml`

### Phase 5.1 fast evaluator check

`.github/workflows/validation-phase51-fastcheck.yml`

### Engineering matrix

`.github/workflows/validation-engineering.yml`

### Phase 3/ViSQOL historical reproduction

`.github/workflows/validation-visqol-baseline.yml`

### OpenACE historical benchmark

`.github/workflows/validation-openace-polqa.yml`

### Phase 4 forensics

`.github/workflows/validation-phase4-forensic.yml`

## Direct POLQA comparison

Protocol:

`validation/LOCKED_POLQA_PROTOCOL.md`

Primary statistic:

RMSE to human MOS.

Predeclared Project OpenVQ non-inferiority margin:

+0.10 MOS RMSE.

A formal direct comparison requires lawful POLQA outputs for the exact same reference/degraded pairs.

## Rules for future Phase 6 work

A new model ID is required if any of these change:

- input feature definition;
- learned representation;
- coefficients;
- architecture;
- normalization;
- calibration mapping;
- output clipping;
- expert-gating rule.

Development evaluation may use the five Phase 5.1 corpora.

A new final holdout must not influence:

- architecture selection;
- hyperparameter selection;
- preprocessing changes;
- threshold changes;
- calibration;
- stopping decisions.

URGENT 2026 remains untouched at the end of Phase 5.1.

## Reporting rule

Always report:

- sample count;
- Pearson;
- Spearman;
- absolute error on a meaningful common scale or clearly labelled normalized error;
- bias where appropriate;
- floor/ceiling saturation;
- processing-family results;
- leave-corpus-out results;
- engineering failures;
- known evidence defects or errata.

Do not report only the strongest metric.
