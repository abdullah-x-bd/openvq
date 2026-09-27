# Phase 6.2 results

## 6.2A-B corrected trace

Trace V2 corrected the trace-only FFT butterfly defect and added direct numerical correctness gates.

Trace schema:

`openvq-trace-v2-2026-09-27`

Implementation ID:

`openvq-trace-spectral-v2-fft-corrected-2026-09-27`

Canonical run:

`36306154897`

Source commit:

`bc2637808f1299570eb74e4b2282da1532fc53f2`

Trace artifact:

- name `openvq-phase62-trace-v2`
- artifact ID `10928082645`
- SHA-256 `1cfb4066a2461c08166cf10555ce287aa63310d68a1186a7573a39b4b0b0aff6`

The trace stage passed:

- frozen Phase 6A source verification;
- FFT-versus-direct-DFT tests;
- impulse and constant fixtures;
- Parseval energy conservation;
- frequency-to-band fixtures;
- amplitude-energy fixture;
- exact recreation of all five development corpora;
- waveform verification against canonical Phase 6B evidence;
- export of all 2,463 development traces;
- export of engineering traces.

## 6.2C unchanged corrected-trace baseline

The original Phase 6E experiment was rerun unchanged except for Trace V2.

The rerun used:

- the same 2,463 development pairs;
- the same source groups;
- the same three architectures;
- the same five held corpora;
- the same three seeds;
- the same optimizer and loss;
- the same early-stopping method;
- the same 80-epoch ceiling;
- the same three-seed ensemble aggregation;
- the same architecture selection rule.

All 45 seeded fits completed successfully.

### Final ensemble results

| Model | Held corpus | Pearson | Spearman | normalized RMSE |
| --- | --- | ---: | ---: | ---: |
| native temporal | P501 | 0.6823 | 0.6946 | 0.2222 |
| native temporal | TEST_FOR | 0.0779 | 0.0342 | 0.3580 |
| native temporal | OpenACE | -0.2449 | -0.2182 | 0.3456 |
| native temporal | TCD | 0.3811 | 0.4329 | 0.2897 |
| native temporal | TMHINT | 0.2763 | 0.2800 | 0.2371 |
| learned bands | P501 | **0.7792** | **0.7563** | **0.1610** |
| learned bands | TEST_FOR | **0.6153** | **0.5611** | **0.2336** |
| learned bands | OpenACE | **0.1132** | **0.0894** | **0.2479** |
| learned bands | TCD | **0.5114** | **0.5246** | **0.2533** |
| learned bands | TMHINT | **0.2430** | **0.2404** | **0.3487** |
| hybrid | P501 | -0.0522 | -0.0817 | 0.5854 |
| hybrid | TEST_FOR | -0.0559 | -0.1287 | 0.4229 |
| hybrid | OpenACE | -0.8059 | -0.7268 | 0.4761 |
| hybrid | TCD | -0.0686 | -0.0915 | 0.3110 |
| hybrid | TMHINT | -0.1677 | -0.1921 | 0.5263 |

### Frozen architecture objective

| Model | worst held-corpus correlation | mean held-corpus correlation | worst normalized RMSE |
| --- | ---: | ---: | ---: |
| native temporal | -0.2449 | 0.2258 | 0.3580 |
| learned bands | **0.0894** | **0.4317** | **0.3487** |
| hybrid | -0.8059 | -0.2600 | 0.5854 |

The unchanged selection rule now selects **learned_bands**.

### Interpretation

Trace V2 materially changes the sequence-model evidence.

The learned spectral representation improves strongly on P501, TEST_FOR, OpenACE, and TCD relative to Trace V1. The winning corrected-trace architecture has no negative held-corpus ensemble correlation.

The corrected hybrid model collapses across all five held corpora. This makes raw global-feature fusion and the hybrid training contract a separate diagnosis target rather than evidence against the local sequence representation.

Canonical corrected-baseline artifact:

- name `openvq-phase62-corrected-trace-baseline`
- artifact ID `10931420305`
- SHA-256 `161e19fb8964177bdc00879ea8fc4606bfac0eb163a8dda669d4d1e07c30deea`

URGENT 2026 remains untouched.

## 6.2D training-contract diagnostics

The next controlled stage tests two issues independently:

1. padding/batch-context invariance of the temporal network;
2. fold-fitted z-score normalization of the rich-v3 global vector in hybrid.

No property losses, new datasets, architecture scaling, or external reserve are introduced in this stage.
