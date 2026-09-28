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

Canonical run:

`36319146056`

### D1 padding-context diagnostic

The original temporal models were not exactly invariant to zero-padding introduced by longer utterances in the same batch.

Maximum absolute MOS differences:

| Model | max absolute MOS delta | violations above 0.0001 MOS |
| --- | ---: | ---: |
| native temporal | 0.001072 | 22 |
| learned bands | 0.000320 | 10 |
| hybrid | 0.000221 | 3 |

The effect is too small to explain the cross-domain failures, but it is a real inference-contract defect.

Diagnostics artifact:

- ID `10932370265`
- SHA-256 `b2b154f0f9837a8b9f1bdb48b7eb8a65dddc9a5cf48f089af8b824615a2f1f4a`

### D2 fold-fitted hybrid global normalization

The rich-v3 global feature standard deviations span approximately 95.6 million to 1.

Hybrid was rerun with z-score normalization fitted only on the allowed training rows for each fold.

| Held corpus | Pearson | Spearman | normalized RMSE |
| --- | ---: | ---: | ---: |
| P501 | 0.7623 | 0.7538 | 0.1680 |
| TEST_FOR | 0.6063 | 0.5493 | 0.1953 |
| OpenACE | -0.4985 | -0.4066 | 0.3319 |
| TCD | 0.5459 | 0.6503 | 0.2405 |
| TMHINT | 0.1525 | 0.2256 | 0.2624 |

Objective:

- worst held-corpus correlation -0.4985;
- mean held-corpus correlation 0.3006;
- worst normalized RMSE 0.3319.

Normalization materially rescues hybrid from the raw-fusion collapse, but it still performs substantially worse than corrected `learned_bands` because OpenACE remains strongly negative.

Normalized-hybrid artifact:

- ID `10932529605`
- SHA-256 `d0667c42cfbccaca345feedcb8890d11e08f1177e4a5c844c3ceca33257c2fb4`

### 6.2D conclusion

The global scale mismatch was real but does not explain the whole hybrid failure.

The batch-context defect is real but numerically small.

Corrected `learned_bands` remains the preferred representation for the next controlled stage.

## 6.2E padding-safe learned-bands ablation

Phase 6.2E changes only the temporal padding/normalization contract of the current winning `learned_bands` architecture.

The encoder masks padded frames after every convolution. The TCN masks padded frames after every stage and replaces BatchNorm1d with per-frame channel LayerNorm.

Before training, the new model must pass the same-utterance-alone versus mixed-length-batch invariance gate at 0.0001 MOS.

The same five held corpora and three fixed seeds are then rerun. No property losses, new data, global fusion, or external reserve are introduced.


## 6.2E completed result

Canonical run:

`36330893596`

Aggregate artifact:

- name `openvq-phase62e-padding-safe`
- artifact ID `10937636963`
- artifact ZIP SHA-256 `7d222696a891cfbb4d8ae6dda8131c259d41840a187d0319ad886d96ec43ce0b`

### Padding invariance

The padding-safe architecture passed the pre-training same-utterance batch-context gate.

- model seeds tested: 17, 23, 37
- samples per seed: 15
- tolerance: 0.0001 MOS
- maximum absolute MOS delta: 0.0000004768
- violations: 0
- result: pass

### Three-seed held-corpus ensembles

| Held corpus | Pearson | Spearman | normalized RMSE |
| --- | ---: | ---: | ---: |
| NISQA P501 | 0.6364 | 0.6456 | 0.2066 |
| NISQA TEST_FOR | 0.5241 | 0.4609 | 0.2019 |
| OpenACE | 0.4403 | 0.4897 | 0.2116 |
| TCD | 0.5521 | 0.5477 | 0.2570 |
| TMHINT | 0.2248 | 0.1900 | 0.3062 |

Aggregate selection objective:

- worst held-corpus correlation 0.1899702;
- mean held-corpus correlation 0.4550501;
- worst normalized RMSE 0.3062099.

Relative to the corrected Trace V2 learned-bands baseline, Phase 6.2E sacrifices some P501 and TEST_FOR correlation but substantially improves OpenACE, modestly improves TCD, removes the padding-context defect, improves the worst held-corpus correlation from 0.0894 to 0.1900, improves mean held-corpus correlation from 0.4317 to 0.4551, and reduces worst normalized RMSE from 0.3487 to 0.3062.

Every completely held-out development corpus now has positive ensemble Pearson and Spearman correlation.

This remains development evidence. URGENT 2026 remains untouched.

## 6.2F aligned engineering qualification

Canonical run:

`36397704754`

The Phase 6.2F candidate aligned qualification with the Phase 6.2E evaluation shape:

- three full-development fits using seeds `20260926`, `20260927`, and `20260928`;
- one ONNX export per seed;
- arithmetic mean of raw quality predictions;
- independent engineering scoring on the ensemble;
- no URGENT label consumption.

All three training jobs completed and all three ONNX exports passed PyTorch-to-ONNX parity at the 0.0001 MOS tolerance.

### Engineering result

| Gate | Result |
| --- | --- |
| identity | 4.4483 MOS, pass |
| pure delay | maximum absolute change 0.0389 MOS, pass |
| dropout severity | pass |
| repeated-dropout severity | pass |
| noise severity | pass under frozen 0.12 MOS reversal criterion |
| low-pass severity | pass |
| mixed impairment severity | pass |
| clipping severity | **fail, one reversal** |

The protected clipping sequence was:

| Threshold | MOS |
| --- | ---: |
| 0.95 | 4.3376 |
| 0.50 | 2.1387 |
| 0.25 | 2.0875 |
| 0.08 | 2.4201 |

The final severe clipping condition incorrectly rose by about 0.333 MOS.

Because the protected gate failed:

- the qualified bundle step was skipped;
- the candidate was not promoted;
- URGENT remained untouched.

Qualification artifact:

- name `openvq-phase62f-engineering-qualification`;
- artifact ID `10961376404`;
- artifact ZIP SHA-256 `2b0c1aeaf1aaa20b5650115a0c4089276ca1a4dc10a4df5ed235c369f2cec852`.

## 6.2G clipping-order property constraint

Phase 6.2G targeted the single remaining Phase 6.2F failure without changing the frontend, trace, architecture, held-corpus protocol, seed set, ensemble rule, or protected engineering gate.

### Property fixtures

Training used three separately generated speech-like references and six clipping thresholds:

`0.85, 0.65, 0.45, 0.30, 0.18, 0.11`

Protected gate thresholds remained:

`0.95, 0.50, 0.25, 0.08`

The threshold sets are disjoint.

The property fixtures contain 18 Trace V2 rows and have no subjective-MOS role.

Training added:

- adjacent clipping-order hinge loss;
- raw-quality margin 0.03, equal to 0.12 MOS;
- property-loss weight 0.25;
- one property contribution every four human training batches.

Early stopping remained human-only corpus-balanced validation RMSE.

Constraint artifact:

- name `openvq-phase62g-clipping-constraints`;
- artifact ID `10969564021`.

### Predeclared subjective guardrails

Phase 6.2G had to preserve:

- positive Pearson and Spearman on all five held corpora;
- at least 90% of the Phase 6.2E worst held-corpus correlation;
- at least 95% of the Phase 6.2E mean held-corpus correlation;
- worst normalized RMSE within 105% of Phase 6.2E.

Guardrail thresholds were:

- worst correlation at least 0.17097;
- mean correlation at least 0.43230;
- worst normalized RMSE at most 0.32152.

All guardrails passed.

### Phase 6.2G held-corpus ensembles

| Held corpus | Pearson | Spearman | normalized RMSE | MAE | bias |
| --- | ---: | ---: | ---: | ---: | ---: |
| NISQA P501 | 0.6551 | 0.6384 | 0.1943 | 0.1546 | -0.0281 |
| NISQA TEST_FOR | 0.5640 | 0.4656 | 0.1850 | 0.1535 | 0.0042 |
| OpenACE | 0.4213 | 0.4659 | 0.2135 | 0.1877 | -0.0046 |
| TCD | 0.5901 | 0.6129 | 0.2818 | 0.2435 | -0.1977 |
| TMHINT | 0.3541 | 0.3281 | 0.2919 | 0.2421 | -0.2112 |

Aggregate objective:

- worst held-corpus correlation 0.3280675;
- mean held-corpus correlation 0.4887042;
- worst normalized RMSE 0.2918971.

Compared with Phase 6.2E:

| Objective | Phase 6.2E | Phase 6.2G |
| --- | ---: | ---: |
| worst held-corpus correlation | 0.1900 | **0.3281** |
| mean held-corpus correlation | 0.4551 | **0.4887** |
| worst normalized RMSE | 0.3062 | **0.2919** |

The clipping-order constraint therefore did not merely repair the engineering defect. Under the frozen aggregate criteria, cross-domain robustness improved as well.

Held-corpus artifact:

- name `openvq-phase62g-held-corpus`;
- artifact ID `10975650939`.

URGENT remained untouched.

## 6.2G final engineering qualification

The final three full-development seeds completed successfully.

The unchanged protected gate passed with **zero failures**.

Identity:

- observed MOS 4.6062;
- requirement at least 4.4;
- result pass.

Pure delay:

- maximum absolute MOS change 0.00924;
- requirement at most 0.20;
- result pass.

Protected monotonic families:

| Family | >0.12 MOS reversals |
| --- | ---: |
| clipping | 0 |
| dropout | 0 |
| repeated dropout | 0 |
| noise | 0 |
| low-pass | 0 |
| mixed impairment | 0 |

The corrected protected clipping sequence was:

| Threshold | MOS |
| --- | ---: |
| 0.95 | 4.4760 |
| 0.50 | 2.0543 |
| 0.25 | 1.7905 |
| 0.08 | 1.5014 |

Noise also became cleanly ordered across the protected subset:

| SNR | MOS |
| --- | ---: |
| 40 dB | 1.7601 |
| 20 dB | 1.4642 |
| 10 dB | 1.3755 |
| 0 dB | 1.3403 |

### ONNX parity

All three final models passed the 0.0001 MOS tolerance.

- seed 20260926 maximum absolute MOS difference 0.00000119;
- seed 20260927 maximum absolute MOS difference 0.00000095;
- seed 20260928 maximum absolute MOS difference 0.00000167.

### Immutable qualified development bundle

The bundle step executed successfully.

- source commit `9c59fec790e0490c22b363474dd75b476f891f8f`;
- model mode `learned_bands_padding_safe_clipreg`;
- seeds `20260926`, `20260927`, `20260928`;
- pipeline ID `openvq-phase62g-749eaa80ea0a796cc15c`;
- qualification artifact `openvq-phase62g-qualification`;
- artifact ID `10980470659`;
- artifact ZIP SHA-256 `407b04a1130b559ef59d54c63f3d40c02d24fb08c106ef80dc7fdf8f654d645c`.

ONNX SHA-256:

- seed 20260926 `7bb40fc128ecc902271be93076a3af21b35f1f142ddcf3cb9b6798d90b1f0821`;
- seed 20260927 `64cb9ba8e769b8c8e2801e4c1fe3b143ddf2ca0b033ce68885430ce85a32981d`;
- seed 20260928 `8ed003ef19bd6b640951f0b1ee6b02c47b5a4573f17eba7e8d477e06685b514b`.

## Phase 6.2 result

Phase 6.2G is the first learned OpenVQ candidate in this research line that simultaneously:

- uses corrected Trace V2;
- maintains positive ensemble Pearson and Spearman across all five completely held-out development corpora;
- passes the predeclared subjective no-regression guardrails;
- passes deployment parity;
- passes the unchanged protected engineering gate;
- has an immutable qualified development bundle.

The result remains development evidence.

It does **not** establish external validity, POLQA equivalence, P.863 conformance, or general superiority to POLQA.

URGENT 2026 subjective labels remain untouched.

The next step is external validation of the exact frozen Phase 6.2G bundle under the reserved protocol.
