# OpenVQ

OpenVQ is a source-available full-reference speech-quality research engine for telecom and drive-test applications.

It compares a known reference utterance with a degraded recording and produces an OpenVQ quality estimate together with interpretable speech-quality diagnostics.

OpenVQ is independently derived. It is not POLQA, does not implement ITU-T P.863, and is not currently demonstrated to be equivalent or superior to POLQA.

## Repository status

The default `main` branch is the stable baseline.

Current research is tracked on `validation/phase6`.

The latest research milestone is **Phase 6.1**. That work established a frozen frontend, canonical dataset registry, local sequence traces, compact sequence-model evaluation, and ONNX export. The selected hybrid sequence candidate passed numerical export parity but failed the independent engineering promotion gate.

The failed candidate is not promoted into the main scoring path.

Research branch:

https://github.com/abdullah-x-bd/openvq/tree/validation/phase6

Current evidence summary:

[docs/PHASE6_1_RESULTS.md](docs/PHASE6_1_RESULTS.md)

## Latest scientific result

The Phase 6E frozen architecture-selection rule selected a 263,009-parameter hybrid sequence model.

Completely held-out OpenACE improved to:

- Pearson 0.3990
- Spearman 0.4390

This was a meaningful improvement over earlier OpenACE reversals.

The full-development candidate then failed engineering sanity:

- clean identity MOS 2.393, below the 4.4 gate;
- two dropout severity reversals;
- one repeated-dropout reversal;
- one mixed-impairment reversal;
- two noise severity reversals.

PyTorch-to-ONNX parity passed with maximum absolute difference 0.0000091 MOS.

The result identifies training, calibration, domain robustness, and engineering constraints as the next model-development problem.

## Stable native baseline

Main contains the independently derived native C++ engine, Android integration, calibration utilities, validation workflows, and historical benchmark infrastructure.

Build:

    cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
    cmake --build build --parallel
    ctest --test-dir build --output-on-failure

Analyze two WAV files:

    ./build/openvq_cli reference.wav degraded.wav

The default and historical calibration paths are research interfaces. They are not POLQA replacements.

## ViSQOL

Google ViSQOL is not vendored into this repository.

Where used, it is an independently computed optional external signal or benchmark. OpenVQ's native analyzer is not based on ViSQOL.

## POLQA

POLQA is not an OpenVQ runtime dependency.

A direct comparison requires lawful published or licensed POLQA outputs for exactly the same reference/degraded audio pairs and the same human target.

OpenACE provides public per-file POLQA values for historical benchmarking, but it is already development evidence and is not an untouched Phase 6.1 validation set.

## External reserve

URGENT 2026 subjective labels remain unconsumed by Phase 6.1 model selection.

The reserve is not opened for a candidate that fails the independent engineering gate.

## Claim boundary

OpenVQ can be described as an independently derived full-reference speech-quality research engine with reproducible native diagnostics and documented human-subjective experiments.

OpenVQ is not currently established as:

- POLQA-equivalent;
- a general POLQA replacement;
- P.863 compliant;
- generally superior to POLQA;
- externally validated at Phase 6.1.

## Documentation

- [Documentation index](docs/README.md)
- [Phase 6.1 results](docs/PHASE6_1_RESULTS.md)
- [Stable algorithm baseline](docs/ALGORITHM.md)
- [Validation status](docs/VALIDATION.md)

## Licensing

OpenVQ is source-available under PolyForm Noncommercial 1.0.0. Commercial use requires a separate written commercial license. See LICENSE and COMMERCIAL-LICENSE.md.
