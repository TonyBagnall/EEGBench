# Evaluation

## Protocol

The protocol is the one in the paper.

- Fit on the default train split, evaluate once on the default test split. This is
  resample `0` in tsml-eval's terms. See [`datasets.md`](datasets.md) for why there are
  no other resamples.
- Estimators are run with their default settings, with no tuning.
- One result per estimator and dataset.

## Metrics

Seven metrics are computed from the stored predictions and probability estimates by
[`tsml_eval`](https://github.com/time-series-machine-learning/tsml-eval), so the same
definitions apply to every estimator.

| File suffix | Metric | Notes |
|---|---|---|
| `accuracy` | Accuracy | |
| `balacc` | Balanced accuracy | Mean recall over classes |
| `auroc` | AUROC | One-vs-rest, weighted by class, for more than two classes |
| `f1` | F1 | Of the minority class for two classes, weighted otherwise |
| `logloss` | Log loss | Lower is better |
| `sensitivity` | Sensitivity | Recall of the minority class for two classes |
| `specificity` | Specificity | Recall of the majority class for two classes |

Estimators that only produce 0/1 probabilities, such as MRHydra and Arsenal, have a very
large log loss. That is a property of their probability estimates and not an error.

Fit and predict times are stored too, as `fittime` and `predicttime` in milliseconds,
but are not on the leaderboard. The deep learners ran on GPU and the rest on a single CPU
thread, on shared clusters, so the times do not compare across estimators.

## The Default baseline

`Default` always predicts the majority class. It is the Default column of Table 7 in the
paper, and is on the leaderboard as a floor: an estimator ranked near it has found
little.

It predicts the most common class in the **test** set, with the test class frequencies
as its probabilities. That makes it the best score any constant prediction can get, so
it is a harder floor than a classifier that predicts the majority class of the train
set, and it is not a classifier that could be fitted. It is built from the true labels
in another estimator's prediction files by `ingest_default`.

## The estimators

<!-- ESTIMATORS:START -->
| Estimator | Family | Library | Description |
|---|---|---|---|
| HC2 | TSML | aeon | HIVE-COTE v2.0 |
| MRHydra | TSML | aeon | MultiROCKET-Hydra |
| Arsenal | TSML | aeon | Ensemble of ROCKET classifiers, an HC2 component |
| DrCIF | TSML | aeon | Diverse Representation CIF, an HC2 component |
| STC | TSML | aeon | Shapelet Transform Classifier, an HC2 component |
| TDE | TSML | aeon | Temporal Dictionary Ensemble, an HC2 component |
| ROCKET | TSML | aeon | Random convolutional kernel transform |
| MiniROCKET | TSML | aeon | MiniROCKET |
| QUANT | TSML | aeon | Quantile interval features |
| FreshPRINCE | TSML | aeon | TSFresh features with a rotation forest |
| CNN | Deep | aeon | Time-CNN |
| IT | Deep | aeon | InceptionTime |
| EEGNet | EEG | Braindecode | EEGNet |
| DCN | EEG | Braindecode | DeepConvNet |
| CSP-SVM | EEG | MNE + scikit-learn | Common Spatial Patterns then an SVM |
| R-MDM | EEG | pyriemann | Riemannian minimum distance to mean |
| R-KNN | EEG | pyriemann | Riemannian nearest neighbour |
| SVM | Standard | scikit-learn | Support vector machine |
| RandomForest | Standard | scikit-learn | Random forest |
| LogisticRegression | Standard | scikit-learn | Logistic regression |
<!-- ESTIMATORS:END -->

The eight compared in the paper are R-MDM, CSP-SVM, CNN, IT, EEGNet, DCN, HC2 and
MRHydra.

## Where the classifiers live

This repository has no classifier code. A classifier is run from the package that
maintains it, and a port of a new method goes to one of these, not here:

| Kind of classifier | Home |
|---|---|
| Designed for EEG, including wrappers of Braindecode and pyriemann | [aeon-neuro](https://github.com/aeon-toolkit/aeon-neuro), `aeon_neuro.classification` |
| Port of a general multivariate time series classifier not in aeon | [Multiverse](https://github.com/aeon-toolkit/multiverse), `multiverse.classification` |
| General time series classifier | [aeon](https://github.com/aeon-toolkit/aeon), `aeon.classification` |

```python
from aeon_neuro.classification import EEGNetClassifier, RiemannianMDMClassifier
from multiverse.classification import ConvTranClassifier, TimesNetClassifier
```

Neither package is a dependency of EEGBench. Install the one that has the classifier
you want to run.

## Result files

Results are stored one directory per estimator, one file per metric:

```text
results/eegbench/<estimator>/<estimator>_<metric>.csv
```

Each file has a row per dataset and a column per resample, with the index labelled
`Resamples:`. A dataset an estimator has no result for is left out, not given a
placeholder score. This is the format the
[Multiverse](https://github.com/aeon-toolkit/multiverse) uses, which EEGBench is part
of, so a result directory can be copied between the two repositories unchanged.

## Generating results

Install the experiment tooling:

```bash
pip install -e ".[experiments]"
```

[`run_single_dataset.py`](../eegbench/experiments/run_single_dataset.py) runs one
estimator on one dataset and
[`run_benchmark.py`](../eegbench/experiments/run_benchmark.py) loops it over the
archive. Both write tsml-eval prediction files:

```text
<results_path>/<estimator>/Predictions/<dataset>/testResample0.csv
```

An existing file is kept, so an interrupted run can be restarted. Running the whole
archive on one machine is not practical for the slower estimators: HC2 averaged 78 hours
a dataset in the paper.

[`ingest.py`](../eegbench/experiments/ingest.py) then turns prediction files into the
metric files above:

```python
from eegbench.experiments.ingest import ingest

ingest(classifier="MRHydra", predictions_path="./results-raw")
```

and `python -m eegbench.experiments.tables` rebuilds the leaderboards.

## Where the current results come from

Every result in `results/eegbench` was ingested from the prediction files of the runs
behind the paper. For the paper's eight classifiers the average accuracies and average
ranks they give match its Figure 1 and Table 3.

Two differences from the paper's tables are known and not yet explained:

- R-MDM differs from Table 7 on four datasets: EpilepticSeizures (0.9461 here, 86.65%
  in the paper), FibroLiverpool (0.4286, 47.62%), MindReading (0.3599, 41.04%) and
  Sleep (0.3029, 33.68%).
- Average log loss is a little lower here than in Table 3 for most estimators, for
  example 0.755 against 0.77 for HC2 and 14.82 against 15.46 for MRHydra.

Six estimators have not finished the archive: ROCKET, MiniROCKET, QUANT, RandomForest
and LogisticRegression have 27 datasets, and FreshPRINCE has 24. They are left out of the
main leaderboard so that it covers all 30 datasets, and are on the all-estimators page.
The reasons the missing runs failed have not been recorded.
