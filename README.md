# Neuroverse

**Neuroverse** is an open benchmark and interactive leaderboard for electroencephalogram (EEG) time series classification. It evaluates **72 distinct classifiers** (across 90 configurations including band-pass and random-weight controls)—spanning general time series machine learning (`aeon`), classical Riemannian and spatial-filtering EEG pipelines, supervised Braindecode neural architectures, pretrained EEG foundation models (`aeon-neuro`), and standard tabular baselines—across **77 scalp EEG classification problems** (from an archive of 86 prepared datasets).

<p align="center">
  <a href="https://raw.githack.com/TonyBagnall/Neuroverse/main/results/neuroverse/leaderboard.html"><strong>Algorithm Leaderboard</strong></a>
  &middot;
  <a href="https://raw.githack.com/TonyBagnall/Neuroverse/main/results/neuroverse/matrix.html"><strong>Overall Score Matrix (77 &times; 72)</strong></a>
  &middot;
  <a href="https://raw.githack.com/TonyBagnall/Neuroverse/main/results/neuroverse/datasets.html"><strong>Problem Explorer</strong></a>
  &middot;
  <a href="docs/datasets.md">Datasets</a>
  &middot;
  <a href="docs/evaluation.md">Evaluation</a>
  &middot;
  <a href="docs/leaderboard.md">Domain Tables</a>
  &middot;
  <a href="Repositories.md">External Benchmarks</a>
</p>

The original 30 datasets and initial benchmark study are described in [Time Series Machine Learning for Classifying Electroencephalograms](https://data.mlr.press/assets/pdf/v03-8.pdf) (Rushbrooke, Sami, Middlehurst and Bagnall, *Journal of Data-centric Machine Learning Research*, 2026; archived in [`results/neuroverse_paper_2026/`](results/neuroverse_paper_2026/)). If you use the archive or these results, please cite `CITATION.cff`.

### Part of the Multiverse

Neuroverse is part of the [Multiverse](https://github.com/aeon-toolkit/multiverse), the archive for multivariate time series classification described in [The Multiverse of Time Series Machine Learning: an Archive for Multivariate Time Series Classification](https://arxiv.org/abs/2603.20352) (`arXiv:2603.20352`). The published open subset corresponds to `eeg2026` in `aeon`, kept in a dedicated repository because EEG problems have domain-specific montages, protocols, and classifier families.

This repository stands alone (no dependency on the `multiverse` package) while supporting lossless conversion between wide summary matrices (`results/neuroverse/<metric>.csv`) and Multiverse per-estimator directories (`<estimator>/<estimator>_<metric>.csv`).

---

## Leaderboard

<!-- LEADERBOARD:START -->
#### Overall Performance Leaderboard (77 Scalp EEG Problems)

| # | Algorithm | Paradigm | Cov. | Mean Rank | Balanced Acc | Accuracy | AUROC | Log Loss &darr; | Wins |
|---:|---|---|---:|---:|---:|---:|---:|---:|---:|
| 1 | `HC2-500-pc` | General TSML | 63/77 | **11.86** | **54.36%** | **56.44%** | **0.6985** | **0.930** | 4 |
| 2 | `Arsenal` | General TSML | 74/77 | 17.21 | 52.50% | 54.70% | 0.6786 | 5.571 | 1 |
| 3 | `MRHydra` | General TSML | 69/77 | 18.18 | 51.49% | 53.09% | 0.6116 | 16.345 | 4 |
| 4 | `DrCIF-500` | General TSML | 70/77 | 19.54 | 51.82% | 54.63% | 0.6820 | 0.958 | 2 |
| 5 | `STC-aeon` | General TSML | 72/77 | 19.76 | 51.93% | 54.43% | 0.6708 | 0.964 | 2 |
| 6 | `EEGNeX-NB` | EEG Supervised DL | 75/77 | 21.24 | 48.75% | 48.95% | 0.6352 | 0.996 | 6 |
| 7 | `DE-LR` | EEG Classical | 71/77 | 24.55 | 48.78% | 50.04% | 0.6383 | 1.748 | 1 |
| 8 | `RDST` | General TSML | 66/77 | 25.70 | 49.28% | 51.51% | 0.5939 | 16.902 | 1 |
| 9 | `TIDNet-NB` | EEG Supervised DL | 75/77 | 26.31 | 48.17% | 48.11% | 0.6281 | 1.084 | 0 |
| 10 | `TSLR-MOABB` | EEG Classical | 72/77 | 26.39 | 48.11% | 49.54% | 0.6302 | 1.670 | 1 |
| 11 | `EEGInceptionMI-NB` | EEG Supervised DL | 75/77 | 26.82 | 49.31% | 49.12% | 0.6206 | 1.146 | 2 |
| 12 | `TSEN-MOABB` | EEG Classical | 75/77 | 27.13 | 47.49% | 48.87% | 0.6251 | 1.643 | 1 |
| 13 | `TSSVM-MOABB` | EEG Classical | 75/77 | 27.36 | 47.34% | 49.93% | 0.6332 | 1.183 | 1 |
| 14 | `SincShallowNet-NB` | EEG Supervised DL | 75/77 | 28.18 | 45.97% | 45.08% | 0.5967 | 1.045 | 0 |
| 15 | `FBMSNet-NB` | EEG Supervised DL | 75/77 | 28.40 | 46.97% | 46.57% | 0.6140 | 1.577 | 1 |
| &vellip; | *Best remaining paradigm representatives* | | | | | | | | |
| 45 | `CBraMod` | EEG Foundation | 72/77 | 35.21 | 43.29% | 45.25% | 0.5450 | 18.903 | 0 |
| 50 | `SVM` | Tabular | 63/77 | 38.02 | 42.41% | 46.11% | 0.5627 | 1.059 | 0 |

*64 of 72 distinct classifiers meet &ge;80% coverage (62/77 problems), evaluated on their 42 shared completed problems (resample 0, ordered by mean balanced-accuracy rank).*

#### Leaderboard by Problem Type

| Problem Type | Problems (Common) | #1 Overall | #2 Overall | #3 Overall | Best EEG-Specific Classifier |
|---|---:|---|---|---|---|
| **All Scalp EEG** | 77 (42) | `HC2-500-pc` (54.4%) | `Arsenal` (52.5%) | `MRHydra` (51.5%) | `EEGNeX-NB` (#6, 48.8%) |
| **BCI (All)** | 54 (31) | `HC2-500-pc` (52.8%) | `Arsenal` (50.4%) | `MRHydra` (49.5%) | `EEGNeX-NB` (#6, 46.2%) |
| **Motor Imagery** | 30 (19) | `HC2-500-pc` (61.3%) | `MRHydra` (58.4%) | `DrCIF-500` (59.9%) | `TIDNet-NB` (#5, 55.2%) |
| **Motor Execution** | 6 (4) | `HC2-500-pc` (71.4%) | `Arsenal` (70.3%) | `EEGNeX-NB` (71.7%) | `EEGNeX-NB` (#3, 71.7%) |
| **ERP / P300** | 8 (6) | `Deep4Net-NB` (68.3%) | `EEGNeX-NB` (68.6%) | `SPARCNet-NB` (66.0%) | `Deep4Net-NB` (#1, 68.3%) |
| **VEP / SSVEP** | 6 (3) | `STC-aeon` (37.4%) | `XdawnCov-MDM-MOABB` (53.8%) | `RDST` (31.0%) | `XdawnCov-MDM-MOABB` (#2, 53.8%) |
| **Speech BCI** | 4 (4) | `TDE` (35.8%) | `HC2-500-pc` (36.0%) | `STC-aeon` (30.1%) | `RiemannianKNN-OAS-BP140` (#5, 30.2%) |
| **Clinical** | 15 (8) | `DE-SVM` (56.4%) | `Arsenal` (57.0%) | `EEGNeX-NB` (55.5%) | `DE-SVM` (#1, 56.4%) |
| **Cognitive** | 8 (6) | `DrCIF-500` (61.2%) | `MRHydra` (60.2%) | `Arsenal` (60.7%) | `EEGNeX-NB` (#4, 58.1%) |
<!-- LEADERBOARD:END -->

### Interactive Views

Rebuilt automatically via `python -m neuroverse.experiments.tables`, which generates three self-contained interactive HTML dashboards in [`results/neuroverse/`](results/neuroverse/):

- **[`results/neuroverse/leaderboard.html`](results/neuroverse/leaderboard.html)** ([live preview](https://raw.githack.com/TonyBagnall/Neuroverse/main/results/neuroverse/leaderboard.html)) — Interactive leaderboard ranking the **72 distinct classifiers** across all 77 problems and split across 9 problem-type tabs (`All`, `BCI`, `Motor Imagery`, `Motor Execution`, `ERP`, `VEP`, `Speech`, `Clinical`, `Cognitive`), with paradigm filter pills, Standard Metrics vs Split-by-Problem-Type column views, an optional toggle to include all 90 configurations (18 band-pass, shrinkage, and random-weight controls), and critical difference diagrams.
- **[`results/neuroverse/matrix.html`](results/neuroverse/matrix.html)** ([live preview](https://raw.githack.com/TonyBagnall/Neuroverse/main/results/neuroverse/matrix.html)) — Interactive **77 Problems &times; 72 Classifiers** (or all 90 configurations) score matrix grouped by problem type and algorithm paradigm, with metric switching (`Balanced Accuracy`, `Accuracy`, `AUROC`, `Log Loss`), row-normalised or baseline-gain heatmap shading, and multi-metric hover tooltips.
- **[`results/neuroverse/datasets.html`](results/neuroverse/datasets.html)** ([live preview](https://raw.githack.com/TonyBagnall/Neuroverse/main/results/neuroverse/datasets.html)) — Per-problem explorer comparing the constant test-majority `Default` floor, median, ceiling, winning algorithm, and spread across all 77 tasks.
- Full Top-15 Markdown tables per problem type are also written to [`docs/leaderboard.md`](docs/leaderboard.md).

---

## Installation

```bash
pip install neuroverse
```

Or install from source:

```bash
git clone https://github.com/TonyBagnall/Neuroverse.git
cd Neuroverse
pip install -e .
```

## Quick start

### Explore datasets by problem type

The repository registers 86 problems in `neuroverse.datasets.neuroverse`:
- **`neuroverse_study`** (`77` scalp EEG problems): split into **BCI** (`54`: `MI` `30`, `ME` `6`, `ERP` `8`, `VEP` `6`, `Speech` `4`), **Clinical** (`15`), and **Cognitive** (`8`), excluding MEG (`4`), ECoG (`1`), and four legacy tasks (`Blink`, `ButtonPress`, `EpilepticSeizures`, `Sleep`).
- **`neuroverse_paper`** (`30` problems): the Rushbrooke et al. (2026) DMLR benchmark (`28` open on Zenodo as `neuroverse_open` / `aeon`'s `eeg2026`, plus `2` restricted fibromyalgia cohorts).

```python
from aeon.datasets import load_classification
from neuroverse.datasets import by_type, metadata, neuroverse_study

print(len(neuroverse_study), len(by_type("MI")), len(by_type("Clinical")))
print(metadata().loc["ImaginedFeetHands"])

X_train, y_train = load_classification("ImaginedFeetHands", split="train")
X_test, y_test = load_classification("ImaginedFeetHands", split="test")
```

For local preparations (56 datasets), load `.ts` files directly via `aeon.datasets.load_from_ts_file`, e.g. `load_from_ts_file("D:/Data/EEG/ImaginedLeftRightHand/ImaginedLeftRightHand_TRAIN.ts")`. Always use the supplied fixed train/test split (`resample 0`); see [`docs/datasets.md`](docs/datasets.md) and [`docs/dataset-provenance.md`](docs/dataset-provenance.md).

### Train and test a classifier

```python
from aeon.classification.convolution_based import MultiRocketHydraClassifier

clf = MultiRocketHydraClassifier(random_state=0)
clf.fit(X_train, y_train)
print(clf.score(X_test, y_test))
```

Neuroverse holds benchmark metadata and results only—no classifier implementation code belongs in this repository:
- EEG-specific classifiers (Riemannian pipelines, CSP/xDAWN/CCA/TRCA, Braindecode wrappers, and pretrained EEG foundation models) live in [`aeon-neuro`](https://github.com/aeon-toolkit/aeon-neuro).
- Ports of general multivariate time series classifiers outside `aeon` live in [`multiverse.classification`](https://github.com/aeon-toolkit/multiverse/tree/main/multiverse/classification).
- General time series classifiers (`HC2`, `MRHydra`, `Arsenal`, `DrCIF`, `STC`, `RDST`, `TDE`, `QUANT`, `InceptionTime`, `LITETime`) live in [`aeon`](https://github.com/aeon-toolkit/aeon).

### Query stored benchmark scores

```python
from neuroverse.experiments.tables import compute_league_table, load_metric

print(load_metric("HC2-500-pc", "balacc")["ImaginedFeetHands"])
```

### Refresh results and rebuild the dashboard

Results are generated on fixed `testResample0.csv` splits with [`tsml_eval`](https://github.com/time-series-machine-learning/tsml-eval):

```bash
python -m neuroverse.experiments.run_benchmark                        # run tsml-eval experiments
python -m neuroverse.experiments.ingest --wide-from D:/Results/EEG    # export wide summary CSVs
python -m neuroverse.experiments.tables                               # rebuild HTML + Markdown tables
```

See [`docs/evaluation.md`](docs/evaluation.md) for metric definitions, baseline rules, and Multiverse export options.

## Repository layout

```text
Neuroverse/
├── docs/                        # Dataset provenance, taxonomy, evaluation & domain tables
├── results/
│   ├── neuroverse/              # Active 76-problem wide CSVs (72 classifiers, 90 configs) & HTML dashboard
│   ├── neuroverse_paper_2026/   # Archived 30-problem DMLR 2026 Multiverse CSVs & pages
│   └── tsml-eval-20261111/      # Dated tsml-eval wide snapshot export
├── neuroverse/                  # Python package (metadata & leaderboard tooling only)
│   ├── datasets.py              # Archive registry (85 total, 76 scalp EEG study, taxonomy)
│   ├── estimators.py            # Classifier metadata (72 distinct across 5 paradigms; 90 configs)
│   └── experiments/             # Benchmark runners, wide/Multiverse ingest, HTML builders
└── tools/                       # Dataset import, validation & cluster collation utilities
```

---

### Ongoing Archive References

- Dataset conversion handover & live progress: [`DATASET_CONVERSION_HANDOVER.md`](DATASET_CONVERSION_HANDOVER.md) and [`docs/assimilation-progress.json`](docs/assimilation-progress.json).
- Restored motor imagery preparations: [`docs/temp-c-mi-preparations.md`](docs/temp-c-mi-preparations.md).
- Selected 76-problem scalp EEG study scope & exclusions: [`eeg.txt`](eeg.txt) and [`docs/problem-taxonomy.md`](docs/problem-taxonomy.md).
- External dataset & algorithm benchmark surveys: [`Repositories.md`](Repositories.md) and [`docs/benchmark_algorithms_survey.md`](docs/benchmark_algorithms_survey.md).
