# Phase 5.1 measurement and validation repair

Phase 5.1 is a repair release, not a claim of POLQA parity.

Phase 5 v1 is preserved as a diagnostic baseline. Phase 5.1 exists because an
independent audit identified evidence and measurement-chain defects that must be
resolved before any neural Phase 6 work can be interpreted cleanly.

## 5.1A Evidence correction

Implemented:

- restored independent pure-delay engineering assertion
- TMHINT release detection from archive processing families
- corrected original TMHINT 1-to-5 rating handling
- archive, raw-metadata and manifest SHA-256 provenance
- historical erratum without rewriting earlier artifacts

Exit:

- corrected manifest is traceable and deterministic
- independent delay assertion executes in the validation source and run

## 5.1B Shared preprocessing

Implemented:

- one windowed-sinc resampler
- one DC-removal path
- one prepared reference/degraded pair shared by base and advanced analysis

Exit:

- native contract tests pass
- base and advanced analysis consume the same prepared buffers

## 5.1C Shared alignment, coverage and active level

Implemented:

- piecewise continuous alignment map with bounded local path movement
- global delay and clock-drift metadata
- common alignment map for multi-resolution, envelope and residual features
- explicit active-reference coverage and lost-active-speech fraction
- matched active-speech level measurement
- out-of-range active speech is counted as missing rather than silently skipped

The local path deliberately refuses large jumps through low-correlation
regions. Alignment is a correction for nuisance timing, not permission to hide
a missing word.

Exit:

- known-delay C++ test passes
- pure delay remains stable in synthetic and real-speech suites
- truncation creates explicit lost-active-speech evidence

## 5.1D Rich representation

Two schemas are retained side by side.

### legacy19

The exact 19 utterance summaries used by Phase 5.

### rich-v2

legacy19 plus:

- lost active speech
- active coverage
- alignment uncertainty
- raw matched active-level delta
- 10th and 50th percentile similarity loss
- 90th percentile discontinuity
- longest bad interval
- severe-frame fraction
- absolute clock drift
- raw clipping ratio
- confidence deficit

No historical artifact is silently reinterpreted as rich-v2.

## 5.1E Evaluation repair

Implemented evaluation axes:

- grouped within-corpus transfer
- nested leave-corpus-out transfer
- processing-family transfer
- independent real-speech engineering suite
- explicit normalized-error reporting across mixed MOS/MUSHRA protocols

The leave-corpus-out corpus is excluded from inner model selection.

URGENT 2026 is not consumed by Phase 5.1.

## 5.1F Fixed-evidence ablations and export equivalence

Ablations on identical evidence:

1. repaired frontend + legacy19 + constrained linear/quadratic model
2. repaired frontend + rich-v2 + constrained linear/quadratic model
3. repaired frontend + rich-v2 + small MLP diagnostic

The MLP is diagnostic only and is not eligible to silently become the exported
product scorer.

The selected constrained rich-v2 model report contains exact feature order,
basis order, normalization statistics and coefficients. A standalone Python
predictor is generated from that same report for later C++ and Android
equivalence checks.

Phase 5.1 is not complete until:

- corrected evidence is recorded
- synthetic and real-speech engineering suites pass
- cross-domain and processing-transfer reports are produced
- the selected model is embedded in native inference
- Python and native CLI predictions match within a predeclared numerical
  tolerance
- Android builds the exact same preprocessing and model sources
- model/preprocessor hashes are recorded

Only after those exits are satisfied should Phase 6 begin.
