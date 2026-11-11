# EEGBench

**EEGBench** is an open benchmark and interactive leaderboard for electroencephalogram (EEG) time series classification. It evaluates **90 classification algorithms**—spanning general time series machine learning (`aeon`), classical Riemannian and spatial-filtering EEG pipelines, supervised Braindecode neural architectures, pretrained EEG foundation models (`aeon-neuro`), and standard tabular baselines—across **76 scalp EEG classification problems** (from an archive of 85 prepared datasets).

<p align="center">
  <a href="https://raw.githack.com/TonyBagnall/EEGBench/main/results/eegbench/leaderboard.html"><strong>Algorithm Leaderboard</strong></a>
  &middot;
  <a href="https://raw.githack.com/TonyBagnall/EEGBench/main/results/eegbench/matrix.html"><strong>Overall Score Matrix (76 &times; 90)</strong></a>
  &middot;
  <a href="https://raw.githack.com/TonyBagnall/EEGBench/main/results/eegbench/datasets.html"><strong>Problem Explorer</strong></a>
  &middot;
  <a href="docs/datasets.md">Datasets</a>
  &middot;
  <a href="docs/evaluation.md">Evaluation</a>
  &middot;
  <a href="docs/leaderboard.md">Domain Tables</a>
  &middot;
  <a href="Repositories.md">External Benchmarks</a>
</p>

The original 30 datasets and initial benchmark study are described in [Time Series Machine Learning for Classifying Electroencephalograms](https://data.mlr.press/assets/pdf/v03-8.pdf) (Rushbrooke, Sami, Middlehurst and Bagnall, *Journal of Data-centric Machine Learning Research*, 2026; archived in [`results/eegbench_paper_2026/`](results/eegbench_paper_2026/)). If you use the archive or these results, please cite `CITATION.cff`.

### Part of the Multiverse

EEGBench is part of the [Multiverse](https://github.com/aeon-toolkit/multiverse), the archive for multivariate time series classification described in [The Multiverse of Time Series Machine Learning: an Archive for Multivariate Time Series Classification](https://arxiv.org/abs/2603.20352) (`arXiv:2603.20352`). The published open subset corresponds to `eeg2026` in `aeon`, kept in a dedicated repository because EEG problems have domain-specific montages, protocols, and classifier families.

This repository stands alone (no dependency on the `multiverse` package) while supporting lossless conversion between wide summary matrices (`results/eegbench/<metric>.csv`) and Multiverse per-estimator directories (`<estimator>/<estimator>_<metric>.csv`).

---

## Leaderboard

<!-- LEADERBOARD:START -->
#### Overall Performance Leaderboard (76 Scalp EEG Problems)

| # | Algorithm | Paradigm | Cov. | Mean Rank | Balanced Acc | Accuracy | AUROC | Log Loss &darr; | Wins |
|---:|---|---|---:|---:|---:|---:|---:|---:|---:|
| 1 | `HC2-500-pc` | General TSML | 63/76 | **15.86** | 53.60% | **55.69%** | 0.6885 | **0.926** | 3 |
| 2 | `HC2-noTDE-500-pc` | General TSML | 70/76 | 16.38 | **53.89%** | 55.57% | **0.6928** | 0.930 | 1 |
| 3 | `MRHydra` | General TSML | 69/76 | 22.45 | 51.04% | 52.70% | 0.6047 | 16.489 | 4 |
| 4 | `Arsenal` | General TSML | 74/76 | 22.77 | 51.63% | 53.85% | 0.6682 | 5.522 | 1 |
| 5 | `DrCIF` | General TSML | 69/76 | 23.01 | 50.85% | 53.70% | 0.6635 | 0.961 | 0 |
| 6 | `DrCIF-500` | General TSML | 70/76 | 24.37 | 51.00% | 53.84% | 0.6706 | 0.956 | 2 |
| 7 | `STC-aeon` | General TSML | 72/76 | 24.83 | 51.25% | 53.77% | 0.6612 | 0.961 | 1 |
| 8 | `EEGNeX-NB` | EEG Supervised DL | 75/76 | 28.63 | 47.52% | 47.75% | 0.6210 | 0.995 | 4 |
| 9 | `DE-LR` | EEG Classical | 71/76 | 29.58 | 48.73% | 49.98% | 0.6334 | 1.743 | 1 |
| 10 | `TSLR-MOABB` | EEG Classical | 72/76 | 32.36 | 47.74% | 49.15% | 0.6228 | 1.696 | 0 |
| 11 | `RDST` | General TSML | 66/76 | 33.06 | 48.23% | 50.47% | 0.5813 | 17.274 | 1 |
| 12 | `TSEN-MOABB` | EEG Classical | 75/76 | 33.18 | 47.01% | 48.36% | 0.6171 | 1.669 | 0 |
| 13 | `TSSVM-MOABB` | EEG Classical | 75/76 | 33.38 | 47.12% | 49.72% | 0.6295 | 1.159 | 0 |
| 14 | `TIDNet-NB` | EEG Supervised DL | 75/76 | 33.79 | 47.25% | 47.21% | 0.6175 | 1.084 | 0 |
| 15 | `FBMSNet-NB` | EEG Supervised DL | 75/76 | 34.28 | 46.29% | 45.88% | 0.6033 | 1.614 | 1 |
| &vellip; | *Best remaining paradigm representatives* | | | | | | | | |
| 49 | `CBraMod` | EEG Foundation | 72/76 | 43.28 | 42.70% | 44.67% | 0.5376 | 19.104 | 0 |
| 61 | `SVM` | Tabular | 63/76 | 46.09 | 42.31% | 46.13% | 0.5620 | 1.050 | 0 |

*80 of 90 algorithms meet &ge;80% coverage (61/76 problems), evaluated on their 39 shared completed problems (resample 0, ordered by mean balanced-accuracy rank).*

#### Leaderboard by Problem Type

| Problem Type | Problems (Common) | #1 Overall | #2 Overall | #3 Overall | Best EEG-Specific Algorithm |
|---|---:|---|---|---|---|
| **All Scalp EEG** | 76 (39) | `HC2-500-pc` (53.6%) | `HC2-noTDE-500-pc` (53.9%) | `MRHydra` (51.0%) | `EEGNeX-NB` (#8, 47.5%) |
| **BCI (All)** | 53 (29) | `HC2-500-pc` (53.1%) | `HC2-noTDE-500-pc` (52.6%) | `DrCIF` (50.9%) | `EEGNeX-NB` (#9, 46.0%) |
| **Motor Imagery** | 35 (18) | `HC2-500-pc` (62.3%) | `HC2-noTDE-500-pc` (62.4%) | `Arsenal` (60.6%) | `TIDNet-NB` (#7, 57.0%) |
| **ERP / P300** | 8 (6) | `Deep4Net-NB` (68.3%) | `SPARCNet-NB` (66.0%) | `EEGNeX-NB` (68.6%) | `Deep4Net-NB` (#1, 68.3%) |
| **VEP / SSVEP** | 6 (3) | `STC-aeon` (37.4%) | `DrCIF-500` (30.5%) | `XdawnCov-MDM-MOABB` (53.8%) | `XdawnCov-MDM-MOABB` (#3, 53.8%) |
| **Speech BCI** | 4 (4) | `TDE` (35.8%) | `HC2-500-pc` (36.0%) | `STC-aeon` (30.1%) | `RiemannianKNN-OAS-BP140` (#7, 30.2%) |
| **Clinical** | 15 (8) | `HC2-noTDE-500-pc` (58.7%) | `DE-SVM` (56.4%) | `Arsenal` (57.0%) | `DE-SVM` (#2, 56.4%) |
| **Cognitive** | 8 (6) | `HC2-noTDE-500-pc` (63.7%) | `DrCIF` (62.2%) | `DrCIF-500` (61.2%) | `EEGNeX-NB` (#6, 58.1%) |
<!-- LEADERBOARD:END -->

### Interactive Views

Rebuilt automatically via `python -m eegbench.experiments.tables`, which generates three self-contained interactive HTML dashboards in [`results/eegbench/`](results/eegbench/):

- **[`results/eegbench/leaderboard.html`](results/eegbench/leaderboard.html)** ([live preview](https://raw.githack.com/TonyBagnall/EEGBench/main/results/eegbench/leaderboard.html)) — Interactive algorithm leaderboard across all 76 problems and split across 8 problem-type tabs (`All`, `BCI`, `Motor Imagery`, `ERP`, `VEP`, `Speech`, `Clinical`, `Cognitive`), with paradigm filter pills, coverage-block vs all-available ranking switches, base-architecture deduplication, and critical difference diagrams.
- **[`results/eegbench/matrix.html`](results/eegbench/matrix.html)** ([live preview](https://raw.githack.com/TonyBagnall/EEGBench/main/results/eegbench/matrix.html)) — Interactive **76 Problems &times; 90 Algorithms** score matrix grouped by problem type and algorithm paradigm, with metric switching (`Balanced Accuracy`, `Accuracy`, `AUROC`, `Log Loss`), row-normalised or baseline-gain heatmap shading, and multi-metric hover tooltips.
- **[`results/eegbench/datasets.html`](results/eegbench/datasets.html)** ([live preview](https://raw.githack.com/TonyBagnall/EEGBench/main/results/eegbench/datasets.html)) — Per-problem explorer comparing the constant test-majority `Default` floor, median, ceiling, winning algorithm, and spread across all 76 tasks.
- Full Top-15 Markdown tables per problem type are also written to [`docs/leaderboard.md`](docs/leaderboard.md).

---

## Installation

Install from source:

```bash
git clone https://github.com/TonyBagnall/EEGBench.git
cd EEGBench
pip install -e .
```

## Quick start

### Explore datasets by problem type

The repository registers 85 problems in `eegbench.datasets.eegbench`:
- **`eegbench_76`** (`76` scalp EEG problems): split into **BCI** (`53`: `MI` `35`, `ERP` `8`, `VEP` `6`, `Speech` `4`), **Clinical** (`15`), and **Cognitive** (`8`), excluding MEG (`4`), ECoG (`1`), and four legacy tasks (`Blink`, `ButtonPress`, `EpilepticSeizures`, `Sleep`).
- **`eegbench_paper`** (`30` problems): the Rushbrooke et al. (2026) DMLR benchmark (`28` open on Zenodo as `eegbench_open` / `aeon`'s `eeg2026`, plus `2` restricted fibromyalgia cohorts).

```python
from aeon.datasets import load_classification
from eegbench.datasets import by_type, eegbench_76, metadata

print(len(eegbench_76), len(by_type("MI")), len(by_type("Clinical")))
print(metadata().loc["ImaginedFeetHands"])

X_train, y_train = load_classification("ImaginedFeetHands", split="train")
X_test, y_test = load_classification("ImaginedFeetHands", split="test")
```

For local preparations (55 datasets), load `.ts` files directly via `aeon.datasets.load_from_ts_file`, e.g. `load_from_ts_file("D:/Data/EEG/ImaginedLeftRightHand/ImaginedLeftRightHand_TRAIN.ts")`. Always use the supplied fixed train/test split (`resample 0`); see [`docs/datasets.md`](docs/datasets.md) and [`docs/dataset-provenance.md`](docs/dataset-provenance.md).

### Train and test a classifier

```python
from aeon.classification.convolution_based import MultiRocketHydraClassifier

clf = MultiRocketHydraClassifier(random_state=0)
clf.fit(X_train, y_train)
print(clf.score(X_test, y_test))
```

EEGBench holds benchmark metadata and results only—no classifier implementation code belongs in this repository:
- EEG-specific classifiers (Riemannian pipelines, CSP/xDAWN/CCA/TRCA, Braindecode wrappers, and pretrained EEG foundation models) live in [`aeon-neuro`](https://github.com/aeon-toolkit/aeon-neuro).
- Ports of general multivariate time series classifiers outside `aeon` live in [`multiverse.classification`](https://github.com/aeon-toolkit/multiverse/tree/main/multiverse/classification).
- General time series classifiers (`HC2`, `MRHydra`, `Arsenal`, `DrCIF`, `STC`, `RDST`, `TDE`, `QUANT`, `InceptionTime`, `LITETime`) live in [`aeon`](https://github.com/aeon-toolkit/aeon).

### Query stored benchmark scores

```python
from eegbench.experiments.tables import compute_league_table, load_metric

print(load_metric("HC2-500-pc", "balacc")["ImaginedFeetHands"])
```

### Refresh results and rebuild the dashboard

Results are generated on fixed `testResample0.csv` splits with [`tsml_eval`](https://github.com/time-series-machine-learning/tsml-eval):

```bash
python -m eegbench.experiments.run_benchmark                     # run tsml-eval experiments
python -m eegbench.experiments.ingest --wide-from D:/Results/EEG # export wide summary CSVs
python -m eegbench.experiments.tables                            # rebuild HTML + Markdown tables
```

See [`docs/evaluation.md`](docs/evaluation.md) for metric definitions, baseline rules, and Multiverse export options.

## Repository layout

```text
EEGBench/
├── docs/                        # Dataset provenance, taxonomy, evaluation & domain tables
├── results/
│   ├── eegbench/                # Active 76-problem x 90-algorithm wide CSVs & HTML dashboard
│   ├── eegbench_paper_2026/     # Archived 30-problem DMLR 2026 Multiverse CSVs & pages
│   └── tsml-eval-20261111/      # Dated tsml-eval wide snapshot export
├── eegbench/                    # Python package (metadata & leaderboard tooling only)
│   ├── datasets.py              # Archive registry (85 total, 76 scalp EEG study, taxonomy)
│   ├── estimators.py            # Classifier metadata (90 active across 5 paradigms)
│   └── experiments/             # Benchmark runners, wide/Multiverse ingest, HTML builders
└── tools/                       # Dataset import, validation & cluster collation utilities
```

---

### Ongoing Archive & Competition References

- Dataset conversion handover & live progress: [`DATASET_CONVERSION_HANDOVER.md`](DATASET_CONVERSION_HANDOVER.md) and [`docs/assimilation-progress.json`](docs/assimilation-progress.json).
- Restored motor imagery preparations: [`docs/temp-c-mi-preparations.md`](docs/temp-c-mi-preparations.md).
- Selected 76-problem scalp EEG study scope & exclusions: [`eeg.txt`](eeg.txt) and [`docs/problem-taxonomy.md`](docs/problem-taxonomy.md).
- External dataset & algorithm benchmark surveys: [`Repositories.md`](Repositories.md) and [`docs/benchmark_algorithms_survey.md`](docs/benchmark_algorithms_survey.md).
- Competition pipeline (separate from archive): [`docs/competition-track2.md`](docs/competition-track2.md).
