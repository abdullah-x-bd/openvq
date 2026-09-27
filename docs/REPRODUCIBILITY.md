# Reproducibility guide

## Core rule

Every scientific claim is tied to source, data identity, protocol, workflow run, artifact, and critical hashes.

## Historical freezes

Phase 3:

`phase3-tcd-only-2026-09-24-f099129`

Phase 4:

`phase4-native-poly2-constrained-2026-09-25-v3`

Phase 5.1 canonical run:

- source `4f96463411da8f9f6aecb370e8ac69ae2c228273`
- run `36219037262`
- artifact `10899193034`
- artifact SHA-256 `7e1e244074520e3e9e620fc29a602b99b094c6592a4bb954407b3e98b4949426`

## Phase 6A frontend freeze

Frontend ID:

`openvq-frontend-phase6a-2026-09-26-v1`

Record:

- source `d129658f084eaac28ed88f801c566ff2addb72f2`
- run `36232604130`
- artifact `openvq-phase6a-foundation`
- artifact ID `10902877054`
- artifact SHA-256 `772ae5666a0edcefbfe835a1d53ea7d5d1d4477c248d6802f6c4f4e262496fb1c`
- freeze file `validation/phase6/frontend-freeze.json`

## Phase 6B summary evidence

Feature schema:

`openvq-rich-v3-2026-09-26-v1`

Record:

- run `36233995161`
- artifact `openvq-phase6b-summary`
- artifact ID `10905043210`
- artifact SHA-256 `8d5fefb87379862acf6385d0514d1ac0088c87762612a3c05601ff978a24d32b`

This artifact is the canonical source for the 2,463-row Phase 6 development manifest and global features.

## Phase 6D trace evidence

Trace schema:

`openvq-trace-v1-2026-09-26`

Record:

- run `36247385269`
- artifact `openvq-phase6d-traces`
- artifact ID `10907723570`
- artifact SHA-256 `b4f709a6160a9de5ceb1afaa8f60e2e87a44c9a120688e97818d5a8e4bd80c40`
- development trace provenance SHA-256 `cbd5c8874026142b065d352335083640000e507ce1ba364614c236e31319c8fc`
- engineering trace provenance SHA-256 `ae6c65002093cb8f0a78b3829a25719467b53352e6009f57094b8e538c4f68b8`

Every recreated waveform was checked against the Phase 6B manifest before trace export.

## Phase 6E/F sequence evidence

The original 15-job run completed 14 folds before the learned-bands P501 job reached the three-hour runner limit.

Original run:

`36247385269`

Recovery split that missing fold into three independent fixed-seed jobs and then reconstructed the same ensemble result.

Recovery run:

`36284538942`

Candidate evidence artifact:

- name `openvq-phase6ef-recovered-candidate`
- ID `10921181778`
- SHA-256 `3912c8581c907d779e37e9728c3144208f4a70e25b7547396c1730c774203068`

Important file hashes:

- selection report `9c4f4a440e9f3c9ef4759b0015a5fc13f77a3dc9d4a25d695bb25eb734c95ae4`
- ONNX `cea7b5e17cf5e7bf183e994cf7c8c24cf509f553d5d4c6ac5329bdb9b93ff7df`
- PyTorch state `0bb206fbd64cc149e72d9aa4d33368d441019dea51a37a0914de5d663283c372`
- final-fit report `0d06cd3eef8811e433a3b1df65578b37bd61d407f0221c3be2c1eba8e723cd86`
- engineering report `cf8c8e9475c7f56511fb00ddc0b6836f89e2e6031326a851fb0c5e35d125d94d`
- parity report `ec7a81ce9206bd242e1448db690bbf8f73732cd60a6c087757d15e25a19523ab`

## Final Phase 6.1 candidate status

Selected architecture:

`hybrid`

Parameters:

263,009

Full-development seed:

`20260926`

Rows:

2,463

ONNX parity:

pass, maximum absolute MOS difference 0.00000906 under tolerance 0.0001.

Engineering promotion gate:

fail.

No immutable release bundle was created after the failure.

## Reserved external validation

URGENT 2026 subjective labels remain untouched.

A failed engineering candidate is not eligible to consume the reserve.

## Reporting rules

Reports preserve:

- sample counts;
- Pearson and Spearman;
- valid absolute or normalized error;
- bias;
- saturation;
- per-corpus and held-corpus results;
- per-seed evidence;
- engineering failures;
- data and artifact hashes.

No failed candidate is silently replaced by a retuned model under the same identifier.
