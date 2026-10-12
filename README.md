# EEGBench

This is a draft, we are adding results as we generate them.

**EEGBench** is a leaderboard for EEG classification. It holds benchmark results for
general purpose time series classifiers, deep learners and methods designed for EEG, on
an archive of 30 EEG classification problems covering medical diagnosis, brain-computer
interfacing and psychology.

The archive and the first set of results are described in
[Time Series Machine Learning for Classifying Electroencephalograms](https://data.mlr.press/assets/pdf/v03-8.pdf)
(Rushbrooke, Sami, Middlehurst and Bagnall, Journal of Data-centric Machine Learning
Research, 2026). If you use the archive or these results, please cite it;
`CITATION.cff` has the full entry.

### Part of the Multiverse

EEGBench is part of the [Multiverse](https://github.com/aeon-toolkit/multiverse), the
archive for multivariate time series classification described in
[The Multiverse of Time Series Machine Learning: an Archive for Multivariate Time Series
Classification](https://arxiv.org/abs/2603.20352) (arXiv:2603.20352). The EEG archive is
a sub-collection of it, `eeg2026` in aeon, kept apart because EEG problems have their own
conventions and their own classifiers.

This repository stands alone: it does not depend on the Multiverse package, and holds
its own results and leaderboard. It uses the same result format and the same leaderboard
tooling, so results can be moved between the two. For multivariate time series
classification beyond EEG, go to the Multiverse.

### Leaderboard

<!-- LEADERBOARD:START -->
| # | Estimator | Accuracy rank | Accuracy | Balanced accuracy | AUROC | F1 | Log loss &darr; | Sensitivity | Specificity |
|---|---|---|---|---|---|---|---|---|---|
| 1 | HC2 | **3.80** | **0.6049** | **0.5803** | **0.6888** | 0.5529 | **0.7550** | 0.5631 | **0.6185** |
| 2 | DrCIF | 5.42 | 0.6004 | 0.5765 | 0.6863 | 0.5476 | 0.7576 | 0.5653 | 0.6065 |
| 3 | Arsenal | 5.53 | 0.5905 | 0.5790 | 0.6414 | **0.5778** | 14.7597 | **0.6079** | 0.5652 |
| 4 | STC | 5.82 | 0.5903 | 0.5729 | 0.6778 | 0.5475 | 0.7803 | 0.5644 | 0.5954 |
| 5 | MRHydra | 6.35 | 0.5889 | 0.5731 | 0.6371 | 0.5613 | 14.8170 | 0.5738 | 0.5869 |
| 6 | SVM | 7.60 | 0.5601 | 0.5309 | 0.6486 | 0.4805 | 0.8417 | 0.5334 | 0.5537 |
| 7 | TDE | 7.75 | 0.5673 | 0.5424 | 0.6414 | 0.5200 | 0.8615 | 0.5369 | 0.5707 |
| 8 | EEGNet | 8.57 | 0.4938 | 0.5023 | 0.6082 | 0.4936 | 0.8735 | 0.5703 | 0.4555 |
| 9 | DCN | 8.72 | 0.5026 | 0.5026 | 0.6135 | 0.4585 | 2.0020 | 0.5396 | 0.4850 |
| 10 | IT | 8.93 | 0.5421 | 0.5422 | 0.6522 | 0.5148 | 2.1187 | 0.5732 | 0.5198 |
| 11 | CNN | 9.85 | 0.5282 | 0.5013 | 0.5915 | 0.3576 | 2.9422 | 0.4133 | 0.6053 |
| 12 | CSP-SVM | 9.98 | 0.5264 | 0.4945 | 0.5992 | 0.4209 | 0.8710 | 0.4718 | 0.5432 |
| 13 | R-KNN | 10.23 | 0.4979 | 0.4871 | 0.5543 | 0.4628 | 18.0963 | 0.4998 | 0.4848 |
| 14 | Default | 10.62 | 0.4833 | 0.4272 | 0.5000 | 0.1857 | 0.8703 | 0.3002 | 0.6002 |
| 15 | R-MDM | 10.83 | 0.4834 | 0.4862 | 0.5687 | 0.4689 | 3.2639 | 0.5208 | 0.4477 |

Average over the 30 datasets with results for every estimator on every metric, ordered by average accuracy rank. Best in each column in bold.
<!-- LEADERBOARD:END -->

Default is the baseline that always predicts the majority class, see
[`docs/evaluation.md`](docs/evaluation.md). Rebuilt with
`python -m eegbench.experiments.tables`, which also writes:

- [`results/eegbench/leaderboard.html`](results/eegbench/leaderboard.html)
  ([preview](https://raw.githack.com/TonyBagnall/EEGBench/main/results/eegbench/leaderboard.html),
  since GitHub shows HTML as source), a sortable version of the table above with a rank
  for every metric
- [`results/eegbench/leaderboard_all.html`](results/eegbench/leaderboard_all.html)
  ([preview](https://raw.githack.com/TonyBagnall/EEGBench/main/results/eegbench/leaderboard_all.html)),
  the same for every estimator with results, including those that have not finished the
  whole archive, scored on the datasets they all completed
- [`results/eegbench/datasets.html`](results/eegbench/datasets.html)
  ([preview](https://raw.githack.com/TonyBagnall/EEGBench/main/results/eegbench/datasets.html)),
  which turns the question around: for each dataset, the baseline, the median and best
  over the estimators, and how much the best gained over the baseline. On many EEG
  problems nothing yet beats the baseline by much, and those come first

<p align="center">
  <a href="docs/datasets.md">Datasets</a>
  ·
  <a href="docs/evaluation.md">Evaluation</a>
  ·
  <a href="docs/leaderboard.md">Leaderboard</a>
</p>

## Installation

The package is not on PyPI yet. Install from source:

```bash
git clone https://github.com/TonyBagnall/EEGBench.git
cd EEGBench
pip install -e .
```

## Quick start

### Load a dataset

28 of the 30 datasets are on Zenodo, in the
[tsml community](https://zenodo.org/communities/tsml/), and are loaded with `aeon`. The
two fibromyalgia datasets are not fully open access; contact Tony Bagnall for access for
research.

```python
from aeon.datasets import load_classification
from eegbench.datasets import eegbench_open, metadata

print(metadata().loc["Blink"])
X_train, y_train = load_classification("Blink", split="train")
X_test, y_test = load_classification("Blink", split="test")
```

Use the train and test split as given. No subject appears on both sides of it, which a
random resample would not respect. More in [`docs/datasets.md`](docs/datasets.md).

### Train and test a classifier

```python
from aeon.classification.convolution_based import MultiRocketHydraClassifier

clf = MultiRocketHydraClassifier(random_state=0)
clf.fit(X_train, y_train)
print(clf.score(X_test, y_test))
```

EEGBench holds results, not classifiers. There is no classifier code in this
repository, and none should be added to it:

- classifiers designed for EEG, such as EEGNet, DeepConvNet and the Riemannian
  classifiers, are in [aeon-neuro](https://github.com/aeon-toolkit/aeon-neuro), and a
  port of a new EEG method belongs there
- ports of general multivariate time series classifiers that are not in aeon, such as
  ConvTran, PatchMTSC, TimesNet, TimesURL and TS2Vec, are in
  [`multiverse.classification`](https://github.com/aeon-toolkit/multiverse/tree/main/multiverse/classification),
  and a port of a new one belongs there
- everything else on the leaderboard is in [aeon](https://github.com/aeon-toolkit/aeon)

### Compare to the results here

```python
from eegbench.experiments.tables import load_metric

print(load_metric("HC2", "accuracy")["Blink"])
```

### Add results

Results are generated with [`tsml_eval`](https://github.com/time-series-machine-learning/tsml-eval),
which writes one file per classifier and dataset holding the predictions and probability
estimates. Three steps take those to the leaderboard, each a script with its settings at
the top of `main`:

```bash
python -m eegbench.experiments.run_benchmark   # write the prediction files
python -m eegbench.experiments.ingest          # compute the metric tables in results/
python -m eegbench.experiments.tables          # rebuild the leaderboards
```

To contribute results, open a pull request with the files `ingest` writes for your
estimator, and say where the prediction files and the code can be found. If the
estimator is a port, contribute the port to aeon-neuro or the Multiverse, as above, and
the results here. More in
[`docs/evaluation.md`](docs/evaluation.md).

## Repository layout

```text
EEGBench/
├── docs/                    # Documentation
├── results/eegbench/        # Results, one directory per estimator, and the leaderboards
└── eegbench/                # Python package
    ├── datasets.py          # The archive: dataset lists and metadata
    ├── estimators.py        # The estimators on the leaderboard, as metadata only
    └── experiments/         # Result generation and leaderboard tables
```
