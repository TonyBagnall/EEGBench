# EEG dataset repository reviews

Start here for the external repositories surveyed for additions to EEGBench.
The detailed reviews are all in this repository's root directory.

| Repository | Our review | What it covers |
|---|---|---|
| [MOABB](https://github.com/NeuroTechX/moabb) | [MOABB.md](MOABB.md) | BCI dataset catalogue, candidate selection, original source/licence checks and local preparations. |
| [Braindecode OpenEEGBench](https://github.com/braindecode/OpenEEGBench) | [OpenEEGBench.md](OpenEEGBench.md) | Available classification tasks, Hugging Face preparations, recording overlap, restrictions and remaining candidates. |
| [AdaBrain-Bench](https://github.com/Jamine-W/AdaBrain-Bench) | [AdaBrain-Bench.md](AdaBrain-Bench.md) | Mapping its datasets and tasks to our archive and identifying additional sources. |
| [ETH-DISCO EEG-Bench](https://github.com/ETH-DISCO/EEG-Bench) | [EEG-Bench.md](EEG-Bench.md) | Dataset/task inventory, original recording sources and overlap with our collection. |
| [EEGDash](https://github.com/eegdash/EEGDash) | [EEGDash.md](EEGDash.md) | Catalogue and mirror access, converted corpus, source matching and the existing [clinical candidate survey](docs/clinical-candidates.md). |
| [EEG-Arena / EEG.FM](https://eeg.fm/benchmarks/overall-performance/) | [EEG-Arena.md](EEG-Arena.md) | Foundation-model and supervised-baseline benchmark; initial review of protocols, dataset access and pretraining-overlap handling. |

For a comprehensive cross-benchmark comparison of **classification algorithms and pipelines** across MOABB, Braindecode, OpenEEGBench, EEG-Arena, NeuralBench, AdaBrain-Bench, ETH EEG-Bench, OmniEEG-Bench, EEGDash, and `aeon-neuro`, see [docs/benchmark_algorithms_survey.md](docs/benchmark_algorithms_survey.md).

These reviews include historical snapshots. For current completion counts and
active work, use [assimilation progress](docs/assimilation-progress.json).

For the prepared collection, see [dataset descriptions](docs/datasets.md),
[dataset provenance](docs/dataset-provenance.md) and the alphabetical selected
problem list [eeg.txt](eeg.txt). To continue downloading/converting, read the
[agent handover](DATASET_CONVERSION_HANDOVER.md) and
[motor imagery roadmap](docs/motor-imagery-road-to-30.md).

Different repository names, labels or preprocessing can refer to the same source
recordings. Compare original accessions, revisions, files and case metadata
before treating a source view as an independent dataset.
